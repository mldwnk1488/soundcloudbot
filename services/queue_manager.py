from collections import deque
import asyncio

class QueueManager:
    def __init__(self):
        self.download_queue = deque()
        self.queue_status = {}
        self.user_data = {}
        self.processing = False
        self.lock = asyncio.Lock()
        self.processing_lock = asyncio.Lock()  # 🔥 ДОБАВЛЯЕМ ЛОК ДЛЯ ПРОЦЕССИНГА
    
    async def add_to_queue(self, user_id, download_type, user_info):
        async with self.lock:
            # 🔥 ПРОВЕРЯЕМ ЧТО ЮЗЕР УЖЕ НЕ В ОЧЕРЕДИ
            for uid, _, _ in self.download_queue:
                if uid == user_id:
                    return False  # Уже в очереди
            
            self.download_queue.append((user_id, download_type, user_info))
            self.queue_status[user_id] = "waiting"
            return True
    
    async def remove_from_queue(self, user_id):
        async with self.lock:
            if user_id in self.queue_status:
                del self.queue_status[user_id]
            if user_id in self.user_data:
                del self.user_data[user_id]
    
    def get_queue_position(self, user_id):
        for idx, (uid, _, _) in enumerate(self.download_queue, 1):
            if uid == user_id:
                return idx
        return 0
    
    def is_user_in_queue(self, user_id):
        """Проверяем есть ли юзер уже в очереди"""
        return any(uid == user_id for uid, _, _ in self.download_queue)
    
    async def process_next(self):
        """Безопасно получаем следующего юзера из очереди"""
        async with self.processing_lock:
            if self.download_queue:
                return self.download_queue[0]
            return None
    
    async def complete_current(self):
        """Безопасно завершаем текущую задачу"""
        async with self.processing_lock:
            if self.download_queue:
                user_id, _, _ = self.download_queue[0]
                self.download_queue.popleft()
                await self.remove_from_queue(user_id)

queue_manager = QueueManager()