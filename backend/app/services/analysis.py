import json

import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2"

_EMPTY_ACTION_VALUES = {"", "none", "n/a", "na", "null", "no action", "no action item", "no action items"}
_CLIENT = httpx.Client(timeout=90.0)

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "owner": {"type": ["string", "null"]},
                    "deadline": {"type": ["string", "null"]},
                },
                "required": ["task", "owner", "deadline"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "summary", "key_points", "action_items"],
    "additionalProperties": False,
}


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

    prompt = (
        "Analyze only the transcript. Do not invent facts. Preserve its language. "
        "Give a short title, a summary of at most two sentences, at most four concise key points, "
        "and only explicit action items. If there are no explicit actions, use an empty array. "
        "Owner and deadline must be null unless explicitly stated.\n\n"
        f"TRANSCRIPT:\n{transcript}"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": ANALYSIS_SCHEMA,
        "keep_alive": "30m",
        "messages": [{"role": "user", "content": prompt}],
        "options": {
            "temperature": 0.0,
            "num_predict": 220,
            "num_ctx": 2048,
        },
    }

    response = _CLIENT.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    content = response.json()["message"]["content"]

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        # Make failures diagnosable without silently accepting malformed model output.
        preview = content[:500].replace("\n", " ")
        raise ValueError(f"Ollama returned malformed structured JSON: {preview}") from exc

    return _normalize_analysis(result)
