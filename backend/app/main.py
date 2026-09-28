from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.analysis import analyze_transcript
from app.services.database import create_meeting, get_meeting, init_db, list_meetings, save_analysis, save_transcript
from app.services.qa import answer_question
from app.services.transcription import transcribe_audio

app = FastAPI(
    title="AI Meeting & Lecture Assistant API",
    version="0.4.0",
    description="Local-first API for transcription, structured analysis, history, and transcript Q&A.",
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
TRANSCRIPT_DIR = BASE_DIR / "data" / "transcripts"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
init_db()

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


class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    deadline: str | None = None


class AnalysisResponse(BaseModel):
    meeting_id: str
    title: str
    summary: str
    key_points: list[str]
    action_items: list[ActionItem]


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    meeting_id: str
    question: str
    answer: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ai-meeting-assistant")


@app.get("/meetings")
def meetings_history() -> list[dict]:
    return list_meetings()


@app.get("/meetings/{meeting_id}")
def meeting_detail(meeting_id: str) -> dict:
    meeting = get_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return meeting


@app.post("/meetings/upload", response_model=UploadResponse)
async def upload_meeting(file: UploadFile = File(...)) -> UploadResponse:
    original_name = Path(file.filename or "recording").name
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported media type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    meeting_id = str(uuid4())
    destination = UPLOAD_DIR / f"{meeting_id}{extension}"
    with destination.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            output.write(chunk)
    await file.close()
    create_meeting(meeting_id, original_name)
    return UploadResponse(meeting_id=meeting_id, filename=original_name, message="Upload successful.")


@app.post("/meetings/{meeting_id}/transcribe", response_model=TranscriptionResponse)
def transcribe_meeting(meeting_id: str, language: str | None = None) -> TranscriptionResponse:
    matches = list(UPLOAD_DIR.glob(f"{meeting_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Meeting recording not found.")
    try:
        result = transcribe_audio(matches[0], language=language)
        (TRANSCRIPT_DIR / f"{meeting_id}.txt").write_text(result["text"], encoding="utf-8")
        save_transcript(meeting_id, result["text"], result["language"], result["duration"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc
    return TranscriptionResponse(meeting_id=meeting_id, **result)


@app.post("/meetings/{meeting_id}/analyze", response_model=AnalysisResponse)
def analyze_meeting(meeting_id: str) -> AnalysisResponse:
    meeting = get_meeting(meeting_id)
    transcript = (meeting or {}).get("transcript")
    if not transcript:
        transcript_path = TRANSCRIPT_DIR / f"{meeting_id}.txt"
        if transcript_path.exists():
            transcript = transcript_path.read_text(encoding="utf-8")
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found. Transcribe the meeting first.")
    try:
        result = analyze_transcript(transcript)
        if meeting is not None:
            save_analysis(meeting_id, result)
        return AnalysisResponse(meeting_id=meeting_id, **result)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Local AI analysis failed: {exc}") from exc


@app.post("/meetings/{meeting_id}/ask", response_model=AnswerResponse)
def ask_meeting(meeting_id: str, request: QuestionRequest) -> AnswerResponse:
    meeting = get_meeting(meeting_id)
    transcript = (meeting or {}).get("transcript")
    if not transcript:
        transcript_path = TRANSCRIPT_DIR / f"{meeting_id}.txt"
        if transcript_path.exists():
            transcript = transcript_path.read_text(encoding="utf-8")
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found. Transcribe the meeting first.")
    try:
        answer = answer_question(transcript, request.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Local AI Q&A failed: {exc}") from exc
    return AnswerResponse(meeting_id=meeting_id, question=request.question, answer=answer)
