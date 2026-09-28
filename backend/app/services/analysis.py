import json

import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2"

_EMPTY_ACTION_VALUES = {"", "none", "n/a", "na", "null", "no action", "no action item", "no action items"}


def _normalize_analysis(result: dict) -> dict:
    """Remove placeholder action items sometimes emitted by small local models."""
    actions = result.get("action_items") or []
    cleaned_actions = []

    for item in actions:
        if not isinstance(item, dict):
            continue
        task = str(item.get("task") or "").strip()
        if task.lower().rstrip(".") in _EMPTY_ACTION_VALUES:
            continue
        cleaned_actions.append(
            {
                "task": task,
                "owner": item.get("owner"),
                "deadline": item.get("deadline"),
            }
        )

    result["action_items"] = cleaned_actions
    result["key_points"] = [
        str(point).strip() for point in (result.get("key_points") or []) if str(point).strip()
    ]
    return result


def analyze_transcript(transcript: str) -> dict:
    """Create structured meeting notes using the local Ollama model."""
    if not transcript.strip():
        raise ValueError("Transcript is empty.")

    prompt = f"""
You are a meeting and lecture analysis assistant.
Analyze ONLY the transcript below. Do not invent information that is not present.
Return valid JSON only, with exactly this structure:
{{
  "title": "short descriptive title",
  "summary": "concise summary",
  "key_points": ["point 1", "point 2"],
  "action_items": [
    {{"task": "action", "owner": null, "deadline": null}}
  ]
}}

Rules:
- Preserve the main language of the transcript.
- If there are no explicit tasks, requests, commitments, or follow-up actions, action_items MUST be [].
- Never use placeholder actions such as "None", "N/A", "No action", or similar text.
- Use null when an owner or deadline is not explicitly stated.
- Never infer people, deadlines, decisions, or facts that are not supported by the transcript.

TRANSCRIPT:
{transcript}
""".strip()

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0.1},
    }

    with httpx.Client(timeout=180.0) as client:
        response = client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()

    content = response.json()["message"]["content"]
    return _normalize_analysis(json.loads(content))
