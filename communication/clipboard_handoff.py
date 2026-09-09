from dataclasses import dataclass
import time

@dataclass(frozen=True)
class ClipboardItem:
    item_id: str
    kind: str
    content: str
    created_at: int
    source_device: str

class ClipboardQueue:
    def __init__(self):
        self._items: list[ClipboardItem] = []

    def push(self, item: ClipboardItem) -> None:
        self._items.append(item)

    def pending(self, device_id: str | None = None) -> list[ClipboardItem]:
        if device_id is None:
            return list(self._items)
        return [x for x in self._items if x.source_device != device_id]

    @staticmethod
    def make_text(item_id: str, content: str, source_device: str) -> ClipboardItem:
        return ClipboardItem(item_id, "text", content, int(time.time()), source_device)
