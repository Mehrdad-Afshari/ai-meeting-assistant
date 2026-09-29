import json

import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2"

_EMPTY_ACTION_VALUES = {"", "none", "n/a", "na", "null", "no action", "no action item", "no action items"}


def _normalize_analysis(result: dict) -> dict:
    actions = result.get("action_items") or []
    cleaned_actions = []
    for item in actions:
        if not isinstance(item, dict):
            continue
        task = str(item.get("task") or "").strip()
        if task.lower().rstrip(".") in _EMPTY_ACTION_VALUES:
            continue
        cleaned_actions.append({"task": task, "owner": item.get("owner"), "deadline": item.get("deadline")})
    result["action_items"] = cleaned_actions
    result["key_points"] = [str(point).strip() for point in (result.get("key_points") or []) if str(point).strip()]
    return result


def analyze_transcript(transcript: str) -> dict:
    if not transcript.strip():
        raise ValueError("Transcript is empty.")

    # Compact instructions reduce prompt processing and generation latency on local CPU inference.
    prompt = f"""Analyze only this transcript. Return JSON with exactly: title (short), summary (1-2 sentences), key_points (max 5 concise strings), action_items (array of objects with task, owner, deadline). Preserve transcript language. Do not invent facts. Only include explicit actions; otherwise action_items=[]. owner/deadline must be null unless explicit.

TRANSCRIPT:
{transcript}"""

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "keep_alive": "10m",
        "messages": [{"role": "user", "content": prompt}],
        "options": {
            "temperature": 0.0,
            "num_predict": 300,
            "num_ctx": 4096,
        },
    }

    with httpx.Client(timeout=120.0) as client:
        response = client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
    content = response.json()["message"]["content"]
    return _normalize_analysis(json.loads(content))
