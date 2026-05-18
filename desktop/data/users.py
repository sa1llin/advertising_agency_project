from models.session import UserSession


USERS = {
    "admin": {
        "password": "admin123",
        "position": "Адміністратор системи",
        "role": "admin",
    },
    "manager": {
        "password": "manager123",
        "position": "Менеджер рекламного агентства",
        "role": "manager",
    },
}


def authorize_user(login: str, password: str) -> UserSession | None:
    user = USERS.get(login)

    if user is None:
        return None

    if user["password"] != password:
        return None

    return UserSession(
        login=login,
        position=user["position"],
        role=user["role"],
    )
