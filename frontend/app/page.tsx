"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { BrainCircuit, FileAudio, LockKeyhole, MessageSquareText, Sparkles, UploadCloud } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type ActionItem = { task: string; owner: string | null; deadline: string | null };
type Analysis = { title: string; summary: string; key_points: string[]; action_items: ActionItem[] };
type Meeting = {
  id: string; filename: string; created_at: string; language?: string | null; duration?: number | null;
  transcript?: string | null; analysis?: Analysis | null; transcribed?: boolean;
};

export default function Home() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState(0);
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [history, setHistory] = useState<Meeting[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");

  async function loadHistory() {
    try { const r = await fetch(`${API}/meetings`); if (r.ok) setHistory(await r.json()); } catch { /* backend may be offline */ }
  }
  useEffect(() => { loadHistory(); }, []);

  function chooseFile(e: ChangeEvent<HTMLInputElement>) { setFile(e.target.files?.[0] || null); setError(""); }

  async function processRecording() {
    if (!file) return;
    setBusy(true); setError(""); setAnswer(""); setStage(0);
    try {
      const form = new FormData(); form.append("file", file);
      const upload = await fetch(`${API}/meetings/upload`, { method: "POST", body: form });
      if (!upload.ok) throw new Error("Upload failed");
      const uploaded = await upload.json(); setStage(1);

      const tr = await fetch(`${API}/meetings/${uploaded.meeting_id}/transcribe`, { method: "POST" });
      if (!tr.ok) throw new Error((await tr.json()).detail || "Transcription failed");
      setStage(2);

      const ar = await fetch(`${API}/meetings/${uploaded.meeting_id}/analyze`, { method: "POST" });
      if (!ar.ok) throw new Error((await ar.json()).detail || "AI analysis failed");
      setStage(3);

      const detail = await fetch(`${API}/meetings/${uploaded.meeting_id}`);
      setMeeting(await detail.json()); await loadHistory();
    } catch (e) { setError(e instanceof Error ? e.message : "Something went wrong"); }
    finally { setBusy(false); }
  }

  async function openMeeting(id: string) {
    setError(""); setAnswer("");
    try { const r = await fetch(`${API}/meetings/${id}`); if (!r.ok) throw new Error("Meeting not found"); setMeeting(await r.json()); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not load meeting"); }
  }

  async function ask() {
    if (!meeting || !question.trim()) return;
    setBusy(true); setError(""); setAnswer("");
    try {
      const r = await fetch(`${API}/meetings/${meeting.id}/ask`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({question}) });
      const data = await r.json(); if (!r.ok) throw new Error(data.detail || "Q&A failed"); setAnswer(data.answer);
    } catch(e) { setError(e instanceof Error ? e.message : "Q&A failed"); }
    finally { setBusy(false); }
  }

  return <main className="shell"><div className="container">
    <header className="header"><div className="brand"><div className="logo"><BrainCircuit size={21}/></div>AI Meeting Assistant</div><div className="badge"><LockKeyhole size={12} style={{display:"inline",marginRight:6}}/>Local AI · Privacy First</div></header>

    <section className="hero"><div className="eyebrow">Whisper + Ollama + FastAPI</div><h1>Turn conversations into useful knowledge.</h1><p>Upload a meeting or lecture recording. Local AI transcribes it, extracts the essentials and lets you ask grounded questions without sending your content to a cloud AI service.</p></section>

    <section className="grid">
      <article className="card"><h2>Process a recording</h2><p>MP3, WAV, M4A, MP4, WebM or OGG.</p>
        <div className="drop" onClick={()=>inputRef.current?.click()}><div><div className="dropIcon"><UploadCloud/></div><strong>{file ? file.name : "Choose a recording"}</strong><p className="muted">Click to select an audio or video file</p></div></div>
        <input ref={inputRef} className="fileInput" type="file" accept="audio/*,video/mp4,video/webm" onChange={chooseFile}/>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginTop:16,gap:12}}><span className="muted">Runs locally on your machine</span><button className="primary" disabled={!file||busy} onClick={processRecording}>{busy ? "Processing…" : "Transcribe & Analyze"}</button></div>
        <div className="status"><span className={`pill ${stage>=1?"done":""}`}>1 Upload</span><span className={`pill ${stage>=2?"done":""}`}>2 Whisper</span><span className={`pill ${stage>=3?"done":""}`}>3 AI Analysis</span></div>{error&&<div className="error">{error}</div>}
      </article>

      <aside className="card"><h2>Meeting history</h2><p>Your locally stored recordings and analyses.</p><div className="history">{history.length===0?<div className="muted">No meetings yet.</div>:history.slice(0,7).map(m=><button className="historyItem" key={m.id} onClick={()=>openMeeting(m.id)}><strong>{m.analysis?.title || m.filename}</strong><small>{m.filename} · {m.language || "—"}{m.duration ? ` · ${Math.round(m.duration)}s` : ""}</small></button>)}</div></aside>

      {meeting && <article className="card result"><div style={{display:"flex",gap:14,alignItems:"center"}}><div className="dropIcon" style={{margin:0,width:46,height:46}}><FileAudio size={20}/></div><div><h2>{meeting.analysis?.title || meeting.filename}</h2><span className="muted">{meeting.filename} · {meeting.language || "unknown language"}</span></div></div>
        <div className="resultGrid">
          <section className="panel"><h3><Sparkles size={15} style={{display:"inline",marginRight:7}}/>AI Summary</h3><p>{meeting.analysis?.summary || "No analysis yet."}</p></section>
          <section className="panel"><h3>Key Points</h3><ul>{meeting.analysis?.key_points?.map((x,i)=><li key={i}>{x}</li>)}</ul></section>
          <section className="panel"><h3>Action Items</h3>{meeting.analysis?.action_items?.length ? <ul>{meeting.analysis.action_items.map((x,i)=><li key={i}>{x.task}{x.owner?` — ${x.owner}`:""}{x.deadline?` · ${x.deadline}`:""}</li>)}</ul>:<p className="muted">No explicit action items detected.</p>}</section>
          <section className="panel"><h3>Transcript</h3><div className="transcript">{meeting.transcript || "No transcript available."}</div></section>
        </div>
        <section className="panel" style={{marginTop:16}}><h3><MessageSquareText size={15} style={{display:"inline",marginRight:7}}/>Ask this meeting</h3><div className="ask"><input value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>e.key==="Enter"&&ask()} placeholder="Ask a question grounded in the transcript…"/><button className="primary" disabled={busy||!question.trim()} onClick={ask}>Ask AI</button></div>{answer&&<div className="answer">{answer}</div>}</section>
      </article>}
    </section>
  </div></main>;
}