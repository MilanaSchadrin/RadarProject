from queue import PriorityQueue
from dispatcher.logger import Logger
from pathlib import Path

class Dispatcher:
    def __init__(self):
        self.currentTime = 0
        self.messageQueues = {}
        self.logger = Logger(Path('./logs'))

    def register(self, recipient_id):
        self.messageQueues[recipient_id] = PriorityQueue()

    def send_message(self, message):
        if message.recipient_id not in self.messageQueues:
            self.register(message.recipient_id)
        self.messageQueues[message.recipient_id].put((message.priority.value, message))
        self.logger.log(message)

    def get_message(self, recipient_id):
        return self.messageQueues.get(recipient_id, PriorityQueue())