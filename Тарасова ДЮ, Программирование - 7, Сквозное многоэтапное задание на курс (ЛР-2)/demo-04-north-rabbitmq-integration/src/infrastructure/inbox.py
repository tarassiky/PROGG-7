class Inbox:
    """Таблица уже обработанных входящих сообщений."""
    def __init__(self):
        self._processed_ids: set[str] = set()

    def is_processed(self, message_id: str) -> bool:
        return message_id in self._processed_ids

    def mark_processed(self, message_id: str) -> None:
        self._processed_ids.add(message_id)