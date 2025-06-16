import os
import openai
from dotenv import load_dotenv
import re
import pickle
import hashlib
import time
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4.1-nano"


def split_sentences(text):
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
        return nano_cache[h]['word'], nano_cache[h].get('usage', {})

    if not openai.api_key:
        print("OpenAI API key is not set. Cannot make API call.")
        return '', {'error': 'API key not set'}

    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2,
            temperature=0.0,
            stop=None,
        )
        text = response.choices[0].message.content.strip()
        next_word = split_words(text)[0] if text else ''
        usage = response.usage.to_dict() if hasattr(response, 'usage') and response.usage else {}
        nano_cache[h] = {'word': next_word, 'usage': usage}
        save_cache()
        return next_word, usage
    except openai.APIError as e:
        print(f"OpenAI API Error in nano_next_word for prompt '{prompt[:50]}...': {e}")
        return '', {'error': str(e)}
    except Exception as e:
        print(f"Unexpected error in nano_next_word for prompt '{prompt[:50]}...': {e}")
        return '', {'error': str(e)}


def llm_or_human(input_text, max_sentences=4):
    MAX_EXECUTION_TIME_SECONDS = 120
    start_time = time.time()
    time_limit_reached_flag = False

    sentences = split_sentences(input_text)
    if not sentences:
        print("Input text contains no sentences.")
        return 0.0, 0

    sentences_to_process = sentences[:max_sentences]
    total_predictions = 0
    correct_predictions = 0
    total_tokens_used_api = 0
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
            if len(words) < 2:
                context += sentence + " "
                continue

            for wi in range(len(words) - 1):
                current_time = time.time()
                if current_time - start_time > MAX_EXECUTION_TIME_SECONDS:
                    print(
                        f"\nTime limit of {MAX_EXECUTION_TIME_SECONDS} seconds reached during word processing. Stopping.")
                    time_limit_reached_flag = True
                    break

                current_prompt_words = words[:wi + 1]
                prompt_text = (context + " ".join(current_prompt_words)).strip()
                if not prompt_text:
                    continue

                instruction = "What is the next word in this text? Respond with ONLY the next word and nothing else."
                full_prompt = f"{prompt_text}\n{instruction}"
                true_next_word = words[wi + 1]
                predicted_next_word, usage_info = nano_next_word(full_prompt)

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
                else:
                    print(f"  Usage (cached): Previous usage info might be in cache if available.")

                total_predictions += 1
                if is_match:
                    correct_predictions += 1

            if time_limit_reached_flag:
                break
            context += sentence + " "
    except KeyboardInterrupt:
        print("\nProcess interrupted by user (KeyboardInterrupt). Reporting current progress.")
    finally:
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


