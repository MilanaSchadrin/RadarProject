from PriorityQueue import PriorityQueue


class Dispatcher:
    def __init__(self):
        self.currentTime = 0
        self.messageQueues = {}

    def register(self, recipient_id):
        self.messageQueues[recipient_id] = PriorityQueue()

    def send_message(self, message):
        if message.recipient_id not in self.messageQueues:
            self.register(message.recipient_id)
        self.messageQueues[message.recipient_id].put((-message.priority.value, message))

    def get_message(self, recipient_id):
        return self.messageQueues.get(recipient_id, PriorityQueue())
