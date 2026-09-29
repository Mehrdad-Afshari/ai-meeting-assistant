# Architecture

## Design goal

AI Meeting Assistant is intentionally local-first. The browser provides the interaction layer, FastAPI orchestrates the workflow, faster-whisper performs speech-to-text, Ollama performs language-model tasks, and SQLite persists meeting metadata and generated content.

## Request flow

### Recording processing

1. The Next.js client uploads a supported recording to FastAPI.
2. FastAPI assigns a UUID and stores the media file locally.
3. The transcription endpoint invokes the cached faster-whisper model.
4. The transcript, detected language, and duration are persisted.
5. The analysis endpoint sends the transcript to the configured local Ollama model.
6. Structured analysis is validated/normalized by the backend and stored in SQLite.
7. The client retrieves the complete meeting and renders summary, key points, action items, transcript, and timing information.

### Grounded Q&A

1. The client submits a question for a meeting ID.
2. The backend loads that meeting's transcript.
3. The Q&A service instructs the local model to answer from transcript context.
4. If information is absent, the intended behavior is to state that it is not present rather than invent an answer.

## Components

### Frontend

Next.js and TypeScript provide upload, progress state, meeting history, analysis presentation, exports, deletion controls, and transcript Q&A.

### API

FastAPI exposes REST endpoints and automatically provides OpenAPI/Swagger documentation. Pydantic response models define the public shapes for transcription, analysis, and Q&A responses.

### Speech-to-text

`faster-whisper` uses the multilingual `small` model. The model is cached per backend process and currently runs on CPU with `int8` compute. Greedy decoding and VAD are used to keep local latency practical.

### Local language model

Ollama is used for structured analysis and transcript-grounded Q&A. No cloud LLM is required by the application workflow.

### Persistence

SQLite stores meeting metadata, transcript text, language, duration, and structured analysis. Uploaded recordings and transcript text files are stored under `backend/data`.

## Trust boundaries

The intended trust boundary is the machine running the backend. Meeting content is processed and persisted there. The architecture avoids a cloud AI dependency, but this project has not undergone a formal security or compliance audit.

## Current trade-offs

- Local inference improves privacy but depends strongly on local hardware.
- The Whisper `small` model balances accuracy and CPU latency rather than maximizing either one.
- Full transcripts are currently supplied to local LLM operations; retrieval/chunking is a future extension for long recordings.
- SQLite is appropriate for the single-machine portfolio MVP; a multi-user deployment would require a different persistence and authorization design.
