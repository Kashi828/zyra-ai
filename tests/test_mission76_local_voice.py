import io
import wave

import pytest

from services.local_voice import (
    AudioBuffer,
    FasterWhisperSTT,
    LocalVoiceDependencyError,
    WindowsMicrophoneRecorder,
)


def test_audio_buffer_writes_valid_wav():
    data = AudioBuffer(b"\x00\x01" * 100, 16000, 1, 2).to_wav()
    with wave.open(io.BytesIO(data), "rb") as wf:
        assert wf.getframerate() == 16000
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getnframes() == 100


def test_recorder_rejects_invalid_duration():
    recorder = WindowsMicrophoneRecorder()
    for seconds in [0, -1, 61]:
        with pytest.raises(ValueError):
            recorder.record(seconds)


def test_recorder_reports_missing_optional_dependency(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "sounddevice":
            raise ImportError("blocked in test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(LocalVoiceDependencyError):
        WindowsMicrophoneRecorder().record(0.1)


def test_faster_whisper_accepts_injected_model():
    class Segment:
        def __init__(self, text):
            self.text = text

    class FakeModel:
        def transcribe(self, audio, language=None, vad_filter=True):
            assert language == "en"
            assert vad_filter is True
            assert audio.read(4)  # WAV bytes are present
            return iter([Segment(" hello "), Segment("world")]), object()

    stt = FasterWhisperSTT(FakeModel(), language="en")
    assert stt.transcribe(b"RIFFfake") == "hello world"


def test_faster_whisper_model_factory_missing_dependency(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "faster_whisper":
            raise ImportError("blocked in test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(LocalVoiceDependencyError):
        FasterWhisperSTT.from_model_name()
