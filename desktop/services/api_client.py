class ApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def get_new_orders(self) -> list[dict[str, object]]:
        return []

    def get_new_orders_stats(self) -> dict[str, int]:
        return {
            "total": 0,
            "billboard": 0,
            "led": 0,
            "print": 0,
        }
