from fastapi import HTTPException


def register_session_activation_routes(app, bridge, replay_guard, verify_proof):
    """Wire the enrollment-secret -> session activation endpoint.

    `verify_proof` must match EnrollmentSessionBridge.activate's expected
    signature: verify_proof(device_id, nonce, timestamp, proof) -> bool.
    """

    @app.post("/v1/devices/session/activate")
    def activate(body: dict):
        device_id = str(body.get("device_id", ""))
        nonce = str(body.get("nonce", ""))
        timestamp = int(body.get("timestamp", 0))
        proof = str(body.get("proof", ""))
        if not replay_guard.accept(device_id, nonce, timestamp):
            raise HTTPException(status_code=401, detail="replayed or stale activation")
        try:
            result = bridge.activate(
                device_id,
                nonce,
                timestamp,
                proof,
                verify_proof,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return {
            "accepted": True,
            "session_id": result.session_id,
            "device_id": result.device_id,
            "expires_at": result.expires_at,
        }
