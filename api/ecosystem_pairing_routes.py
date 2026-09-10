from fastapi import HTTPException

from security.ecosystem_pairing import EcosystemPairingService


def register_ecosystem_pairing_routes(app, pairing_service=None):
    service = pairing_service or EcosystemPairingService()
    app.state.ecosystem_pairing = service

    @app.post("/v1/ecosystem/pairing/start")
    def start_pairing(body: dict):
        device_id = str(body.get("device_id", ""))
        device_type = str(body.get("device_type", ""))
        endpoint = str(body.get("endpoint", ""))
        if not device_id or not device_type:
            raise HTTPException(status_code=400, detail="device_id and device_type are required")
        request, code = service.create(device_id, device_type, endpoint)
        # The code is returned only to the authenticated local UI caller.
        return {
            "pairing_id": request.pairing_id,
            "device_id": request.device_id,
            "device_type": request.device_type,
            "expires_at": request.expires_at,
            "pairing_code": code,
        }

    @app.post("/v1/ecosystem/pairing/approve")
    def approve_pairing(body: dict):
        pairing_id = str(body.get("pairing_id", ""))
        code = str(body.get("pairing_code", ""))
        if not pairing_id or len(code) != 6 or not code.isdigit():
            raise HTTPException(status_code=400, detail="pairing_id and six-digit pairing_code are required")
        try:
            request = service.approve(pairing_id, code)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return {
            "ok": True,
            "pairing_id": request.pairing_id,
            "device_id": request.device_id,
            "device_type": request.device_type,
            "endpoint": request.endpoint,
            "status": "approved",
        }

    return service
