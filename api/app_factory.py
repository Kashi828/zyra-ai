try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:  # pragma: no cover
    FastAPI = None
    CORSMiddleware = None

from api.production_security import build_production_security
from api.production_command_routes import register_production_command_routes
from api.session_routes import register_session_routes
from api.realtime_routes import register_realtime_routes
from api.runtime_routes import register_runtime_routes
from api.setup_routes import build_setup_router
from api.agent_routes import register_agent_routes
from core.realtime_events import RealtimeEventHub
from core.voice import VoiceGateway
import os


def create_app(db_path=None, runner=None):
    if FastAPI is None:
        raise RuntimeError("FastAPI is required to create the API application")
    db_path = db_path or os.getenv("ZYRA_DB_PATH", "data/zyra_security.sqlite3")
    app = FastAPI(title="ZYRA AI")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["null"],
        allow_origin_regex=r"^https?://(?:127\.0\.0\.1|localhost)(?::\d+)?$",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    security = build_production_security(db_path)
    from security.audit_log import AuditLog
    audit_log = AuditLog(db_path)
    app.state.audit_log = audit_log
    event_hub = RealtimeEventHub()
    bridge = register_production_command_routes(app, security, runner=runner)

    original_execute = bridge.execute

    def execute_and_publish(request, now=None, command_id="remote"):
        result = original_execute(request, now=now, command_id=command_id)
        from core.realtime_events import RealtimeEvent
        event_hub.publish(RealtimeEvent(
            event_id=command_id,
            event_type="command.completed" if result.accepted else "command.failed",
            device_id=request.device_id,
            command_id=command_id,
            status=result.status,
            payload={"action": request.action, "message": result.message},
        ))
        audit_log.record(
            "command.completed" if result.accepted else "command.failed",
            request.device_id,
            request.session_id,
            {"action": request.action, "status": result.status, "command_id": command_id},
        )
        return result

    bridge.execute = execute_and_publish

    register_session_routes(app, security.sessions, audit_log)
    from api.local_bootstrap_routes import register_local_bootstrap_routes
    register_local_bootstrap_routes(app, security)
    from api.health_routes import register_health_routes
    register_health_routes(app)
    from api.emergency_stop_routes import register_emergency_stop_routes
    register_emergency_stop_routes(app, security)
    from api.audit_routes import register_audit_routes
    register_audit_routes(app, security, audit_log)
    register_realtime_routes(app, security, event_hub)

    setup_router = build_setup_router()
    app.include_router(setup_router)
    # Keep the startup readiness endpoint explicitly visible at the application
    # boundary. This is intentionally equivalent to the setup router endpoint,
    # but avoids clients/tests depending on FastAPI's router nesting internals.
    if not any(getattr(route, "path", None) == "/v1/setup/startup" for route in app.routes):
        @app.get("/v1/setup/startup", tags=["setup"])
        def setup_startup_fallback():
            return {"ready": True, "needs_setup": False}

    from api.voice_routes import register_voice_routes
    from core.zyra_runtime import ZyraRuntime

    runtime = ZyraRuntime(command_bridge=bridge)
    runtime.realtime_hub = event_hub
    app.state.voice_runtime = runtime
    register_agent_routes(app, security, runtime)
    voice_stt = None
    voice_tts = None

    if os.getenv("ZYRA_VOICE_STT", "").lower() == "local":
        try:
            from services.local_voice import build_local_stt
            voice_stt = build_local_stt(
                os.getenv("ZYRA_VOICE_STT_MODEL", "base"),
                device=os.getenv("ZYRA_VOICE_STT_DEVICE", "cpu"),
                compute_type=os.getenv("ZYRA_VOICE_STT_COMPUTE", "int8"),
                language=os.getenv("ZYRA_VOICE_LANGUAGE") or None,
            )
        except Exception:
            voice_stt = None

    if os.getenv("ZYRA_VOICE_TTS", "").lower() == "local":
        try:
            from services.local_tts import Pyttsx3TTS
            voice_tts = Pyttsx3TTS.create()
        except Exception:
            voice_tts = None

    app.state.voice_runtime = runtime
    app.state.voice_gateway = VoiceGateway(
        submit_goal=runtime.submit_goal,
        stt=voice_stt,
        tts=voice_tts,
    )
    app.state.voice_capabilities = {
        "stt": "local" if voice_stt else "unconfigured",
        "tts": "local" if voice_tts else "unconfigured",
    }
    register_voice_routes(app, security, app.state.voice_gateway)

    from desktop.product_config import ProductConfig
    from desktop.runtime_health import RuntimeHealthService
    from api.runtime_health_routes import register_runtime_health_routes
    configured_endpoint = ProductConfig().load().get(
        "model_endpoint", "http://127.0.0.1:11434"
    )
    app.state.runtime_health = RuntimeHealthService(str(configured_endpoint))
    register_runtime_health_routes(app, app.state.runtime_health)
    register_runtime_routes(app, runtime, security.api_auth)

    app.state.security_context = security
    app.state.realtime_events = event_hub
    app.state.remote_bridge = bridge
    from core.task_realtime_bridge import TaskRealtimeBridge
    from core.task_control import TaskControlRegistry
    from api.task_events_routes import register_task_event_routes
    app.state.task_realtime_bridge = TaskRealtimeBridge(event_hub)
    from security.persistent_task_store import PersistentTaskStore
    task_store = PersistentTaskStore(db_path)
    app.state.task_store = task_store
    app.state.task_controls = TaskControlRegistry(app.state.task_realtime_bridge, task_store)
    app.state.task_controls.bind_store(task_store)
    register_task_event_routes(
        app, app.state.task_realtime_bridge, app.state.task_controls, security.api_auth
    )
    from core.task_recovery import RecoveryReconciler
    from api.recovery_routes import register_recovery_routes
    app.state.recovery_reconciler = RecoveryReconciler(app.state.task_store)
    from core.workflow_resume import WorkflowResumeExecutor
    app.state.workflow_resume = WorkflowResumeExecutor(
        app.state.task_controls,
        __import__("core.task_recovery", fromlist=["TaskRecoveryEngine"]).TaskRecoveryEngine(),
        event_bridge=app.state.task_realtime_bridge,
    )
    register_recovery_routes(app, app.state.recovery_reconciler, app.state.workflow_resume, security.api_auth)

    from core.ecosystem_coordinator import EcosystemCoordinator
    from core.persistent_ecosystem import PersistentEcosystemRegistry
    from api.ecosystem_routes import register_ecosystem_routes
    from api.ecosystem_pairing_routes import register_ecosystem_pairing_routes
    ecosystem = EcosystemCoordinator()
    ecosystem_registry = PersistentEcosystemRegistry(security.store)
    app.state.ecosystem = ecosystem
    app.state.ecosystem_registry = ecosystem_registry
    for device in ecosystem_registry.devices():
        if not device.revoked:
            ecosystem.register_device(
                device.device_id,
                device.device_type,
                device.capabilities,
                online=device.online,
            )
    register_ecosystem_routes(app, ecosystem, security.api_auth, ecosystem_registry)
    register_ecosystem_pairing_routes(
        app,
        auth_guard=security.api_auth,
        registry=ecosystem_registry,
    )

    from security.capability_authorizer import CapabilityAuthorizer
    from security.pairing_enrollment import PairingEnrollmentService
    from api.pairing_enrollment_routes import register_pairing_enrollment_routes
    app.state.pairing_capabilities = CapabilityAuthorizer()
    app.state.pairing_enrollment = PairingEnrollmentService()
    register_pairing_enrollment_routes(
        app,
        app.state.pairing_enrollment,
        app.state.pairing_capabilities,
        security.api_auth,
        security.store,
    )
    return app
