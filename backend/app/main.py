from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.analysis import analyze_transcript
from app.services.database import create_meeting, get_meeting, init_db, list_meetings, save_analysis, save_transcript, delete_meeting, clear_meetings
from app.services.qa import answer_question
from app.services.transcription import transcribe_audio

app = FastAPI(title="AI Meeting & Lecture Assistant API", version="0.5.0", description="Local-first API for transcription, structured analysis, history, export-ready data, and grounded transcript Q&A.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "data" / "uploads"; TRANSCRIPT_DIR = BASE_DIR / "data" / "transcripts"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True); TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True); init_db()
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg"}

class HealthResponse(BaseModel): status:str; service:str
class UploadResponse(BaseModel): meeting_id:str; filename:str; message:str
class TranscriptSegment(BaseModel): start:float; end:float; text:str
class TranscriptionResponse(BaseModel): meeting_id:str; text:str; language:str; language_probability:float; duration:float; model:str; segments:list[TranscriptSegment]; processing_seconds:float
class ActionItem(BaseModel): task:str; owner:str|None=None; deadline:str|None=None
class AnalysisResponse(BaseModel): meeting_id:str; title:str; summary:str; key_points:list[str]; action_items:list[ActionItem]; processing_seconds:float
class QuestionRequest(BaseModel): question:str
class AnswerResponse(BaseModel): meeting_id:str; question:str; answer:str

@app.get("/health", response_model=HealthResponse)
def health(): return HealthResponse(status="ok", service="ai-meeting-assistant")
@app.get("/meetings")
def meetings_history(): return list_meetings()
@app.get("/meetings/{meeting_id}")
def meeting_detail(meeting_id:str):
    meeting=get_meeting(meeting_id)
    if meeting is None: raise HTTPException(404,"Meeting not found.")
    return meeting
@app.delete("/meetings/{meeting_id}")
def remove_meeting(meeting_id:str):
    if not get_meeting(meeting_id): raise HTTPException(404,"Meeting not found.")
    for path in list(UPLOAD_DIR.glob(f"{meeting_id}.*")) + [TRANSCRIPT_DIR / f"{meeting_id}.txt"]:
        if path.exists(): path.unlink()
    delete_meeting(meeting_id)
    return {"deleted": True, "meeting_id": meeting_id}
@app.delete("/meetings")
def remove_all_meetings():
    for path in UPLOAD_DIR.glob("*"):
        if path.is_file(): path.unlink()
    for path in TRANSCRIPT_DIR.glob("*.txt"): path.unlink()
    return {"deleted": clear_meetings()}

@app.post("/meetings/upload",response_model=UploadResponse)
async def upload_meeting(file:UploadFile=File(...)):
    original_name=Path(file.filename or "recording").name; extension=Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS: raise HTTPException(400,f"Unsupported media type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    meeting_id=str(uuid4()); destination=UPLOAD_DIR/f"{meeting_id}{extension}"
    with destination.open("wb") as output:
        while chunk:=await file.read(1024*1024): output.write(chunk)
    await file.close(); create_meeting(meeting_id,original_name)
    return UploadResponse(meeting_id=meeting_id,filename=original_name,message="Upload successful.")

@app.post("/meetings/{meeting_id}/transcribe",response_model=TranscriptionResponse)
def transcribe_meeting(meeting_id:str,language:str|None=None):
    matches=list(UPLOAD_DIR.glob(f"{meeting_id}.*"))
    if not matches: raise HTTPException(404,"Meeting recording not found.")
    started=perf_counter()
    try:
        result=transcribe_audio(matches[0],language=language); (TRANSCRIPT_DIR/f"{meeting_id}.txt").write_text(result["text"],encoding="utf-8"); save_transcript(meeting_id,result["text"],result["language"],result["duration"])
    except Exception as exc: raise HTTPException(500,f"Transcription failed: {exc}") from exc
    elapsed=round(perf_counter()-started,2); print(f"[timing] transcription {meeting_id}: {elapsed}s")
    return TranscriptionResponse(meeting_id=meeting_id,processing_seconds=elapsed,**result)

@app.post("/meetings/{meeting_id}/analyze",response_model=AnalysisResponse)
def analyze_meeting(meeting_id:str):
    meeting=get_meeting(meeting_id); transcript=(meeting or {}).get("transcript")
    if not transcript:
        p=TRANSCRIPT_DIR/f"{meeting_id}.txt"; transcript=p.read_text(encoding="utf-8") if p.exists() else None
    if not transcript: raise HTTPException(404,"Transcript not found. Transcribe the meeting first.")
    started=perf_counter()
    try:
        result=analyze_transcript(transcript)
        if meeting is not None: save_analysis(meeting_id,result)
    except Exception as exc: raise HTTPException(502,f"Local AI analysis failed: {exc}") from exc
    elapsed=round(perf_counter()-started,2); print(f"[timing] analysis {meeting_id}: {elapsed}s")
    return AnalysisResponse(meeting_id=meeting_id,processing_seconds=elapsed,**result)

@app.post("/meetings/{meeting_id}/ask",response_model=AnswerResponse)
def ask_meeting(meeting_id:str,request:QuestionRequest):
    meeting=get_meeting(meeting_id); transcript=(meeting or {}).get("transcript")
    if not transcript:
        p=TRANSCRIPT_DIR/f"{meeting_id}.txt"; transcript=p.read_text(encoding="utf-8") if p.exists() else None
    if not transcript: raise HTTPException(404,"Transcript not found. Transcribe the meeting first.")
    if not request.question.strip(): raise HTTPException(400,"Question cannot be empty.")
    try: answer=answer_question(transcript,request.question.strip())
    except Exception as exc: raise HTTPException(502,f"Local AI Q&A failed: {exc}") from exc
    return AnswerResponse(meeting_id=meeting_id,question=request.question,answer=answer)
