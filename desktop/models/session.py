from dataclasses import dataclass


@dataclass(frozen=True)
class UserSession:
    user_id: int
    login: str
    full_name: str
    position: str
    role: str