# --- Plotting Function ---
def plot_with_icons(score, author_name_on_plot):
    # Base benchmarks and their icons
    base_benchmarks_data = {
        "James Joyce": {"score": 2.45, "icon": "james_joyce_icon.png"},
        "KITT": {"score": 6.25, "icon": "kitt_icon.png"},
        "Al Gore": {"score": 17.71, "icon": "al_gore_icon.png"},
        "Elizabeth Holmes": {"score": 27.42, "icon": "elizabeth_holmes_icon.png"},
    }

    # Prepare lists for plotting
    names_to_plot = list(base_benchmarks_data.keys()) + [author_name_on_plot]
    scores_to_plot = [data["score"] for data in base_benchmarks_data.values()] + [score]

    icon_file_names = [data["icon"] for data in base_benchmarks_data.values()] + ["brain.png"]  # Default icon for input

    icon_paths_to_plot = [os.path.join("images", "icons", fname) for fname in icon_file_names]

    # Define colors (ensure enough colors for all bars)
    colors = ["#FF9999", "#FFE699", "#99FFCC", "#99CCFF", "#CC99FF", "#E3B7D4"]
    if len(names_to_plot) > len(colors):  # Fallback if more bars than defined colors
        colors.extend(["#D3D3D3"] * (len(names_to_plot) - len(colors)))
    plot_colors = colors[:len(names_to_plot)]

    fig, ax = plt.subplots(figsize=(12, 8))  # Slightly larger figure size
    bars = ax.bar(names_to_plot, scores_to_plot, color=plot_colors)
    ax.set_ylim(0, max(scores_to_plot) * 1.3 if scores_to_plot else 10)

    # Increased font sizes
    ax.set_ylabel("LLM Probability (%)", fontsize=14)
    ax.set_title("KITT Scale Comparison", fontsize=18)
    plt.xticks(rotation=20, ha="right", fontsize=12)  # Adjusted rotation and font size
    plt.yticks(fontsize=12)

    for bar, name, icon_path_str in zip(bars, names_to_plot, icon_paths_to_plot):
        if os.path.exists(icon_path_str):
            try:
                icon_img = Image.open(icon_path_str)
                zoom_level = 0.45  # Adjusted default zoom
                if bar.get_height() < 10:
                    zoom_level = 0.3
                elif bar.get_height() > 50:
                    zoom_level = 0.55

                im = OffsetImage(icon_img, zoom=zoom_level)
                ab = AnnotationBbox(
                    im,
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    frameon=False,
                    box_alignment=(0.5, -0.1),  # Fine-tuned alignment
                    pad=0.2
                )
                ax.add_artist(ab)
            except Exception as e:
                print(f"Failed to load or place icon for {name} ({icon_path_str}): {e}")
        else:
            print(f"Icon path not found for {name}: {icon_path_str}")

    plt.tight_layout(pad=3.0)  # Increased padding
    plt.savefig("kitt_scale_plot.png", dpi=300)  # Increased resolution
    print("Plot saved to kitt_scale_plot.png")
    plt.show()
    plt.close()


# --- Main Execution Block ---
if __name__ == "__main__":
    default_author_name = "Stephen Hawking"
    default_hawking_quote = (
        "IF you remember every word in this book, your memory will have "
        "recorded about two million pieces of information: the order in your "
        "brain will have increased by about two million units. However, while "
        "you have been reading the book, you will have converted at least a "
        "thousand calories of ordered energy, in the form of food, into "
        "disordered energy, in the form of heat that you lose to the air around "
        "you by convection and sweat. This will increase the disorder of the "
        "universe by about twenty million million million million units - or "
        "about ten million million million times the increase in order in your "
        "brain - and that's if you remember everything in this book."
    )

    user_name_input = input(f"Enter author's name (or press Enter for '{default_author_name}'): ").strip()
    author_name_to_use = user_name_input or default_author_name

    if author_name_to_use == default_author_name:
        user_text_input = input(
            f"Enter text by {author_name_to_use} to evaluate (or press Enter for default quote):\n").strip()
        sample_text_to_analyze = user_text_input or default_hawking_quote
    else:  # Custom author name
        user_text_input = input(f"Enter text by {author_name_to_use} to evaluate:\n").strip()
        if not user_text_input:
            print(f"No text provided for {author_name_to_use}. Exiting.")
            exit()
        sample_text_to_analyze = user_text_input

    try:
        if not openai.api_key:
            print("OPENAI_API_KEY is not set in the environment. Please set it to run the example.")
        else:
            print(
                f"\nStarting evaluation for text by '{author_name_to_use}' (max duration ~120s for up to 4 sentences):")
            print(f"'''\n{sample_text_to_analyze.strip()}\n'''")
            print(f"Max sentences to analyze: {4}\n")

            final_score_pct, api_tokens = llm_or_human(sample_text_to_analyze, max_sentences=4)

            print("\n--- Evaluation Summary ---")
            print(f"Returned Final Score for '{author_name_to_use}': {final_score_pct:.2f}%")
            print(f"Returned API Tokens Used (non-cached): {api_tokens}")

            if final_score_pct is not None:
                plot_with_icons(final_score_pct, author_name_to_use)
            else:
                print("Skipping plot as no final score was generated.")

    except KeyboardInterrupt:
        print("\nMain script execution interrupted by user.")
    finally:
        print("Exiting isitllm.py script.")