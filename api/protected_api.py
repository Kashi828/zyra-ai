def protected_request_error(decision):
    """Return a standardized FastAPI response tuple for failed authorization."""
    headers = {}
    if decision.status_code == 429:
        headers["Retry-After"] = "1"
    return {
        "ok": False,
        "error": {
            "code": decision.status_code,
            "message": decision.reason,
        },
        "_status_code": decision.status_code,
        "_headers": headers,
    }


def authorize_request(auth_guard, body):
    device_id = str(body.get("device_id", ""))
    session_id = str(body.get("session_id", ""))
    key = str(body.get("client_key") or device_id or "anonymous")
    return auth_guard.authorize(device_id, session_id, key)
