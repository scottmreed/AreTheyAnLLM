import os
import openai
from dotenv import load_dotenv
import re
import pickle
import hashlib
import time  # Added for time tracking
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4.1-nano"  # This was the model in the original script, ensure it's what you intend to use.


def split_sentences(text):
    # More robust sentence split
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]


def split_words(text):
    return text.strip().split()


CACHE_FILE = "nano_next_word_cache.pkl"
try:
    with open(CACHE_FILE, "rb") as f:
        nano_cache = pickle.load(f)
except FileNotFoundError:
    print(f"Cache file {CACHE_FILE} not found. Starting with an empty cache.")
    nano_cache = {}
except Exception as e:
    print(f"Error loading cache file {CACHE_FILE}: {e}. Starting with an empty cache.")
    nano_cache = {}


def hash_prompt(prompt):
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()


def save_cache():
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(nano_cache, f)
    except Exception as e:
        print(f"Error saving cache file {CACHE_FILE}: {e}")


def nano_next_word(prompt):
    h = hash_prompt(prompt)
    if h in nano_cache:
        # Ensure usage is always a dict, even if not present in older cache entries
        return nano_cache[h]['word'], nano_cache[h].get('usage', {})

    # Ensure API key is set before making a call
    if not openai.api_key:
        print("OpenAI API key is not set. Cannot make API call.")
        return '', {'error': 'API key not set'}

    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2,  # Increased slightly to catch two-word proper nouns if needed, but will take first.
            temperature=0.0,
            stop=None,  # Explicitly None, though it's the default.
        )
        text = response.choices[0].message.content.strip()
        next_word = split_words(text)[0] if text else ''
        usage = response.usage.to_dict() if hasattr(response, 'usage') and response.usage else {}
        nano_cache[h] = {'word': next_word, 'usage': usage}
        save_cache()
        return next_word, usage
    except openai.APIError as e:
        print(f"OpenAI API Error in nano_next_word for prompt '{prompt[:50]}...': {e}")
        return '', {'error': str(e)}  # Return error info in usage dict
    except Exception as e:
        print(f"Unexpected error in nano_next_word for prompt '{prompt[:50]}...': {e}")
        return '', {'error': str(e)}


def llm_or_human(input_text, max_sentences=4):
    MAX_EXECUTION_TIME_SECONDS = 120  # 1 minute
    start_time = time.time()
    time_limit_reached_flag = False

    sentences = split_sentences(input_text)
    if not sentences:
        print("Input text contains no sentences.")
        return 0.0, 0  # Return 0% score and 0 tokens if no sentences

    sentences_to_process = sentences[:max_sentences]

    total_predictions = 0
    correct_predictions = 0
    total_tokens_used_api = 0  # Tokens from actual API calls (non-cached)

    context = ""
    try:
        for si, sentence in enumerate(sentences_to_process):
            current_time = time.time()
            if current_time - start_time > MAX_EXECUTION_TIME_SECONDS:
                print(
                    f"\nTime limit of {MAX_EXECUTION_TIME_SECONDS} seconds reached during sentence processing. Stopping.")
                time_limit_reached_flag = True
                break

            words = split_words(sentence)
            if len(words) < 2:  # Need at least one word to predict the next
                context += sentence + " "
                continue

            for wi in range(len(words) - 1):  # Iterate up to the second to last word to predict the next
                current_time = time.time()
                if current_time - start_time > MAX_EXECUTION_TIME_SECONDS:
                    print(
                        f"\nTime limit of {MAX_EXECUTION_TIME_SECONDS} seconds reached during word processing. Stopping.")
                    time_limit_reached_flag = True
                    break  # Breaks inner (word) loop

                current_prompt_words = words[:wi + 1]
                prompt_text = (context + " ".join(current_prompt_words)).strip()

                if not prompt_text:
                    continue

                instruction = "What is the next word in this text? Respond with ONLY the next word and nothing else."
                full_prompt = f"{prompt_text}\n{instruction}"

                true_next_word = words[wi + 1]

                predicted_next_word, usage_info = nano_next_word(full_prompt)

                # Print streaming evaluation
                print(f"\nEvaluating: [...{prompt_text[-80:]}]")
                print(f"  True next word:      '{true_next_word}'")
                print(f"  Predicted next word: '{predicted_next_word}'")

                is_match = (predicted_next_word.lower().strip() == true_next_word.lower().strip())
                print(f"  Match: {is_match}")
                if usage_info and not usage_info.get('error'):
                    print(f"  Usage (API call): {usage_info}")
                    if 'total_tokens' in usage_info:
                        total_tokens_used_api += usage_info['total_tokens']
                elif usage_info.get('error'):
                    print(f"  API call failed or skipped for this word: {usage_info.get('error')}")
                else:  # Cached
                    print(f"  Usage (cached): Previous usage info might be in cache if available.")

                total_predictions += 1
                if is_match:
                    correct_predictions += 1

            if time_limit_reached_flag:  # If inner loop broke due to time, break outer (sentence) loop too
                break

            context += sentence + " "  # Add the full sentence to context for the next iteration

    except KeyboardInterrupt:
        print("\nProcess interrupted by user (KeyboardInterrupt). Reporting current progress.")

    finally:
        # This block executes regardless of how the try block was exited (normally, via break, or exception)
        score_percentage = 0.0
        if total_predictions > 0:
            score_percentage = (correct_predictions / total_predictions) * 100
            print(f"\nFinal Match Rate: {correct_predictions}/{total_predictions} ({score_percentage:.2f}%)")
        elif time_limit_reached_flag:
            print(
                f"\nTime limit reached. Final Match Rate: {correct_predictions}/{total_predictions} ({score_percentage:.2f}%)")
        else:
            print(
                "\nNo valid predictions were made (e.g., text too short, or process interrupted before any predictions).")

        print(f"Total tokens used from new API calls (non-cached): {total_tokens_used_api}")
        elapsed_time = time.time() - start_time
        print(f"Processing duration: {elapsed_time:.2f} seconds.")

        return score_percentage, total_tokens_used_api


