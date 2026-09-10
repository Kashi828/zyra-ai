from urllib.parse import urlparse

from fastapi import HTTPException

from security.ecosystem_pairing import EcosystemPairingService


def _validate_endpoint(endpoint):
    value = str(endpoint or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="invalid pairing endpoint")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HTTPException(status_code=400, detail="pairing endpoint must not contain credentials, query, or fragment")
    host = parsed.hostname.lower()
    private_hosts = {"localhost", "127.0.0.1", "::1"}
    private_prefixes = (
        "10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.",
        "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
        "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
    )
    if parsed.scheme == "http" and host not in private_hosts and not host.startswith(private_prefixes):
        raise HTTPException(status_code=400, detail="non-private pairing endpoints require HTTPS")
    return value.rstrip("/")


def register_ecosystem_pairing_routes(app, pairing_service=None, auth_guard=None, registry=None):
    service = pairing_service or EcosystemPairingService()
    app.state.ecosystem_pairing = service

    def authorize(body):
        if auth_guard is None:
            raise HTTPException(status_code=503, detail="ecosystem authentication is unavailable")
        device_id = str(body.get("device_id", ""))
        session_id = str(body.get("session_id", ""))
        if not device_id or not session_id:
            raise HTTPException(status_code=401, detail="device_id and session_id are required")
        decision = auth_guard.authorize(device_id, session_id, session_id)
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)
        return device_id

    @app.post("/v1/ecosystem/pairing/start")
    def start_pairing(body: dict):
        authorize(body)
        device_id = str(body.get("target_device_id", body.get("device_id", "")))
        device_type = str(body.get("device_type", ""))
        endpoint = _validate_endpoint(body.get("endpoint", ""))
        if not device_id or not device_type:
            raise HTTPException(status_code=400, detail="target_device_id and device_type are required")
        request, code = service.create(device_id, device_type, endpoint)
        return {
            "pairing_id": request.pairing_id,
            "device_id": request.device_id,
            "device_type": request.device_type,
            "expires_at": request.expires_at,
            "pairing_code": code,
        }

    @app.post("/v1/ecosystem/pairing/approve")
    def approve_pairing(body: dict):
        authorize(body)
        pairing_id = str(body.get("pairing_id", ""))
        code = str(body.get("pairing_code", ""))
        if not pairing_id or len(code) != 6 or not code.isdigit():
            raise HTTPException(status_code=400, detail="pairing_id and six-digit pairing_code are required")
        try:
            request = service.approve(pairing_id, code)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        if registry is not None:
            try:
                registry.register(
                    request.device_id,
                    request.device_type,
                    request.device_id,
                    online=False,
                    endpoint=request.endpoint,
                )
            except (PermissionError, ValueError) as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
        return {
            "ok": True,
            "pairing_id": request.pairing_id,
            "device_id": request.device_id,
            "device_type": request.device_type,
            "endpoint_bound": bool(request.endpoint),
            "status": "approved",
        }

    return service
