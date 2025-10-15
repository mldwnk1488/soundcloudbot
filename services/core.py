import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db = None
    
    def set_db(self, database):
        self.db = database
    
    def get_db(self):
        return self.db

class QueueManager:
    def __init__(self):
        self.queue: List[int] = []
        self.current_user: Optional[int] = None
        self._processing = False
        self._user_data = {}

    async def add_to_queue(self, user_id: int) -> int:
        if user_id not in self.queue:
            self.queue.append(user_id)
        
        position = self.queue.index(user_id) + 1
        logger.info(f"Юзер {user_id} в очереди. Позиция: {position}")
        return position

    def start_processing(self, user_id: int):
        self.current_user = user_id
        self._processing = True
        if user_id in self.queue:
            self.queue.remove(user_id)
        logger.info(f"Начата обработка для user_id={user_id}")

    def finish_processing(self):
        logger.info(f"Завершена обработка для user_id={self.current_user}")
        self.current_user = None
        self._processing = False

    def get_next_user(self) -> Optional[int]:
        return self.queue[0] if self.queue else None

    def is_user_in_queue(self, user_id: int) -> bool:
        return user_id in self.queue

    def get_queue_position(self, user_id: int) -> int:
        try:
            return self.queue.index(user_id) + 1
        except ValueError:
            return 0

    def get_queue_size(self) -> int:
        return len(self.queue)

    def is_processing(self) -> bool:
        return self._processing

    def set_user_data(self, user_id: int, data: dict):
        self._user_data[user_id] = data

    def get_user_data(self, user_id: int) -> Optional[dict]:
        return self._user_data.get(user_id)

    def remove_user_data(self, user_id: int):
        if user_id in self._user_data:
            del self._user_data[user_id]

db_manager = DatabaseManager()
queue_manager = QueueManager()