if __name__ == "__main__":
    # Use a sample text from the user request
    sample_text = (
        "IF you remember every word in this book, your memory will have "
        "recorded about two million pieces of information: the order in your "
        "brain will have increased by about two million units. However, while "
        "you have been reading the book, you will have converted at least a "
        "thousand calories of ordered energy, in the form of food, into "
        "disordered energy, in the form of heat that you lose to the air around "
        "you by convection and sweat. This will increase the disorder of the "
        "universe by about twenty million million million million units - or "
        "about ten million million million times the increase in order in your "
        "brain - and that's if you remember everything in this book." )

    try:
        if not openai.api_key:
            print("OPENAI_API_KEY is not set in the environment. Please set it to run the example.")
        else:
            print(
                f"Starting evaluation for text (max duration {60}s):\n'''{sample_text.strip()}'''\nMax sentences: {4}")
            final_score_pct, api_tokens = llm_or_human(sample_text, max_sentences=4)
            print("\n--- Evaluation Summary ---")
            print(f"Returned Final Score: {final_score_pct:.2f}%")
            print(f"Returned API Tokens Used (non-cached): {api_tokens}")

            # Plot the result against reference benchmarks
            def plot_with_icons(score):
                benchmarks = {
                    "KITT": 6.25,
                    "Al Gore": 17.71,
                    "Elizabeth Holmes": 27.42,
                    "James Joyce": 2.45,
                    "Input Text": score,
                }

                icon_urls = {
                    "KITT": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f697.png",
                    "Al Gore": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3a4.png",
                    "Elizabeth Holmes": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9ea.png",
                    "James Joyce": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4da.png",
                    "Input Text": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f9e0.png",
                }

                names = list(benchmarks.keys())
                values = list(benchmarks.values())
                colors = ["#FF9999", "#FFE699", "#99FFCC", "#99CCFF", "#CC99FF"]

                fig, ax = plt.subplots(figsize=(8, 6))
                bars = ax.bar(names, values, color=colors)
                ax.set_ylim(0, max(values) * 1.3)
                ax.set_ylabel("LLM Probability (%)")
                ax.set_title("KITT Scale Comparison")

                for bar, name in zip(bars, names):
                    url = icon_urls.get(name)
                    try:
                        resp = requests.get(url, timeout=5)
                        icon_img = Image.open(BytesIO(resp.content))
                        im = OffsetImage(icon_img, zoom=0.3)
                        ab = AnnotationBbox(im, (bar.get_x() + bar.get_width() / 2, bar.get_height()), frameon=False, box_alignment=(0.5, -0.1))
                        ax.add_artist(ab)
                    except Exception as e:
                        print(f"Failed to load icon for {name}: {e}")

                plt.tight_layout()
                plt.savefig("kitt_scale_plot.png")
                plt.show()
                plt.close()

            plot_with_icons(final_score_pct)
    except KeyboardInterrupt:
        print("\nMain script execution interrupted by user.")
    finally:
        print("Exiting isitllm.py script.")
