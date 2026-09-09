import asyncio
from fastapi import WebSocket

from core.realtime_events import RealtimeEvent, RealtimeEventHub


def register_realtime_routes(app, security_context, event_hub: RealtimeEventHub):
    @app.websocket("/v1/realtime/ws")
    async def realtime_socket(websocket: WebSocket):
        device_id = websocket.headers.get("x-zyra-device-id", "")
        authorization = websocket.headers.get("authorization", "")
        session_id = authorization[7:] if authorization.startswith("Bearer ") else ""

        decision = security_context.api_auth.authorize(
            device_id,
            session_id,
            device_id or "anonymous",
        )
        if not decision.allowed:
            await websocket.close(code=4401)
            return

        await websocket.accept()
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)

        def on_event(event: RealtimeEvent):
            try:
                queue.put_nowait(event.to_json())
            except asyncio.QueueFull:
                # Backpressure is handled by dropping the oldest queued event.
                try:
                    queue.get_nowait()
                    queue.put_nowait(event.to_json())
                except asyncio.QueueEmpty:
                    pass

        unsubscribe = event_hub.subscribe(device_id, on_event)
        try:
            await websocket.send_json({
                "event_type": "realtime.connected",
                "device_id": device_id,
            })
            while True:
                sender = asyncio.create_task(queue.get())
                receiver = asyncio.create_task(websocket.receive_text())
                done, pending = await asyncio.wait(
                    {sender, receiver},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                result = next(iter(done)).result()

                if isinstance(result, str) and result.startswith("{") and '"event_type"' in result:
                    await websocket.send_text(result)
                else:
                    # Client messages are limited to heartbeat/ack control frames.
                    if result in ("ping", "heartbeat"):
                        await websocket.send_json({
                            "event_type": "realtime.pong",
                            "device_id": device_id,
                        })
                    elif result == "close":
                        break
        except Exception:
            pass
        finally:
            unsubscribe()
            try:
                await websocket.close()
            except Exception:
                pass

    return event_hub
