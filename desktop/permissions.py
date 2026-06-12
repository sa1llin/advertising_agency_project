NAV_ITEMS = [
    {
        "key": "new_orders",
        "title": "Нові заявки",
        "subtitle": "Заявки на зворотний зв’язок, що надійшли з сайту",
        "icon": "assignment",
        "roles": ["admin", "manager"],
    },
    {
        "key": "all_orders",
        "title": "Усі замовлення",
        "subtitle": "Повний список замовлень агентства",
        "icon": "list_alt",
        "roles": ["admin", "manager"],
    },
    {
        "key": "clients",
        "title": "База клієнтів",
        "subtitle": "Клієнти, компанії та контактні особи",
        "icon": "groups",
        "roles": ["admin", "manager"],
    },
    {
        "key": "analytics",
        "title": "Аналітика",
        "subtitle": "Показники продажів, доходів та популярних послуг",
        "icon": "bar_chart",
        "roles": ["admin", "manager"],
    },
    {
        "key": "reports",
        "title": "Звіти",
        "subtitle": "Формування звітів та друк документів",
        "icon": "description",
        "roles": ["admin", "manager"],
    },
    {
        "key": "users",
        "title": "Користувачі",
        "subtitle": "Керування адміністраторами та менеджерами",
        "icon": "manage_accounts",
        "roles": ["admin"],
    },
    {
        "key": "logs",
        "title": "Логи системи",
        "subtitle": "Журнал дій користувачів у CRM",
        "icon": "history",
        "roles": ["admin"],
    },
]


def get_nav_items(role: str) -> list[dict[str, object]]:
    return [item for item in NAV_ITEMS if role in item["roles"]]
