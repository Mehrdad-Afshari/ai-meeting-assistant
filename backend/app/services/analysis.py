import json

import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2"

_EMPTY_ACTION_VALUES = {"", "none", "n/a", "na", "null", "no action", "no action item", "no action items"}
_CLIENT = httpx.Client(timeout=90.0)


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
    result["key_points"] = [str(point).strip() for point in (result.get("key_points") or []) if str(point).strip()][:4]
    return result


def analyze_transcript(transcript: str) -> dict:
    transcript = transcript.strip()
    if not transcript:
        raise ValueError("Transcript is empty.")

    # Keep the task and output deliberately compact: local generation speed is
    # dominated by the number of output tokens on CPU.
    prompt = (
        "Analyze only the transcript. No invented facts. Preserve its language. "
        "Return compact JSON: title:string, summary:string (max 2 sentences), "
        "key_points:string[] (max 4), action_items:[{task,owner,deadline}]. "
        "Only explicit actions; otherwise []. owner/deadline null unless stated.\n\n"
        f"TRANSCRIPT:\n{transcript}"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "keep_alive": "30m",
        "messages": [{"role": "user", "content": prompt}],
        "options": {
            "temperature": 0.0,
            "num_predict": 180,
            "num_ctx": 2048,
        },
    }

    response = _CLIENT.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    content = response.json()["message"]["content"]
    return _normalize_analysis(json.loads(content))
