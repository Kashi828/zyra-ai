from __future__ import annotations

from dataclasses import dataclass
import io
import wave


class LocalVoiceDependencyError(RuntimeError):
    """Raised when an optional local audio/ML dependency is unavailable."""


@dataclass(frozen=True)
class AudioBuffer:
    pcm: bytes
    sample_rate: int
    channels: int
    sample_width: int

    def to_wav(self) -> bytes:
        out = io.BytesIO()
        with wave.open(out, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.sample_width)
            wf.setframerate(self.sample_rate)
            wf.writeframes(self.pcm)
        return out.getvalue()


class WindowsMicrophoneRecorder:
    """
    Local microphone capture using sounddevice when installed.

    The recorder is deliberately one-shot and bounded. Continuous listening,
    wake-word detection, and VAD are separate concerns for later missions.
    """

    def __init__(self, sample_rate: int = 16_000, channels: int = 1, sample_width: int = 2):
        if sample_rate <= 0 or channels <= 0:
            raise ValueError("invalid audio format")
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width

    def record(self, seconds: float) -> AudioBuffer:
        if seconds <= 0 or seconds > 60:
            raise ValueError("recording duration must be > 0 and <= 60 seconds")
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise LocalVoiceDependencyError(
                "sounddevice is required for microphone capture"
            ) from exc

        frames = int(self.sample_rate * seconds)
        dtype = "int16" if self.sample_width == 2 else "int8"
        try:
            recording = sd.rec(
                frames,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=dtype,
                blocking=True,
            )
        except Exception as exc:
            raise RuntimeError(f"microphone capture failed: {exc}") from exc

        pcm = recording.tobytes()
        return AudioBuffer(
            pcm=pcm,
            sample_rate=self.sample_rate,
            channels=self.channels,
            sample_width=self.sample_width,
        )


class FasterWhisperSTT:
    """
    Local/offline STT adapter for faster-whisper.

    The model is injected or loaded by name. No network call is made by this
    adapter itself; model acquisition is the deployment concern.
    """

    def __init__(self, model, *, language: str | None = None):
        if model is None:
            raise ValueError("model is required")
        self.model = model
        self.language = language

    @classmethod
    def from_model_name(
        cls,
        model_name: str = "base",
        *,
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = None,
    ):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise LocalVoiceDependencyError(
                "faster-whisper is required for local STT"
            ) from exc
        model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )
        return cls(model, language=language)

    def transcribe(self, audio: bytes, *, content_type: str = "audio/wav") -> str:
        if not audio:
            raise ValueError("audio is required")
        segments, _info = self.model.transcribe(
            io.BytesIO(audio),
            language=self.language,
            vad_filter=True,
        )
        return " ".join(
            segment.text.strip()
            for segment in segments
            if getattr(segment, "text", "").strip()
        ).strip()


def build_local_stt(model_name: str = "base", *, device: str = "cpu", compute_type: str = "int8", language=None):
    return FasterWhisperSTT.from_model_name(
        model_name,
        device=device,
        compute_type=compute_type,
        language=language,
    )
