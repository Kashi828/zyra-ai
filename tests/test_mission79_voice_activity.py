from core.voice_activity import EnergyVoiceActivityDetector, VoiceActivityConfig
from core.voice_status import VoiceStatusAnnouncer


def pcm(value, count=320):
    return int(value).to_bytes(2, "little", signed=True) * count


def test_vad_detects_speech_then_silence():
    vad = EnergyVoiceActivityDetector(
        VoiceActivityConfig(threshold=0.01, silence_ms=600, min_speech_ms=200)
    )
    a = vad.update(pcm(2000), 100)
    assert not a["speech_started"]
    b = vad.update(pcm(2000), 100)
    assert b["speech_started"]
    assert not b["silence_reached"]

    vad.update(b"", 200)
    out = vad.update(b"", 400)
    assert out["silence_reached"]


def test_vad_reset_clears_state():
    vad = EnergyVoiceActivityDetector()
    vad.update(pcm(3000), 300)
    vad.reset()
    assert vad.active_ms == 0
    assert vad.silent_ms == 0
    assert not vad.started


def test_vad_rejects_bad_frame_duration():
    vad = EnergyVoiceActivityDetector()
    try:
        vad.update(b"", 0)
    except ValueError:
        pass
    else:
        assert False


def test_vad_config_validates_threshold_and_silence():
    for kwargs in [{"threshold":0}, {"threshold":1}, {"silence_ms":50}]:
        try:
            VoiceActivityConfig(**kwargs)
        except ValueError:
            pass
        else:
            assert False


def test_status_announcer_deduplicates():
    spoken=[]
    a=VoiceStatusAnnouncer(spoken.append)
    assert a.announce("t1","running") is not None
    assert a.announce("t1","running") is None
    assert spoken == ["I am working on it."]


def test_status_announcer_supports_approval():
    spoken=[]
    a=VoiceStatusAnnouncer(spoken.append)
    m=a.announce("t1","awaiting_approval")
    assert m.text == "I need your approval before I continue."
    assert spoken[-1] == m.text


def test_status_announcer_can_be_disabled():
    spoken=[]
    a=VoiceStatusAnnouncer(spoken.append, enabled=False)
    assert a.announce("t1","completed") is None
    assert spoken == []
