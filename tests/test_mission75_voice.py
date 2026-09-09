from fastapi.testclient import TestClient

from api.app_factory import create_app
from core.voice import VoiceError, VoiceGateway


class FakeStore:
    pass


def _enroll_and_session(tmp_path):
    from security.persistent_device_store import PersistentDeviceStore
    from security.persistent_enrollment import PersistentEnrollment
    db = tmp_path / "voice.sqlite3"
    store = PersistentDeviceStore(db)
    device, _ = PersistentEnrollment(store).create_device({"pc.apps"})
    store.issue_session(device, "sess1", 60)
    return db, device


def test_voice_session_and_transcript_start_task(tmp_path):
    db, device = _enroll_and_session(tmp_path)
    app = create_app(db)
    tasks = []

    app.state.voice_gateway.submit_goal = lambda goal, ctx: tasks.append((goal, ctx)) or "task123"

    client = TestClient(app)
    body = {"device_id": device, "session_id": "sess1"}
    r = client.post("/v1/voice/session/start", json=body)
    assert r.status_code == 200
    vs = r.json()["voice_session_id"]

    r = client.post("/v1/voice/transcript", json={
        **body,
        "voice_session_id": vs,
        "text": "open my browser",
        "provider": "test",
    })
    assert r.status_code == 200
    assert r.json()["task_id"] == "task123"
    assert tasks[0][0] == "open my browser"
    assert tasks[0][1]["source"] == "voice"


def test_voice_route_requires_authenticated_session(tmp_path):
    db, device = _enroll_and_session(tmp_path)
    app = create_app(db)
    client = TestClient(app)
    r = client.post("/v1/voice/session/start", json={
        "device_id": device, "session_id": "wrong"
    })
    assert r.status_code == 401


def test_voice_session_is_device_bound():
    gateway = VoiceGateway(submit_goal=lambda goal, ctx: "t")
    a = gateway.start_session("a")
    try:
        gateway.handle_transcript(a.session_id, "b", "hello")
    except VoiceError as exc:
        assert "another device" in str(exc)
    else:
        assert False


def test_voice_rejects_empty_and_oversized_text():
    gateway = VoiceGateway(submit_goal=lambda goal, ctx: "t", max_text_chars=4)
    s = gateway.start_session("d")
    for value in ["", "12345"]:
        try:
            gateway.handle_transcript(s.session_id, "d", value)
        except VoiceError:
            pass
        else:
            assert False


def test_voice_provider_interfaces_are_injected():
    class STT:
        def transcribe(self, audio, *, content_type="audio/wav"):
            return "hello zyra"

    class TTS:
        def synthesize(self, text, *, voice=None):
            return b"audio"

    gateway = VoiceGateway(
        submit_goal=lambda goal, ctx: "t",
        stt=STT(),
        tts=TTS(),
    )
    assert gateway.transcribe(b"wav").text == "hello zyra"
    s = gateway.start_session("d")
    reply = gateway.handle_transcript(s.session_id, "d", "hello", synthesize=True)
    assert reply.audio == b"audio"
    assert reply.provider == "TTS"
