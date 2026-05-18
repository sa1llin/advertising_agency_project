from dataclasses import dataclass


@dataclass(frozen=True)
class UserSession:
    login: str
    position: str
    role: str
