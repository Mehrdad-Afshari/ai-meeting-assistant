# AI Meeting Assistant

A privacy-first, local AI application that turns meeting and lecture recordings into searchable, structured knowledge.

Built as a full-stack AI portfolio project with **Next.js + TypeScript**, **FastAPI + Python**, **faster-whisper**, **Ollama**, and **SQLite**.

## Why this project?

Meeting assistants are useful, but recordings and transcripts can contain sensitive information. This project explores a **local-first AI workflow**: speech-to-text and LLM processing run on the machine hosting the backend instead of sending meeting content to a cloud AI provider.

## Features

- Upload MP3, WAV, M4A, MP4, WebM, and OGG recordings
- Multilingual local transcription with faster-whisper
- Structured local-AI analysis: title, summary, key points, and action items
- Grounded Q&A over the meeting transcript
- Persistent local meeting history with SQLite
- Delete individual meetings or clear local history
- Export transcript and Markdown meeting notes
- Processing-time feedback for Whisper and AI analysis
- Responsive dark UI
- FastAPI OpenAPI / Swagger documentation

## Architecture

```text
                       local machine
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  Next.js / TypeScript UI                                     │
│          │                                                    │
│          ▼                                                    │
│  FastAPI REST API                                             │
│          │                                                    │
│          ├──── upload ───────► local recording storage        │
│          │                                                    │
│          ├──── transcribe ───► faster-whisper (CPU / int8)    │
│          │                         │                          │
│          │                         ▼                          │
│          │                    transcript                      │
│          │                         │                          │
│          ├──── analyze ──────► Ollama / local LLM             │
│          │                         │                          │
│          │                    structured notes                │
│          │                                                    │
│          ├──── ask ──────────► transcript-grounded Q&A        │
│          │                                                    │
│          └───────────────────► SQLite meeting history         │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, Pydantic |
| Speech-to-text | faster-whisper |
| Local AI | Ollama + local LLM |
| Persistence | SQLite |
| API | REST + OpenAPI |

## Local Setup

### Prerequisites

- Python 3.12 recommended
- Node.js / npm
- Ollama installed and running
- A local Ollama model compatible with the backend configuration

### 1. Clone

```bash
git clone https://github.com/Mehrdad-Afshari/ai-meeting-assistant.git
cd ai-meeting-assistant
```

### 2. Backend

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

The API is available at `http://127.0.0.1:8000` and Swagger documentation at `http://127.0.0.1:8000/docs`.

> On first transcription, faster-whisper may need to download the configured Whisper model. The current implementation uses the multilingual `small` model on CPU with `int8` compute.

### 3. Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

Optionally configure the API URL:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## API Overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Health check |
| GET | `/meetings` | List meeting history |
| GET | `/meetings/{id}` | Get one meeting |
| POST | `/meetings/upload` | Upload a recording |
| POST | `/meetings/{id}/transcribe` | Run local transcription |
| POST | `/meetings/{id}/analyze` | Generate structured analysis |
| POST | `/meetings/{id}/ask` | Ask a transcript-grounded question |
| DELETE | `/meetings/{id}` | Delete one meeting and local files |
| DELETE | `/meetings` | Clear meeting history and local files |

## Privacy Model

The application is designed for local execution. Uploaded recordings, transcripts, structured analyses, and meeting history are stored on the machine running the backend. Whisper inference and Ollama inference also run locally.

This is a portfolio/learning project rather than an audited security product; local-first architecture should not be interpreted as a formal security or compliance guarantee.

## Performance

The backend reuses the Whisper model within a process and uses CPU `int8` inference. Processing time depends on recording length, hardware, Whisper model size, and the selected Ollama model. The UI exposes transcription and analysis timings so performance is visible rather than hidden.

## Repository Structure

```text
ai-meeting-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       ├── analysis.py
│   │       ├── database.py
│   │       ├── qa.py
│   │       └── transcription.py
│   ├── data/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   └── package.json
└── README.md
```

## Current Status

**Portfolio-ready MVP — v0.5.0**

Core end-to-end workflow implemented and manually validated: upload → transcription → local AI analysis → persistence → grounded Q&A → history/export management.

## Engineering Focus

This project demonstrates practical work with:

- local AI inference and privacy-aware architecture
- speech-to-text pipelines
- structured LLM output handling
- grounded question answering
- REST API design
- local persistence and lifecycle management
- full-stack TypeScript/Python integration
- latency measurement and iterative performance optimization

## Roadmap

Potential future extensions include speaker diarization, timestamp-aware Q&A, semantic retrieval for long meetings, richer exports, automated tests, and containerized deployment.

## Author

**Mehrdad Afshari**  
M.Sc. Computer Science student at the University of Rostock, Germany  
AI & Software Development
