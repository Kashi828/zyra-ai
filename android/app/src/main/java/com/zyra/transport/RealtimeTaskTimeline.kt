package com.zyra.transport

class RealtimeTaskTimeline(
    private val listener: (TaskProgress) -> Unit
) : RealtimeEventListener {
    override fun onEvent(event: RealtimeEvent) {
        if (!event.eventType.startsWith("task.")) return
        listener(
            TaskProgress(
                taskId = event.taskId ?: return,
                status = event.status ?: "unknown",
                phase = event.payload.optString("phase", null),
                detail = event.payload.optString("detail", null)
            )
        )
    }

    override fun onPresence(online: Boolean) = Unit
}
