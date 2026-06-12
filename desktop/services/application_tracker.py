class NewApplicationTracker:
    def __init__(self):
        self.known_ids: set[int] | None = None

    def update(
        self,
        applications: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        current_ids = {
            item["id"]
            for item in applications
            if isinstance(item.get("id"), int)
        }
        if self.known_ids is None:
            self.known_ids = current_ids
            return []

        new_ids = current_ids - self.known_ids
        self.known_ids = current_ids
        return [
            item for item in applications if item.get("id") in new_ids
        ]
