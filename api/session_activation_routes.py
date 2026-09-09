def register_session_activation_routes(app, bridge, replay_guard, issue_session):
    @app.post("/v1/devices/session/activate")
    def activate(body: dict):
        device_id = body.get("device_id", "")
        nonce = body.get("nonce", "")
        timestamp = int(body.get("timestamp", 0))
        proof = body.get("proof", "")
        if not replay_guard.accept(device_id, nonce, timestamp):
            return {"accepted": False, "message": "replayed or stale activation"}
        result = bridge.activate(
            device_id=device_id,
            nonce=nonce,
            timestamp=timestamp,
            proof=proof,
            issue_session=issue_session,
        )
        return {
            "accepted": True,
            "session_id": result.session_id,
            "device_id": result.device_id,
            "expires_at": result.expires_at,
        }
