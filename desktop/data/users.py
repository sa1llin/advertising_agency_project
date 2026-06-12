from models.session import UserSession
from services.api_client import ApiClient


ROLE_POSITIONS = {
    "admin": "Адміністратор системи",
    "manager": "Менеджер рекламного агентства",
}


def authorize_user(
    api_client: ApiClient,
    login: str,
    password: str,
) -> UserSession:
    user = api_client.login(login, password)
    role = str(user["role"])
    return UserSession(
        user_id=int(user["id"]),
        login=str(user["username"]),
        full_name=str(user["full_name"]),
        position=ROLE_POSITIONS.get(role, role),
        role=role,
    )
