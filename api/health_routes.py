from api.health import bootstrap_environment
from desktop.install_check import run_install_checks


def register_health_routes(app):
    @app.get("/health")
    def health():
        report = bootstrap_environment()
        return {
            "ok": report["ready"],
            "service": "zyra-ai",
            "version": "0.1.0",
        }

    @app.get("/v1/system/diagnostics")
    def diagnostics():
        return {"ok": True, **bootstrap_environment()}

    @app.get("/v1/system/setup-check")
    def setup_check():
        return run_install_checks()
