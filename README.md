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
     ![KITT car](image0)  ![1-pontiac-firebird-trans-am-982-knight-industries-two-thousand-kitt-knight-rider-vladyslav-shapovalenko](https://github.com/user-attachments/assets/50d8e290-3936-4094-8f98-b983b4a0cdce)

  2. **Al Gore Acceptance Speech**: **17.71%**  
     ![Al Gore](image1)  ![POW27_A](https://github.com/user-attachments/assets/1e032170-d5d9-4409-a1e6-bb58c39df63e)

  3. **Elizabeth Holmes Bio Excerpt**: **27.42%**  
     ![Elizabeth Holmes](image2)  ![4010bc283493b480fec16dc40e9f682f](https://github.com/user-attachments/assets/841a7863-b149-48d6-830b-7a5a8b403fd5)

  4. **James Joyce, *Finnegans Wake* (“riverrun”…)**: **2.45%**  
     ![James Joyce](image3)  ![th](https://github.com/user-attachments/assets/0cf42037-23ae-4163-ba04-e84592bd7eec)


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


