from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class VoiceActivityConfig:
    threshold: float = 0.02
    silence_ms: int = 1200
    min_speech_ms: int = 250

    def __post_init__(self):
        if not 0 < self.threshold < 1:
            raise ValueError("threshold must be between 0 and 1")
        if self.silence_ms < 100:
            raise ValueError("silence_ms must be >= 100")
        if self.min_speech_ms < 0:
            raise ValueError("min_speech_ms must be >= 0")


class EnergyVoiceActivityDetector:
    """Small dependency-free RMS VAD for PCM16 mono frames."""

    def __init__(self, config: VoiceActivityConfig | None = None):
        self.config = config or VoiceActivityConfig()
        self.active_ms = 0
        self.silent_ms = 0
        self.started = False

    def reset(self) -> None:
        self.active_ms = 0
        self.silent_ms = 0
        self.started = False

    @staticmethod
    def rms(pcm16: bytes) -> float:
        if not pcm16:
            return 0.0
        if len(pcm16) % 2:
            pcm16 = pcm16[:-1]
        if not pcm16:
            return 0.0
        samples = [
            int.from_bytes(pcm16[i:i+2], "little", signed=True)
            for i in range(0, len(pcm16), 2)
        ]
        return sqrt(sum((sample / 32768.0) ** 2 for sample in samples) / len(samples))

    def update(self, pcm16: bytes, frame_ms: int) -> dict:
        if frame_ms <= 0:
            raise ValueError("frame_ms must be > 0")
        energy = self.rms(pcm16)
        speaking = energy >= self.config.threshold

        if speaking:
            self.active_ms += frame_ms
            self.silent_ms = 0
            self.started = self.active_ms >= self.config.min_speech_ms
        else:
            self.silent_ms += frame_ms

        silence_reached = (
            self.started and self.silent_ms >= self.config.silence_ms
        )
        return {
            "speaking": speaking,
            "speech_started": self.started,
            "silence_ms": self.silent_ms,
            "active_ms": self.active_ms,
            "energy": energy,
            "silence_reached": silence_reached,
        }
