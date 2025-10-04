from collections import deque
from typing import Dict, Any

class QueueManager:
    def __init__(self):
        self.download_queue = deque()
        self.processing = False
        self.queue_status = {}
        self.user_data = {}

    def add_to_queue(self, user_id: int, callback_data: str, user_info: Dict[str, Any]):
        self.download_queue.append((user_id, callback_data, user_info))
        self.queue_status[user_id] = "waiting"

    def get_queue_position(self, user_id: int) -> int:
        for i, (uid, _, _) in enumerate(self.download_queue):
            if uid == user_id:
                return i + 1
        return 0

    def remove_from_queue(self, user_id: int):
        if user_id in self.queue_status:
            del self.queue_status[user_id]

queue_manager = QueueManager()