from __future__ import annotations

import threading


class LocalTTSError(RuntimeError):
    """Raised when the optional local TTS engine is unavailable."""


class Pyttsx3TTS:
    """Local/offline text-to-speech adapter using pyttsx3."""

    def __init__(self, engine=None):
        if engine is None:
            try:
                import pyttsx3
            except ImportError as exc:
                raise LocalTTSError("pyttsx3 is required for local TTS") from exc
            try:
                engine = pyttsx3.init()
            except Exception as exc:
                raise LocalTTSError(f"local TTS initialization failed: {exc}") from exc
        self.engine = engine
        self._lock = threading.RLock()

    @classmethod
    def create(cls):
        return cls()

    def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        if not text or not text.strip():
            raise ValueError("text is required")
        # pyttsx3 writes through a platform audio driver rather than exposing
        # encoded audio consistently across operating systems. The provider
        # therefore speaks locally and returns an empty payload.
        with self._lock:
            try:
                if voice:
                    for item in self.engine.getProperty("voices") or []:
                        if getattr(item, "id", "") == voice:
                            self.engine.setProperty("voice", voice)
                            break
                self.engine.say(text.strip())
                self.engine.runAndWait()
            except Exception as exc:
                raise LocalTTSError(f"local TTS synthesis failed: {exc}") from exc
        return b""
