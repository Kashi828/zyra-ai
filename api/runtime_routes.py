def register_runtime_routes(app, runtime, auth_gateway=None):
    try:
        from fastapi import HTTPException
    except Exception:
        HTTPException = Exception

    @app.post("/v1/runtime/tasks")
    def create_task(body: dict):
        goal = body.get("goal", "")
        if not goal:
            raise HTTPException(status_code=400, detail="goal is required")
        task_id = runtime.submit_goal(goal, body.get("context", {}))
        return {"task_id": task_id, "status": "queued"}

    @app.get("/v1/runtime/state")
    def runtime_state():
        return runtime.snapshot()
