from pathlib import Path
import logging

logger = logging.getLogger(__name__)
_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "Local transcription dependencies are missing. Run "
                "'python -m pip install -r requirements-audio-windows.txt'."
            ) from exc

        # The model downloads on first use and is cached by Hugging Face.
        # CPU int8 is the baseline for broad compatibility with Windows PCs.
        logger.info("Loading local faster-whisper base model (first run may download it)")
        _MODEL = WhisperModel("base", device="cpu", compute_type="int8")
    return _MODEL


def transcribe_local(audio_path):
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    model = _get_model()
    segments, info = model.transcribe(
        str(path),
        language="en",
        vad_filter=True,
        beam_size=5,
    )
    text = " ".join(
        segment.text.strip() for segment in segments if segment.text.strip()
    )
    logger.info(
        "Transcription finished: language=%s, duration=%.1fs",
        getattr(info, "language", "unknown"),
        getattr(info, "duration", 0.0) or 0.0,
    )
    return text.strip()
