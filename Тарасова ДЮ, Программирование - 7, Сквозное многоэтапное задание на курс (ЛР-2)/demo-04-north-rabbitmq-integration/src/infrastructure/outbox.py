import uuid

class OutboxMessage:
    def __init__(self, event_type: str, payload: dict):
        self.id = str(uuid.uuid4())
        self.event_type = event_type
        self.payload = payload
        self.status = "PENDING"

class Outbox:
    """Транзакционная таблица исходящих сообщений."""
    def __init__(self):
        self._messages: list[OutboxMessage] = []

    def add(self, event_type: str, payload: dict) -> OutboxMessage:
        msg = OutboxMessage(event_type, payload)
        self._messages.append(msg)
        return msg

    def get_pending(self) -> list[OutboxMessage]:
        return [m for m in self._messages if m.status == "PENDING"]

    def mark_published(self, msg: OutboxMessage) -> None:
        msg.status = "PUBLISHED"