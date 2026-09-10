from fastapi import HTTPException


def register_pairing_enrollment_routes(
    app, enrollment_service, capability_authorizer, auth_guard, store
):
    def authorize(body: dict):
        decision = auth_guard.authorize(
            body.get("device_id", ""),
            body.get("session_id", ""),
            body.get("auth_key", ""),
        )
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)
        return decision.device_id

    @app.post("/v1/devices/pairing/offer")
    def create_offer(body: dict):
        issuer_id = authorize(body)
        issuer = store.get_device(issuer_id)
        requested = frozenset(body.get("capabilities", []))
        if not requested.issubset(issuer["capabilities"]):
            raise HTTPException(
                status_code=403,
                detail="pairing grant exceeds issuer capabilities",
            )
        offer, code = enrollment_service.create_offer(requested)
        return {
            "offer_id": offer.offer_id,
            "pairing_code": code,
            "expires_at": offer.expires_at,
            "capabilities": sorted(offer.capabilities),
        }

    @app.post("/v1/devices/pairing/enroll")
    def enroll(body: dict):
        try:
            result = enrollment_service.enroll(
                body.get("offer_id", ""),
                body.get("pairing_code", ""),
                body.get("capabilities"),
            )
            store.enroll_device(
                result.device_id,
                result.device_secret,
                result.capabilities,
            )
            capability_authorizer.set_capabilities(
                result.device_id, result.capabilities
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        # The bootstrap secret is returned exactly once to the newly enrolled
        # device. It is never persisted or exposed to the model/tool layer.
        return {
            "device_id": result.device_id,
            "expires_at": result.expires_at,
            "capabilities": sorted(result.capabilities),
            "device_secret": result.device_secret.hex(),
        }
