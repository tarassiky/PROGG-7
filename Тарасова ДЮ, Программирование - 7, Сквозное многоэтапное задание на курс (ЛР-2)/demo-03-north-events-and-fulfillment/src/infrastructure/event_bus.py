class InMemoryEventBus:
    """Простой брокер сообщений в памяти."""
    def __init__(self):
        self.handlers = {}

    def subscribe(self, event_type: str, handler):
        self.handlers.setdefault(event_type, []).append(handler)

    def publish(self, event_type: str, payload: dict):
        for handler in self.handlers.get(event_type, []):
            handler(payload)