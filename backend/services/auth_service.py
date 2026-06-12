import secrets
from threading import Lock


_sessions: dict[str, int] = {}
_sessions_lock = Lock()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with _sessions_lock:
        _sessions[token] = user_id
    return token


def get_session_user_id(token: str) -> int | None:
    with _sessions_lock:
        return _sessions.get(token)


def delete_session(token: str) -> None:
    with _sessions_lock:
        _sessions.pop(token, None)


def delete_user_sessions(user_id: int) -> None:
    with _sessions_lock:
        expired_tokens = [
            token for token, session_user_id in _sessions.items()
            if session_user_id == user_id
        ]
        for token in expired_tokens:
            _sessions.pop(token, None)


def clear_sessions() -> None:
    with _sessions_lock:
        _sessions.clear()
