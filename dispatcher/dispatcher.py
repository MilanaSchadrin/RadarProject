from queue import PriorityQueue


class Dispatcher:
    def __init__(self):
        self.currentTime = 0
        self.messageQueues = {}

    def register(self, recipient_id, messages_type=0):
        self.messageQueues[(recipient_id, messages_type)] = PriorityQueue()

    def send_message(self, message, recipient_id, messages_type=0):
        if not (recipient_id, messages_type) in self.messageQueues:
            self.register(recipient_id, messages_type)
        self.messageQueues[(recipient_id, messages_type)].put((message.priority.value, message))

    def get_message(self, recipient_id, messages_type=0):
        return self.messageQueues.get((recipient_id, messages_type), PriorityQueue())
