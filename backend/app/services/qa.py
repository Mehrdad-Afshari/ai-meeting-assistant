import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2"


def answer_question(transcript: str, question: str) -> str:
    if not transcript.strip():
        raise ValueError("Transcript is empty.")
    if not question.strip():
        raise ValueError("Question is empty.")

    prompt = f"""
You answer questions about one meeting or lecture transcript.
Use ONLY the transcript below as evidence.
If the transcript does not contain enough information, say clearly that the answer is not available in the transcript.
Do not invent facts, people, dates, decisions, or context.
Answer in the same language as the user's question when possible.
Be concise but useful.

TRANSCRIPT:
{transcript}

QUESTION:
{question}
""".strip()

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0.1},
    }

    with httpx.Client(timeout=180.0) as client:
        response = client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()

    return response.json()["message"]["content"].strip()
