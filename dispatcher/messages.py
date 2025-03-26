from dataclasses import dataclass


@dataclass
class Message:
    recipient_id: int
    priority: int
    timeSend: int

    def get_data(self):
        pass
