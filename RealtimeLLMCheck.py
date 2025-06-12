import os
import json
import base64
import time
import logging
import threading
import sys
from threading import Timer
from dotenv import load_dotenv
import websocket
import sounddevice as sd
from isitllm import llm_or_human  # This now returns (score_percentage, api_tokens)

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY") or sys.exit("ERROR: set OPENAI_API_KEY in .env")
WS_URL = "wss://api.openai.com/v1/realtime?intent=transcription"
HEADERS = [
    f"Authorization: Bearer {API_KEY}",
    "OpenAI-Beta: realtime=v1"
]
MIN_RUN_SECONDS = 60.0  # total run before auto-shutdown
SEGMENT_SECONDS = 3.0  # record length per chunk
FLUSH_INTERVAL = 5.0  # flush buffer for scoring
TRANSCRIPT_FILE = "transcript.txt"

_buffer, total_score, n_scores = [], 0.0, 0
_api_tokens_total = 0  # Optional: to accumulate total API tokens from isitllm
_is_running = False
_shutdown_timer = None
_ws = None
transcript_fh = open(TRANSCRIPT_FILE, "a", buffering=1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)


def flush_and_score():
    global _buffer, total_score, n_scores, _api_tokens_total, _shutdown_timer
    if not _is_running: return
    text = " ".join(_buffer).strip()
    _buffer.clear()
    if text:
        try:
            # llm_or_human now returns (score_percentage, api_tokens)
            score_percentage, api_tokens_segment = llm_or_human(text)

            total_score += score_percentage
            n_scores += 1
            _api_tokens_total += api_tokens_segment  # Accumulate API tokens

            # avg_percentage is now an average of scores that are already 0-100
            avg_percentage = total_score / n_scores if n_scores > 0 else 0.0

            logging.info(
                f"🔍 [SEGMENT SCORE] {score_percentage:.1f}% | Running Avg {avg_percentage:.1f}% (API Tokens: {api_tokens_segment})")
        except Exception as e:
            logging.error(f"Scoring error: {e}")
    # schedule next flush
    if _is_running:  # Only schedule next if still running
        Timer(FLUSH_INTERVAL, flush_and_score).start()


def record_loop():
    """Continuously record fixed-length chunks, send append+commit."""
    global _is_running
    samplerate = 16000
    channels = 1
    while _is_running and _ws and _ws.sock and _ws.sock.connected:  # Added _ws check
        logging.info(f"🎙 Recording {SEGMENT_SECONDS}s of audio…")
        recording = sd.rec(int(SEGMENT_SECONDS * samplerate), samplerate=samplerate, channels=channels, dtype="int16")
        sd.wait()
        pcm = recording.tobytes()
        b64 = base64.b64encode(pcm).decode("ascii")

        # append
        append_msg = {"type": "input_audio_buffer.append", "audio": b64}
        if _is_running and _ws and _ws.sock and _ws.sock.connected:  # Check before send
            _ws.send(json.dumps(append_msg))
            logging.info("→ SENT append chunk")
        else:
            break  # Exit loop if not running or ws disconnected

        # commit
        commit_msg = {"type": "input_audio_buffer.commit"}
        if _is_running and _ws and _ws.sock and _ws.sock.connected:  # Check before send
            _ws.send(json.dumps(commit_msg))
            logging.info("→ SENT commit")
        else:
            break  # Exit loop if not running or ws disconnected

    logging.info("🎙 Record loop exiting")


def initiate_shutdown():
    logging.info(f"⏹ Auto-shutdown after {MIN_RUN_SECONDS}s")
    stop_all()


