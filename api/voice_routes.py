from fastapi import HTTPException, Request
import time

from core.voice import VoiceError, VoiceTranscript, VoiceGateway


def _authorize(auth_guard, body: dict) -> str:
    device_id = str(body.get("device_id", ""))
    session_id = str(body.get("session_id", ""))
    decision = auth_guard.authorize(
        device_id, session_id, device_id or "anonymous"
    )
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.reason)
    return device_id


def register_voice_routes(app, security_context, voice_gateway: VoiceGateway):
    @app.post("/v1/voice/desktop/bootstrap")
    def desktop_bootstrap(request: Request):
        # Desktop bootstrap is intentionally loopback-only and opt-in.
        host = request.client.host if request.client else ""
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise HTTPException(status_code=403, detail="desktop bootstrap is local-only")

        from security.persistent_enrollment import PersistentEnrollment
        enrollment = PersistentEnrollment(security_context.store)
        device_id, _secret = enrollment.create_device({"pc.voice"})
        session = security_context.sessions.create(device_id)
        return {
            "ok": True,
            "device_id": device_id,
            "session_id": session["session_id"],
            "refresh_token": session["refresh_token"],
            "expires_at": session.get("expires_at", time.time() + 900),
            "capabilities": ["pc.voice"],
        }

    @app.get("/v1/voice/capabilities")
    def voice_capabilities():
        return {
            "ok": True,
            "stt": "configured" if voice_gateway.stt is not None else "unconfigured",
            "tts": "configured" if voice_gateway.tts is not None else "unconfigured",
        }
    @app.post("/v1/voice/session/start")
    def start_voice_session(body: dict):
        device_id = _authorize(security_context.api_auth, body)
        try:
            session = voice_gateway.start_session(
                device_id, metadata=body.get("metadata") or {}
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {
            "ok": True,
            "voice_session_id": session.session_id,
            "device_id": device_id,
            "created_at": session.created_at,
        }

    @app.post("/v1/voice/session/end")
    def end_voice_session(body: dict):
        device_id = _authorize(security_context.api_auth, body)
        try:
            voice_gateway.end_session(str(body.get("voice_session_id", "")), device_id)
        except (VoiceError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return {"ok": True, "ended": True}

    @app.post("/v1/voice/transcript")
    def submit_voice_transcript(body: dict):
        device_id = _authorize(security_context.api_auth, body)
        try:
            reply = voice_gateway.handle_transcript(
                str(body.get("voice_session_id", "")),
                device_id,
                VoiceTranscript(
                    text=str(body.get("text", "")),
                    provider=str(body.get("provider", "text")),
                    language=body.get("language"),
                    confidence=body.get("confidence"),
                ),
                context=body.get("context") or {},
                synthesize=bool(body.get("synthesize", False)),
                voice=body.get("voice"),
            )
        except VoiceError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return {
            "ok": True,
            "task_id": reply.task_id,
            "text": reply.text,
            "audio_content_type": reply.audio_content_type,
            "audio_base64": (
                __import__("base64").b64encode(reply.audio).decode("ascii")
                if reply.audio is not None else None
            ),
            "tts_provider": reply.provider,
        }

    @app.post("/v1/voice/transcribe")
    async def transcribe_voice(request: Request):
        # Multipart/audio upload is intentionally kept behind the authenticated
        # session fields in headers to avoid exposing unauthenticated STT.
        device_id = request.headers.get("x-zyra-device-id", "")
        session_id = request.headers.get("authorization", "")
        session_id = session_id[7:] if session_id.startswith("Bearer ") else ""
        decision = security_context.api_auth.authorize(
            device_id, session_id, device_id or "anonymous"
        )
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)

        audio = await request.body()
        content_type = request.headers.get("content-type", "audio/wav")
        try:
            result = voice_gateway.transcribe(audio, content_type=content_type)
        except VoiceError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return {
            "ok": True,
            "text": result.text,
            "provider": result.provider,
            "language": result.language,
            "confidence": result.confidence,
        }

    @app.post("/v1/voice/speak")
    def speak_voice(body: dict):
        device_id = _authorize(security_context.api_auth, body)
        text = str(body.get("text", "")).strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")
        try:
            session_id = str(body.get("voice_session_id", ""))
            # Keep the voice session device-bound even for synthesis-only calls.
            session = voice_gateway.get_session(session_id, device_id)
            if session is None:
                raise VoiceError("voice session not found")
            if voice_gateway.tts is None:
                raise VoiceError("text-to-speech provider is not configured")
            audio = voice_gateway.tts.synthesize(text, voice=body.get("voice"))
        except VoiceError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return {
            "ok": True,
            "audio_content_type": "audio/wav",
            "audio_base64": __import__("base64").b64encode(audio).decode("ascii") if audio else None,
            "spoken_locally": True,
        }

    return voice_gateway
