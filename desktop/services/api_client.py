import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 5,
        token: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = token

    def login(self, username: str, password: str) -> dict[str, object]:
        result = self._request(
            "POST",
            "/auth/login",
            payload={"username": username, "password": password},
        )
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректну відповідь авторизації.")
        token = result.get("token")
        user = result.get("user")
        if not isinstance(token, str) or not isinstance(user, dict):
            raise ApiError("Backend повернув неповні дані авторизації.")
        self.token = token
        return user

    def logout(self) -> None:
        if self.token is None:
            return
        try:
            self._request("POST", "/auth/logout")
        finally:
            self.token = None

    def health_check(self) -> dict[str, object]:
        return self._get_dict("/health")

    def get_orders(
        self,
        *,
        order_type: str | None = None,
        status: str | None = None,
        client_id: int | None = None,
        include_unassigned: bool = False,
        skip: int = 0,
        limit: int = 500,
    ) -> list[dict[str, object]]:
        query: dict[str, object] = {"skip": skip, "limit": limit}
        if order_type is not None:
            query["order_type"] = order_type
        if status is not None:
            query["status"] = status
        if client_id is not None:
            query["client_id"] = client_id
        if include_unassigned:
            query["include_unassigned"] = "true"

        return self._get_list("/orders/", query)

    def get_all_orders(
        self,
        *,
        order_type: str | None = None,
        status: str | None = None,
        client_id: int | None = None,
        include_unassigned: bool = False,
        page_size: int = 500,
    ) -> list[dict[str, object]]:
        orders: list[dict[str, object]] = []
        skip = 0
        while True:
            page = self.get_orders(
                order_type=order_type,
                status=status,
                client_id=client_id,
                include_unassigned=include_unassigned,
                skip=skip,
                limit=page_size,
            )
            orders.extend(page)
            if len(page) < page_size:
                return orders
            skip += page_size

    def get_new_orders(self) -> list[dict[str, object]]:
        return self.get_orders(status="new", include_unassigned=True)

    def get_new_orders_stats(
        self,
        orders: list[dict[str, object]] | None = None,
    ) -> dict[str, int]:
        new_orders = orders if orders is not None else self.get_new_orders()
        stats = {
            "total": len(new_orders),
            "billboard": 0,
            "led": 0,
            "printing": 0,
        }

        for order in new_orders:
            order_type = str(order.get("order_type", ""))
            if order_type in stats:
                stats[order_type] += 1

        return stats

    def get_applications(
        self,
        *,
        status: str | None = None,
        search: str | None = None,
        include_hidden: bool = False,
        skip: int = 0,
        limit: int = 500,
    ) -> list[dict[str, object]]:
        query: dict[str, object] = {"skip": skip, "limit": limit}
        if status is not None:
            query["status"] = status
        if search:
            query["search"] = search
        if include_hidden:
            query["include_hidden"] = "true"
        return self._get_list("/applications/", query)

    def get_all_applications(
        self,
        *,
        status: str | None = None,
        search: str | None = None,
        include_hidden: bool = False,
        page_size: int = 500,
    ) -> list[dict[str, object]]:
        applications: list[dict[str, object]] = []
        skip = 0
        while True:
            page = self.get_applications(
                status=status,
                search=search,
                include_hidden=include_hidden,
                skip=skip,
                limit=page_size,
            )
            applications.extend(page)
            if len(page) < page_size:
                return applications
            skip += page_size

    def update_application_status(
        self,
        application_id: int,
        status: str,
    ) -> dict[str, object]:
        result = self._request(
            "PATCH",
            f"/applications/{application_id}/status",
            payload={"status": status},
        )
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані заявки.")
        return result

    def create_client_from_application(
        self,
        application_id: int,
    ) -> dict[str, object]:
        result = self._request(
            "POST",
            f"/applications/{application_id}/create-client",
        )
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані клієнта.")
        return result

    def link_application_order(
        self,
        application_id: int,
        order_id: int,
    ) -> dict[str, object]:
        result = self._request(
            "PATCH",
            f"/applications/{application_id}/link-order",
            payload={"order_id": order_id},
        )
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані заявки.")
        return result

    def set_application_hidden(
        self,
        application_id: int,
        is_hidden: bool = True,
    ) -> dict[str, object]:
        result = self._request(
            "PATCH",
            f"/applications/{application_id}/visibility",
            payload={"is_hidden": is_hidden},
        )
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані заявки.")
        return result

    def delete_application(self, application_id: int) -> None:
        self._request("DELETE", f"/applications/{application_id}")

    def get_clients(
        self,
        *,
        search: str | None = None,
        client_type: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 500,
    ) -> list[dict[str, object]]:
        query: dict[str, object] = {"skip": skip, "limit": limit}
        if search:
            query["search"] = search
        if client_type:
            query["client_type"] = client_type
        if is_active is not None:
            query["is_active"] = str(is_active).lower()

        return self._get_list("/clients/", query)

    def get_all_clients(
        self,
        *,
        search: str | None = None,
        client_type: str | None = None,
        is_active: bool | None = None,
        page_size: int = 500,
    ) -> list[dict[str, object]]:
        clients: list[dict[str, object]] = []
        skip = 0

        while True:
            page = self.get_clients(
                search=search,
                client_type=client_type,
                is_active=is_active,
                skip=skip,
                limit=page_size,
            )
            clients.extend(page)
            if len(page) < page_size:
                return clients
            skip += page_size

    def get_client(self, client_id: int) -> dict[str, object]:
        return self._get_dict(f"/clients/{client_id}")

    def create_client(self, payload: dict[str, object]) -> dict[str, object]:
        result = self._request("POST", "/clients/", payload=payload)
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані клієнта.")
        return result

    def update_client(
        self,
        client_id: int,
        payload: dict[str, object],
    ) -> dict[str, object]:
        result = self._request("PUT", f"/clients/{client_id}", payload=payload)
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані клієнта.")
        return result

    def delete_client(self, client_id: int) -> None:
        self._request("DELETE", f"/clients/{client_id}")

    def delete_order(self, order_id: int) -> None:
        self._request("DELETE", f"/orders/{order_id}")

    def create_order(self, payload: dict[str, object]) -> dict[str, object]:
        result = self._request("POST", "/orders/", payload=payload)
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані замовлення.")
        return result

    def update_order(
        self,
        order_id: int,
        payload: dict[str, object],
    ) -> dict[str, object]:
        result = self._request("PUT", f"/orders/{order_id}", payload=payload)
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані замовлення.")
        return result

    def prolong_order(
        self,
        order_id: int,
        segments: list[dict[str, object]],
    ) -> dict[str, object]:
        result = self._request(
            "POST",
            f"/orders/{order_id}/prolong",
            payload={"segments": segments},
        )
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані пролонгації.")
        return result

    def update_order_status(self, order_id: int, status: str) -> dict[str, object]:
        result = self._request(
            "PATCH",
            f"/orders/{order_id}/status",
            payload={"status": status},
        )
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані замовлення.")
        return result

    def get_users(self) -> list[dict[str, object]]:
        return self._get_list("/users/")

    def get_managers(self) -> list[dict[str, object]]:
        return self._get_list("/users/managers")

    def create_user(self, payload: dict[str, object]) -> dict[str, object]:
        result = self._request("POST", "/users/", payload=payload)
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані працівника.")
        return result

    def update_user(
        self,
        user_id: int,
        payload: dict[str, object],
    ) -> dict[str, object]:
        result = self._request("PUT", f"/users/{user_id}", payload=payload)
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректні дані працівника.")
        return result

    def get_logs(self, limit: int = 500) -> list[dict[str, object]]:
        return self._get_list("/logs/", {"limit": limit})

    def get_analytics_summary(self) -> dict[str, object]:
        return self._get_dict("/analytics/summary")

    def get_order_catalog(
        self,
        include_inactive: bool = False,
    ) -> dict[str, object]:
        query = {"include_inactive": "true"} if include_inactive else None
        return self._get_dict("/catalog/order-options", query)

    def _get_list(
        self,
        path: str,
        query: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        result = self._request("GET", path, query=query)
        if not isinstance(result, list) or not all(
            isinstance(item, dict) for item in result
        ):
            raise ApiError("Backend повернув некоректний список даних.")
        return result

    def _get_dict(
        self,
        path: str,
        query: dict[str, object] | None = None,
    ) -> dict[str, object]:
        result = self._request("GET", path, query=query)
        if not isinstance(result, dict):
            raise ApiError("Backend повернув некоректний об'єкт даних.")
        return result

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, object] | None = None,
        payload: dict[str, object] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urlencode(query)}"

        data = None
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if extra_headers:
            headers.update(extra_headers)
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except HTTPError as error:
            detail = self._extract_error_detail(error.read())
            raise ApiError(
                detail or f"Backend повернув HTTP {error.code}.", error.code
            ) from error
        except URLError as error:
            reason = getattr(error, "reason", error)
            raise ApiError(
                f"Не вдалося підключитися до backend {self.base_url}: {reason}"
            ) from error
        except TimeoutError as error:
            raise ApiError(
                f"Backend не відповів протягом {self.timeout:g} с."
            ) from error

        if not body:
            return None

        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ApiError("Backend повернув некоректний JSON.") from error

    @staticmethod
    def _extract_error_detail(body: bytes) -> str:
        if not body:
            return ""
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return body.decode("utf-8", errors="replace")

        detail = payload.get("detail") if isinstance(payload, dict) else None
        if isinstance(detail, str):
            return detail
        if detail is not None:
            return json.dumps(detail, ensure_ascii=False)
        return ""
