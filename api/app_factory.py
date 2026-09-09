try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover
    FastAPI = None

from api.production_security import build_production_security
from api.production_command_routes import register_production_command_routes
from api.session_routes import register_session_routes
from api.realtime_routes import register_realtime_routes
from core.realtime_events import RealtimeEventHub
from core.voice import VoiceGateway
import os


def create_app(db_path="data/zyra_security.sqlite3", runner=None):
    if FastAPI is None:
        raise RuntimeError("FastAPI is required to create the API application")
    app = FastAPI(title="ZYRA AI")
    security = build_production_security(db_path)
    event_hub = RealtimeEventHub()
    bridge = register_production_command_routes(app, security, runner=runner)

    # Publish command results into the unified realtime stream.
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
        return result

    bridge.execute = execute_and_publish

    register_session_routes(app, security.sessions)
    from api.health_routes import register_health_routes
    register_health_routes(app)
    register_realtime_routes(app, security, event_hub)
    from api.voice_routes import register_voice_routes
    from core.zyra_runtime import ZyraRuntime

    # Voice is a secure input adapter into the same goal pipeline. The default
    # submit function is intentionally provider-neutral and can be replaced by
    # the concrete workflow runtime when voice execution is enabled.
    runtime = ZyraRuntime()
    app.state.voice_runtime = runtime
    voice_stt = None
    voice_tts = None

    # Local voice is opt-in so a fresh checkout never downloads models or
    # initializes audio devices unexpectedly.
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
    from desktop.runtime_health import RuntimeHealthService
    from api.runtime_health_routes import register_runtime_health_routes
    app.state.runtime_health = RuntimeHealthService()
    register_runtime_health_routes(app, app.state.runtime_health)
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
    app.state.task_controls = TaskControlRegistry(
        app.state.task_realtime_bridge, task_store
    )
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
    return app
