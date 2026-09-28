# AI Meeting & Lecture Assistant

A privacy-first, local AI application that turns meeting and lecture recordings into useful knowledge.

## Planned MVP

- Upload audio recordings
- Local speech-to-text transcription with Whisper
- Structured AI summaries
- Key points and action-item extraction
- Question answering over transcripts
- Meeting history stored in SQLite
- Local LLM inference with Ollama

## Tech Stack

**Frontend:** Next.js, TypeScript, Tailwind CSS  
**Backend:** FastAPI, Python, Pydantic  
**Speech-to-Text:** Whisper / faster-whisper  
**AI:** Ollama + local LLM  
**Database:** SQLite  

## Architecture

```text
Audio / Video
     |
     v
FastAPI Upload API
     |
     v
Whisper Transcription
     |
     +--------------------+
     |                    |
     v                    v
Structured Summary     Transcript
Key Points             Storage
Action Items              |
     |                    v
     +--------------> SQLite
                          |
                          v
                    Transcript Q&A
                          |
                          v
                       Ollama
```

## Project Status

🚧 MVP under active development.

## Goals

This project demonstrates practical experience with speech-to-text, local AI inference, structured information extraction, persistence, API design, and modern full-stack development.

## Author

Mehrdad Afshari  
M.Sc. Computer Science student, University of Rostock  
AI & Software Developer
