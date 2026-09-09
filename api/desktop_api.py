def register_desktop_routes(app, agent_runtime):
    @app.post("/v1/agent/stop")
    def stop_agent():
        stopped = False
        stopper = getattr(agent_runtime, "stop", None)
        if callable(stopper):
            stopper()
            stopped = True
        return {"ok": True, "stopped": stopped}
