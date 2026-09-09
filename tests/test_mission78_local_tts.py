import pytest

from services.local_tts import LocalTTSError, Pyttsx3TTS


def test_local_tts_uses_injected_engine():
    spoken = []

    class Voice:
        id = "voice-1"

    class Engine:
        def getProperty(self, name):
            return [Voice()] if name == "voices" else None
        def setProperty(self, name, value):
            spoken.append(("set", name, value))
        def say(self, text):
            spoken.append(("say", text))
        def runAndWait(self):
            spoken.append(("run",))

    engine = Engine()
    tts = Pyttsx3TTS(engine)
    assert tts.synthesize("hello", voice="voice-1") == b""
    assert ("say", "hello") in spoken


def test_local_tts_rejects_empty_text():
    class Engine: pass
    tts = Pyttsx3TTS(Engine())
    with pytest.raises(ValueError):
        tts.synthesize("")


def test_local_tts_missing_dependency(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "pyttsx3":
            raise ImportError("blocked in test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(LocalTTSError):
        Pyttsx3TTS()
