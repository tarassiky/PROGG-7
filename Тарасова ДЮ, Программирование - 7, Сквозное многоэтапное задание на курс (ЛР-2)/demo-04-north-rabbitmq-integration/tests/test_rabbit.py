from src.application import run_demo

def test_full_rabbit_cycle():
    result = run_demo()
    assert "AUTHORIZED" in result

def test_idempotency():
    """Проверяем, что дубликат сообщения не вызывает повторной команды."""
    from src.infrastructure.inbox import Inbox
    inbox = Inbox()
    inbox.mark_processed("msg-1")
    assert inbox.is_processed("msg-1") is True