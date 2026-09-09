def register_pairing_enrollment_routes(app, enrollment_service, capability_authorizer):
    @app.post("/v1/devices/pairing/enroll")
    def enroll(body: dict):
        offer_id = body.get("offer_id", "")
        requested = body.get("capabilities", [])
        result = enrollment_service.enroll(offer_id, requested)
        capability_authorizer.set_capabilities(result.device_id, result.capabilities)
        return {
            "device_id": result.device_id,
            "expires_at": result.expires_at,
            "capabilities": sorted(result.capabilities),
            "device_secret": result.device_secret.hex(),
        }