def stop_all():
    """Clean up everything."""
    global _is_running, _shutdown_timer, total_score, n_scores, _api_tokens_total, _ws
    if not _is_running: return  # Already stopping or stopped

    logging.info("Initiating shutdown sequence...")
    _is_running = False  # Signal other loops/timers to stop

    if _shutdown_timer:
        _shutdown_timer.cancel()
        _shutdown_timer = None

    # Close WebSocket connection if it exists and is open
    if _ws and _ws.sock and _ws.sock.connected:
        logging.info("Closing WebSocket connection...")
        try:
            _ws.close()  # This should trigger on_close eventually
        except Exception as e:
            logging.error(f"Error during WebSocket close: {e}")
    _ws = None  # Clear WebSocket reference

    # Log final score summary
    if n_scores > 0:
        final_avg_score = total_score / n_scores
        logging.info(
            f"🏁 [FINAL SUMMARY] Average LLM-likeness: {final_avg_score:.1f}% across {n_scores} scored segments.")
        logging.info(f"🏁 [FINAL SUMMARY] Total API tokens used for scoring (non-cached): {_api_tokens_total}")
    else:
        logging.info("🏁 [FINAL SUMMARY] No segments were scored.")

    if transcript_fh and not transcript_fh.closed:
        try:
            logging.info(f"Flushing transcript data to '{TRANSCRIPT_FILE}'...")
            transcript_fh.flush()  # Explicitly flush Python's internal buffer
            # Ensure data is written to disk by the OS
            # This is a more forceful flush to the physical storage
            if hasattr(transcript_fh, 'fileno'): # Check if it's a real file descriptor
                os.fsync(transcript_fh.fileno())
            transcript_fh.close()
            logging.info(f"Transcript file '{TRANSCRIPT_FILE}' flushed and closed.")
        except Exception as e:
            logging.error(f"Error flushing/closing transcript file: {e}")

    logging.info("Clean shutdown complete.")


def on_open(ws_app):
    global _ws, _is_running
    _ws = ws_app
    _is_running = True
    logging.info("WS open; awaiting transcription_session.created…")


def on_message(ws_app, raw):
    global _shutdown_timer, _is_running  # Added _is_running
    if not _is_running: return  # Don't process messages if shutting down

    data = json.loads(raw)
    t = data.get("type", "")
    ts = time.strftime("%H:%M:%S")

    if t == "transcription_session.created":
        logging.info("🆕 session.created → sending update")
        ws_app.send(json.dumps({
            "type": "transcription_session.update",
            "session": {
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "gpt-4o-mini-transcribe",
                    "language": "en"
                }
            }
        }))
        return

    if t == "transcription_session.updated":
        logging.info("✅ session.updated → starting record loop & flush")
        # start periodic flush
        if _is_running:  # Check before starting new timers/threads
            flush_and_score()
            # start recording loop
            threading.Thread(target=record_loop, daemon=True).start()
            # schedule auto shutdown
            if _shutdown_timer: _shutdown_timer.cancel()  # Cancel any existing
            _shutdown_timer = Timer(MIN_RUN_SECONDS, initiate_shutdown)
            _shutdown_timer.start()
        return

    if t == "input_audio_buffer.committed":
        logging.info("✔ buffer committed")
        return

    if t == "conversation.item.input_audio_transcription.delta":
        delta = data.get("delta", "").strip()
        if delta:
            logging.info(f"[{ts}] Δ {delta}")
            if transcript_fh and not transcript_fh.closed:
                transcript_fh.write(f"[{ts}] Δ {delta}\n")
            _buffer.append(delta)
        return

    if t == "conversation.item.input_audio_transcription.completed":
        full = data.get("transcript", "").strip()
        if full:
            logging.info(f"[{ts}] ✔ {full}")
            if transcript_fh and not transcript_fh.closed:
                transcript_fh.write(f"[{ts}] ✔ {full}\n")
            _buffer.append(full)  # Append full transcript as well for scoring context
        return


def on_error(ws_app, err):
    logging.error(f"WS error: {err}")
    stop_all()  # Ensure cleanup on error


def on_close(ws_app, code, reason):
    logging.info(f"WS closed: {code} / {reason if reason else 'No reason provided'}")
    stop_all()  # Ensure cleanup on close


def wait_for_enter():
    input("Press ENTER to stop early…\n")
    if _is_running:  # Only log and stop if it was actually running
        logging.info("ENTER key pressed → initiating early shutdown")
        initiate_shutdown()  # Use initiate_shutdown to be consistent with timer


if __name__ == "__main__":
    threading.Thread(target=wait_for_enter, daemon=True).start()
    ws_app_instance = websocket.WebSocketApp(  # Renamed for clarity
        WS_URL,
        header=HEADERS,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    _ws = ws_app_instance  # Assign to global _ws so stop_all can access it if run_forever exits early

    logging.info("Connecting to OpenAI Realtime…")
    try:
        ws_app_instance.run_forever()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received.")
        # stop_all() will be called by on_close if ws.close() is effective,
        # or by the finally block.
    except Exception as e:
        logging.error(f"Unhandled exception from ws.run_forever(): {e}", exc_info=True)
    finally:
        logging.info("Exiting main execution block.")
        stop_all()  # Ensure stop_all is called on any exit path from run_forever