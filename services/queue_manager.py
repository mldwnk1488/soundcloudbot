from collections import deque

class QueueManager:
    def __init__(self):
        self.download_queue = deque()
        self.queue_status = {}
        self.user_data = {}
        self.processing = False
        self.user_languages = {}
    
    def add_to_queue(self, user_id, download_type, user_info):
        self.download_queue.append((user_id, download_type, user_info))
        self.queue_status[user_id] = "waiting"
    
    def remove_from_queue(self, user_id):
        if user_id in self.queue_status:
            del self.queue_status[user_id]
        if user_id in self.user_data:
            del self.user_data[user_id]
    
    def get_queue_position(self, user_id):
        for idx, (uid, _, _) in enumerate(self.download_queue, 1):
            if uid == user_id:
                return idx
        return 0

queue_manager = QueueManager()