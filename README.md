# 🎙️ MeetMind: AI Meeting Assistant

Upload a meeting recording and MeetMind gives you a **transcript, summary, decisions, action items, a follow-up email**, and a **chat** where you can ask questions about the meeting.

> Built step by step as a learning project: Colab prototype → Streamlit app → Docker container.

---

## ✨ Features

| Feature | What it does |
| --- | --- |
| 📝 **Transcript** | Whisper speech-to-text with `[MM:SS]` timestamps, plus optional name hints for better spelling |
| 🎯 **Decisions** | What the team agreed: dates, budgets, goals |
| ✅ **Action items** | Who does what, and by when, in a clean table |
| 🔍 **Self-checking** | A checker agent compares the notes with the transcript and sends them back for fixing if something is wrong |
| 📧 **Follow-up email** | A ready-to-send summary email, downloadable |
| 💬 **Chat** | Ask *"Why was the launch delayed?"* and get an answer with the timestamp. Things never discussed are refused, not invented |

---

## 🧠 How it works

```
Audio ─► Whisper (Groq) ─► timestamped transcript
                               │
                   LangGraph agents (GPT-OSS 120B)
        ┌─────────────────────────────────────────────┐
        │  notes ─► checker ─► issues? ─ yes ─► notes │  (max 2 tries)
        │                        └ no ──► email       │
        └─────────────────────────────────────────────┘
                               │
               Streamlit UI: notes · email · transcript · chat
```

- **Notes agent:** extracts summary, decisions and action items as JSON, validated with **Pydantic**
- **Checker agent:** looks for wrong causes, missing decisions, wrong owners and invented deadlines
- **Email agent:** drafts the follow-up email using only facts from the notes

---

## 🛠️ Tech stack

`Python` · `Groq API` (Whisper large-v3, GPT-OSS 120B) · `LangGraph` · `Pydantic` · `Streamlit` · `pandas` · `Docker` · `Git`

---

## 🚀 Run it

### Option 1: Python
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m streamlit run app.py
```

### Option 2: Docker
```bash
docker build -t meetmind .
docker run -p 8501:8501 meetmind
```
Open **http://localhost:8501**, paste your free [Groq API key](https://console.groq.com) in the sidebar, upload a recording and click **Analyze meeting**.

You can also set the key as an environment variable, `GROQ_API_KEY`, instead of typing it in the sidebar.

---

## 📁 Project structure

```
MeetMind/
├── app.py               # Streamlit web page
├── meetmind_core.py     # AI logic: Whisper, agents, chat
├── style.css            # custom dark design
├── .streamlit/config.toml
├── requirements.txt
├── Dockerfile
└── test_core.py         # quick test of the AI logic without the UI
```

---

## 🐞 What I learned

- **Retrieval vs generation bugs.** In the Colab prototype, *"Why was the launch delayed?"* kept returning a side benefit ("more time for marketing") instead of the real cause (an iOS bug). The search *had* found the right part of the meeting, but the cause and the decision were in different chunks. Using the **full transcript for short meetings** fixed it: test questions went from **3/4 to 4/4**.
- **LLMs invent details.** An early version invented a deadline nobody stated. A strict prompt rule plus the checker agent removed it.
- **Results vary between runs.** The same meeting sometimes assigned a task to the wrong person, because the transcript doesn't say *who* is speaking.
- **Docker layer caching.** Copying `requirements.txt` before the code, plus a `.dockerignore`, cut the build context from **392 MB to 329 bytes** and rebuilds from minutes to seconds.

---

## 🗺️ Roadmap

- [ ] Speaker diarization (who said what), to fix wrong task owners
- [ ] Evaluation on a 5-meeting test set with an answer key (decision accuracy, action-item F1, hallucination rate)
- [ ] Hybrid RAG (FAISS + BM25 + multi-query) in the app for long meetings (already prototyped in Colab)
- [ ] Prompt-injection guardrail
- [ ] Demo video

---

## 👩‍💻 Author

**Yugadharshini Sundharakumar**, AI/ML Engineer
[GitHub](https://github.com/skrYugadharshini) · [LinkedIn](https://www.linkedin.com/in/yugadharshini-sundharakumar/)
