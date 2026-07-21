# LectureLens 🎓

AI-powered lecture video assistant that goes beyond subtitles — it transcribes, simplifies, builds a glossary, and generates quizzes from any lecture video, completely free and open source.

---

## 🚀 Features

- **Auto Transcription** — Converts lecture audio/video into a timestamped transcript using faster-whisper (runs locally, free).
- **Subtitle Generation** — Exports transcripts as standard `.srt` and `.vtt` subtitle files.
- **Dual-Mode Summarization** — Every lecture is summarized in two ways:
  - **Technical** — Uses original terminology in a concise format.
  - **Simple (ELI-Junior)** — Explains concepts in plain English with easy analogies.
- **Auto Glossary** — Detects technical terms and generates timestamped one-line definitions.
- **Quiz Generator** — Automatically generates MCQs and short-answer questions, with a weak-area detector that links incorrect answers back to the relevant lecture timestamp.

---

## 🛠️ Tech Stack

| Component | Tool |
|-----------|------|
| Transcription | faster-whisper (Local) |
| AI Summarization / Quiz / Glossary | Groq API (Free Tier) |
| Frontend | Streamlit |
| Backend | Python |
| Subtitle Generation | Python |
| Environment | Virtual Environment (`venv`) |

---

## 📁 Project Structure

```text
LectureLens/
│
├── backend/
│   ├── transcription/
│   │   └── transcriber.py
│   ├── subtitle_generation/
│   │   └── subtitle_generator.py
│   ├── summarization/
│   │   └── summarizer.py
│   ├── quiz_generation/
│   │   └── quiz_generator.py
│   └── utils/
│       ├── config.py
│       └── prompts.py
│
├── frontend/
│   └── app.py
│
├── data/
│
├── output/
│   ├── transcripts/
│   ├── subtitles/
│   └── quizzes/
│
├── tests/
│
├── .gitignore
├── .env.example
├── README.md
└── requirements.txt
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/geetanksahare/LectureLens.git
cd LectureLens
```

### 2. Create a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Install FFmpeg

FFmpeg is required by **faster-whisper**.

**Windows (Chocolatey)**

```bash
choco install ffmpeg
```

**macOS (Homebrew)**

```bash
brew install ffmpeg
```

**Ubuntu / Debian**

```bash
sudo apt update
sudo apt install ffmpeg
```

---

### 5. Configure the API Key

Create a `.env` file from the example:

```bash
cp .env.example .env
```

For Windows PowerShell:

```powershell
copy .env.example .env
```

Get your free API key from:

https://console.groq.com

Add it to your `.env` file:

```env
GROQ_API_KEY=your_actual_key_here
```

---

### 6. Run the application

```bash
streamlit run frontend/app.py
```

> **Note:** Run this command from the project root directory, not from inside the `frontend` folder.

---

## 🔄 Project Workflow

```text
               Lecture Video / Audio
                        │
                        ▼
            faster-whisper Transcription
                        │
                        ▼
             Timestamped Transcript
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
  Subtitle Generator  Summarizer     Glossary Generator
        │               │                │
        ▼               ▼                ▼
     .srt / .vtt   Technical + Simple    Key Terms
                        │
                        ▼
                 Quiz Generator
                        │
                        ▼
           MCQs + Short Answer Questions
```

---

## 💰 Cost

LectureLens is designed to be completely free for learning and academic projects.

- ✅ **faster-whisper** runs locally (no API cost).
- ✅ **Groq API Free Tier** is sufficient for demo projects and small-scale usage.
- ✅ No paid AI subscriptions are required.

---

## 📌 Project Status

- ✅ Transcription Module
- ✅ Subtitle Generation
- ✅ Summarization Module
- ✅ Quiz Generator
- 🚧 Streamlit Frontend (In Progress)
- 🚧 Glossary Module
- 🚧 Export Features

---

## 🤝 Contributors

- **Geetank Sahare**
- **Anjali Pal**
- **Sahil Singh**

Final Year B.Tech Project

---

## 📄 License

This project is developed for educational and research purposes.
