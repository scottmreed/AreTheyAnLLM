# AreTheyAnLLM

> *“In the future, even our most human selves might reveal they’re not so human after all.”*

A playful toolkit for sniffing out large-language-model output—whether it’s typed or spoken—and ranking it on Scott’s bespoke “KITT Scale.”

---

## 🚀 What’s Inside

- **Text Detective**:  
  Feed any snippet to `isitllm.check(...)` and get back a likelihood score (0–100%) of “LLM-ness.”

- **Voice Inspector**:  
  Speak into your mic; our realtime client streams audio to OpenAI’s `gpt-4o-mini-transcribe`, logs the transcript, then scores it in chunks.

- **Transcript Log**:  
  All your deltas (Δ) and completions (✔) land in `transcript.txt` for post-mortem reading.

- **KITT Scale Benchmarks**:  
  1. **Knight Industries Two Thousand** (KITT, _Knight Rider_ Trans Am): **6.25%**  
     ![KITT car](image0)  
  2. **Al Gore Acceptance Speech**: **17.71%**  
     ![Al Gore](image1)  
  3. **Elizabeth Holmes Bio Excerpt**: **27.42%**  
     ![Elizabeth Holmes](image2)  
  4. **James Joyce, *Finnegans Wake* (“riverrun”…)**: **2.45%**  
     ![James Joyce](image3)  

---

## 📖 Getting Started

1. **Clone** this repo  
   ```bash
   git clone https://github.com/your-org/AreTheyAnLLM.git
   cd AreTheyAnLLM
2. **Install dependencies**
pip install -r requirements.txt
Configure
Create a .env file containing:
OPENAI_API_KEY=sk-...
🛠️ Usage

Text mode
from isitllm import llm_or_human

snippet = "In a hole in the ground there lived a hobbit..."
score = llm_or_human(snippet)
print(f"LLM Probability: {score*100:.2f}%")
Voice mode
python realtime_transcribe_detect_with_logging.py
# → speak for 15 seconds (or press ENTER to stop early)
Check transcript.txt for the full Δ/✔ log.
Watch your LLM score roll in every 5 s chunk.
🤝 Contributing

Pull requests welcome!

Add more benchmarks to the KITT Scale
Tweak flush intervals or model choice
Improve the LLM detector algorithm
📜 License

MIT © 2025 Scott Reed


