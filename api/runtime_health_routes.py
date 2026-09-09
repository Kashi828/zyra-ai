from __future__ import annotations

from fastapi import APIRouter

from desktop.runtime_health import RuntimeHealthService


def register_runtime_health_routes(app, health: RuntimeHealthService | None = None):
    service = health or RuntimeHealthService()
    router = APIRouter(prefix="/v1/runtime", tags=["runtime"])

    @router.get("/health")
    def runtime_health():
        voice = getattr(app.state, "voice_capabilities", {}).get("tts", "unconfigured")
        return service.read(voice=voice)

    app.include_router(router)
    app.state.runtime_health = service
    return router
