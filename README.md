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
     ![KITT car](images/readme/kitt.png)

  2. **Al Gore Acceptance Speech**: **17.71%**
     ![Al Gore](images/readme/al_gore.png)

  3. **Elizabeth Holmes Bio Excerpt**: **27.42%**
     ![Elizabeth Holmes](images/readme/elizabeth_holmes.png)

  4. **James Joyce, *Finnegans Wake* (“riverrun”…)**: **2.45%**
     ![James Joyce](images/readme/james_joyce.png)


---

## 📖 Getting Started

1. **Clone** this repo
   ```bash
   git clone https://github.com/your-org/AreTheyAnLLM.git
   cd AreTheyAnLLM
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure**
   Create a `.env` file containing:
   ```
   OPENAI_API_KEY=sk-...
   ```

### 🛠️ Usage

**Text mode**
```python
from isitllm import llm_or_human

snippet = "In a hole in the ground there lived a hobbit..."
score = llm_or_human(snippet)
print(f"LLM Probability: {score*100:.2f}%")
```

**Voice mode**
```bash
python realtime_transcribe_detect_with_logging.py
```
Speak for 15 seconds (or press ENTER to stop early). Check `transcript.txt` for the full Δ/✔ log and watch your score roll in every 5 s chunk.

### Image Resizing

Run `python resize_images.py` to download the benchmark images and create half-sized versions for this README under `images/readme/` as well as 50x50 icons under `images/icons/`.

### 🤝 Contributing

Pull requests welcome!

- Add more benchmarks to the KITT Scale
- Tweak flush intervals or model choice
- Improve the LLM detector algorithm

### 📜 License

MIT © 2025 Scott Reed


