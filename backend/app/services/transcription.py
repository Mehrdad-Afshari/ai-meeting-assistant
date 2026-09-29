from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

# "small" remains a good quality/speed compromise for multilingual meetings.
MODEL_SIZE = "small"


@lru_cache(maxsize=1)
def get_whisper_model() -> WhisperModel:
    """Load Whisper once per backend process and reuse it across requests."""
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


def warmup_whisper() -> None:
    """Initialize the model without running transcription."""
    get_whisper_model()


def transcribe_audio(file_path: Path, language: str | None = None) -> dict:
    model = get_whisper_model()
    segments, info = model.transcribe(
        str(file_path),
        language=language,
        # Greedy decoding is substantially faster than beam_size=5 on CPU and
        # is sufficient for the interactive local-first MVP.
        beam_size=1,
        best_of=1,
        temperature=0.0,
        vad_filter=True,
        condition_on_previous_text=False,
    )

    transcript_segments = []
    text_parts = []

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        text_parts.append(text)
        transcript_segments.append(
            {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text,
            }
        )

    return {
        "text": " ".join(text_parts).strip(),
        "language": info.language,
        "language_probability": round(info.language_probability, 4),
        "duration": round(info.duration, 2),
        "segments": transcript_segments,
        "model": MODEL_SIZE,
    }
