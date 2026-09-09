from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Callable, Protocol
import time
import uuid


class SpeechToTextProvider(Protocol):
    def transcribe(self, audio: bytes, *, content_type: str = "audio/wav") -> str:
        ...


class TextToSpeechProvider(Protocol):
    def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        ...


class VoiceError(Exception):
    """Base class for safe voice pipeline errors."""


@dataclass(frozen=True)
class VoiceTranscript:
    text: str
    provider: str = "text"
    language: str | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class VoiceReply:
    text: str
    task_id: str | None = None
    audio: bytes | None = None
    audio_content_type: str = "audio/wav"
    provider: str = "none"


@dataclass
class VoiceSession:
    session_id: str
    device_id: str
    created_at: float
    last_activity: float
    active: bool = True
    turns: int = 0
    metadata: dict = field(default_factory=dict)


class VoiceGateway:
    """
    Provider-neutral voice orchestration boundary.

    Audio recognition and synthesis are deliberately injected. This keeps the
    secure command path independent from any particular STT/TTS engine and
    makes local/offline providers possible without changing API contracts.
    """

    def __init__(
        self,
        *,
        submit_goal: Callable[[str, dict | None], str],
        stt: SpeechToTextProvider | None = None,
        tts: TextToSpeechProvider | None = None,
        max_text_chars: int = 4000,
    ):
        self.submit_goal = submit_goal
        self.stt = stt
        self.tts = tts
        self.max_text_chars = max_text_chars
        self._sessions: dict[str, VoiceSession] = {}
        self._lock = RLock()

    def start_session(self, device_id: str, metadata: dict | None = None) -> VoiceSession:
        if not device_id:
            raise ValueError("device_id is required")
        now = time.time()
        session = VoiceSession(
            session_id=uuid.uuid4().hex,
            device_id=device_id,
            created_at=now,
            last_activity=now,
            metadata=dict(metadata or {}),
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def end_session(self, session_id: str, device_id: str) -> None:
        with self._lock:
            session = self._require_session(session_id, device_id)
            session.active = False
            session.last_activity = time.time()

    def get_session(self, session_id: str, device_id: str) -> VoiceSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session or session.device_id != device_id or not session.active:
                return None
            return VoiceSession(**vars(session))

    def transcribe(self, audio: bytes, *, content_type: str = "audio/wav") -> VoiceTranscript:
        if self.stt is None:
            raise VoiceError("speech-to-text provider is not configured")
        if not audio:
            raise VoiceError("audio is required")
        text = self.stt.transcribe(audio, content_type=content_type)
        return self._normalize_transcript(text, provider=self.stt.__class__.__name__)

    def handle_transcript(
        self,
        session_id: str,
        device_id: str,
        transcript: VoiceTranscript | str,
        *,
        context: dict | None = None,
        synthesize: bool = False,
        voice: str | None = None,
    ) -> VoiceReply:
        with self._lock:
            session = self._require_session(session_id, device_id)
            session.last_activity = time.time()
            session.turns += 1

        normalized = (
            transcript
            if isinstance(transcript, VoiceTranscript)
            else self._normalize_transcript(transcript)
        )
        merged_context = {
            "source": "voice",
            "voice_session_id": session_id,
            "transcript_provider": normalized.provider,
        }
        if normalized.language:
            merged_context["language"] = normalized.language
        if normalized.confidence is not None:
            merged_context["confidence"] = normalized.confidence
        if context:
            merged_context["voice_context"] = dict(context)

        task_id = self.submit_goal(normalized.text, merged_context)
        reply_text = "I started that task."
        audio = None
        provider = "none"
        if synthesize:
            if self.tts is None:
                raise VoiceError("text-to-speech provider is not configured")
            audio = self.tts.synthesize(reply_text, voice=voice)
            provider = self.tts.__class__.__name__
        return VoiceReply(
            text=reply_text,
            task_id=task_id,
            audio=audio,
            provider=provider,
        )

    def _require_session(self, session_id: str, device_id: str) -> VoiceSession:
        if not session_id:
            raise VoiceError("voice_session_id is required")
        session = self._sessions.get(session_id)
        if session is None:
            raise VoiceError("voice session not found")
        if session.device_id != device_id:
            raise VoiceError("voice session belongs to another device")
        if not session.active:
            raise VoiceError("voice session is inactive")
        return session

    def _normalize_transcript(
        self,
        text: str,
        *,
        provider: str = "text",
    ) -> VoiceTranscript:
        text = str(text or "").strip()
        if not text:
            raise VoiceError("transcript is required")
        if len(text) > self.max_text_chars:
            raise VoiceError("transcript is too long")
        return VoiceTranscript(text=text, provider=provider)
