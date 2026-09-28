from __future__ import annotations

import socket

from fastapi import HTTPException, Request

LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
# Grant names a paired phone may hold; anything else is rejected outright.
PHONE_CAPABILITIES = ("pc.apps", "pc.files", "pc.web")


def lan_addresses() -> list[str]:
    """Best-effort private IPv4 addresses of this PC, for showing in the pairing UI."""
    found: list[str] = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and ip not in found:
                found.append(ip)
    except OSError:
        pass
    return found


def register_desktop_pairing_routes(app, enrollment_service, port: int = 8000):
    """Lets the desktop app itself mint a one-time phone pairing offer.

    Only callable from this PC (loopback peer). Phones never reach this route:
    they redeem the offer at /v1/devices/pairing/enroll.
    """

    @app.post("/v1/desktop/pairing/offer")
    def desktop_pairing_offer(request: Request, body: dict | None = None):
        peer = request.client.host if request.client else ""
        if peer not in LOOPBACK_HOSTS:
            raise HTTPException(status_code=403, detail="pairing offers can only be created on this PC")
        requested = (body or {}).get("capabilities")
        if requested is None:
            capabilities = set(PHONE_CAPABILITIES)
        else:
            if not isinstance(requested, list) or not set(requested).issubset(PHONE_CAPABILITIES):
                raise HTTPException(status_code=400, detail="unsupported capability requested")
            capabilities = set(requested)
        offer, code = enrollment_service.create_offer(capabilities)
        return {
            "offer_id": offer.offer_id,
            "pairing_code": code,
            "expires_at": offer.expires_at,
            "capabilities": sorted(offer.capabilities),
            "addresses": [f"http://{ip}:{port}" for ip in lan_addresses()],
        }
