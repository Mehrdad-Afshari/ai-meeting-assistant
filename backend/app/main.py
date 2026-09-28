from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.transcription import transcribe_audio

app = FastAPI(
    title="AI Meeting & Lecture Assistant API",
    version="0.2.0",
    description="Local-first API for transcription and AI-assisted meeting analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg"}


class HealthResponse(BaseModel):
    status: str
    service: str


class UploadResponse(BaseModel):
    meeting_id: str
    filename: str
    message: str


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionResponse(BaseModel):
    meeting_id: str
    text: str
    language: str
    language_probability: float
    duration: float
    model: str
    segments: list[TranscriptSegment]


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-meeting-assistant")


@app.post("/meetings/upload", response_model=UploadResponse)
async def upload_meeting(file: UploadFile = File(...)) -> UploadResponse:
    original_name = Path(file.filename or "recording").name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported media type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    meeting_id = str(uuid4())
    destination = UPLOAD_DIR / f"{meeting_id}{extension}"

    with destination.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            output.write(chunk)

    await file.close()

    return UploadResponse(
        meeting_id=meeting_id,
        filename=original_name,
        message="Upload successful. Use the transcription endpoint with this meeting ID.",
    )


@app.post("/meetings/{meeting_id}/transcribe", response_model=TranscriptionResponse)
def transcribe_meeting(meeting_id: str, language: str | None = None) -> TranscriptionResponse:
    matches = list(UPLOAD_DIR.glob(f"{meeting_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Meeting recording not found.")

    media_path = matches[0]
    try:
        result = transcribe_audio(media_path, language=language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc

    return TranscriptionResponse(meeting_id=meeting_id, **result)
