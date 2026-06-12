import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.models
from backend.database import Base, get_db
from backend.main import app
from backend.models.advertising_space_model import AdvertisingSpace
from backend.services.auth_service import clear_sessions
from backend.services.catalog_service import seed_order_catalog

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class AccessControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        engine.dispose()

    def setUp(self):
        clear_sessions()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        with TestingSessionLocal() as db:
            seed_order_catalog(db)
        self.admin_headers = self.login("admin", "admin123")
        self.manager_one = self.create_user("manager.one", "Менеджер Один")
        self.manager_two = self.create_user("manager.two", "Менеджер Два")
        self.manager_one_headers = self.login("manager.one", "password1")
        self.manager_two_headers = self.login("manager.two", "password1")
        self.client_id = self.create_client()

    def login(self, username: str, password: str) -> dict[str, str]:
        response = self.client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['token']}"}

    def create_user(self, username: str, full_name: str) -> dict[str, object]:
        response = self.client.post(
            "/users/",
            headers=self.admin_headers,
            json={
                "username": username,
                "password": "password1",
                "role": "manager",
                "full_name": full_name,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def create_client(self) -> int:
        response = self.client.post(
            "/clients/",
            headers=self.admin_headers,
            json={
                "client_type": "individual",
                "full_name": "Тестовий клієнт",
                "phone": "+380501112233",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def order_payload(self, manager_id=None) -> dict[str, object]:
        return {
            "client_id": self.client_id,
            "manager_id": manager_id,
            "order_type": "printing",
            "status": "new",
            "product_name": "Візитки",
            "quantity": 100,
            "amount_without_vat": "1000.00",
        }

    def test_manager_order_is_forced_to_current_user_and_hidden_from_others(self):
        created = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json=self.order_payload(self.manager_two["id"]),
        )
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["manager_id"], self.manager_one["id"])

        own_orders = self.client.get("/orders/", headers=self.manager_one_headers)
        other_orders = self.client.get("/orders/", headers=self.manager_two_headers)
        admin_orders = self.client.get("/orders/", headers=self.admin_headers)

        self.assertEqual(len(own_orders.json()), 1)
        self.assertEqual(other_orders.json(), [])
        self.assertEqual(len(admin_orders.json()), 1)

    def test_manager_can_claim_unassigned_site_application(self):
        application = self.client.post(
            "/orders/",
            headers=self.admin_headers,
            json=self.order_payload(),
        )
        order_id = application.json()["id"]

        regular_list = self.client.get(
            "/orders/?status=new",
            headers=self.manager_two_headers,
        )
        inbox = self.client.get(
            "/orders/?status=new&include_unassigned=true",
            headers=self.manager_two_headers,
        )
        self.assertEqual(regular_list.json(), [])
        self.assertEqual([order["id"] for order in inbox.json()], [order_id])

        claimed = self.client.patch(
            f"/orders/{order_id}/status",
            headers=self.manager_two_headers,
            json={"status": "in_progress"},
        )
        self.assertEqual(claimed.status_code, 200, claimed.text)
        self.assertEqual(claimed.json()["manager_id"], self.manager_two["id"])

        forbidden = self.client.get(
            f"/orders/{order_id}",
            headers=self.manager_one_headers,
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_manager_cannot_use_admin_endpoints_or_delete_order(self):
        order = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json=self.order_payload(),
        ).json()

        self.assertEqual(
            self.client.get("/users/", headers=self.manager_one_headers).status_code,
            403,
        )
        self.assertEqual(
            self.client.get("/logs/", headers=self.manager_one_headers).status_code,
            403,
        )
        analytics = self.client.get(
            "/analytics/summary",
            headers=self.manager_one_headers,
        )
        self.assertEqual(analytics.status_code, 200)
        self.assertEqual(analytics.json()["orders_total"], 1)
        self.assertEqual(
            self.client.delete(
                f"/orders/{order['id']}",
                headers=self.manager_one_headers,
            ).status_code,
            403,
        )

    def test_manager_analytics_contains_only_own_orders(self):
        self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json=self.order_payload(),
        )
        self.client.post(
            "/orders/",
            headers=self.manager_two_headers,
            json=self.order_payload(),
        )

        manager_summary = self.client.get(
            "/analytics/summary",
            headers=self.manager_one_headers,
        )
        admin_summary = self.client.get(
            "/analytics/summary",
            headers=self.admin_headers,
        )

        self.assertEqual(manager_summary.status_code, 200)
        self.assertEqual(manager_summary.json()["orders_total"], 1)
        self.assertEqual(manager_summary.json()["clients_total"], 1)
        self.assertEqual(admin_summary.json()["orders_total"], 2)

    def test_admin_can_manage_users_and_read_audit_log(self):
        update = self.client.put(
            f"/users/{self.manager_one['id']}",
            headers=self.admin_headers,
            json={"is_active": False},
        )
        self.assertEqual(update.status_code, 200, update.text)
        self.assertFalse(update.json()["is_active"])

        rejected_login = self.client.post(
            "/auth/login",
            json={"username": "manager.one", "password": "password1"},
        )
        self.assertEqual(rejected_login.status_code, 401)

        logs = self.client.get("/logs/", headers=self.admin_headers)
        self.assertEqual(logs.status_code, 200, logs.text)
        actions = {entry["action"] for entry in logs.json()}
        self.assertIn("user_created", actions)
        self.assertIn("user_updated", actions)

    def test_order_crud_persists_changes_and_generates_number(self):
        created = self.client.post(
            "/orders/",
            headers=self.admin_headers,
            json=self.order_payload(self.manager_one["id"]),
        )
        self.assertEqual(created.status_code, 201, created.text)
        order_id = created.json()["id"]
        self.assertEqual(created.json()["order_number"], f"ORD-{order_id:05d}")

        updated = self.client.put(
            f"/orders/{order_id}",
            headers=self.admin_headers,
            json={
                "order_type": "led",
                "rental_start": "2026-06-15",
                "rental_end": "2026-06-20",
                "product_name": None,
                "quantity": None,
                "led_seconds": 15,
                "led_block_seconds": 600,
                "amount_without_vat": "2000.00",
                "discount_rate": "10.00",
                "vat_rate": "20.00",
            },
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["order_type"], "led")
        self.assertEqual(updated.json()["led_seconds"], 15)
        self.assertEqual(updated.json()["total_amount"], "2160.00")

        status_update = self.client.patch(
            f"/orders/{order_id}/status",
            headers=self.admin_headers,
            json={"status": "completed"},
        )
        self.assertEqual(status_update.status_code, 200, status_update.text)

        stored = self.client.get(
            f"/orders/{order_id}",
            headers=self.admin_headers,
        )
        self.assertEqual(stored.json()["status"], "completed")
        self.assertEqual(stored.json()["rental_start"], "2026-06-15")

        deleted = self.client.delete(
            f"/orders/{order_id}",
            headers=self.admin_headers,
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(
            self.client.get(
                f"/orders/{order_id}",
                headers=self.admin_headers,
            ).status_code,
            404,
        )

    def test_authenticated_users_can_load_manager_options(self):
        response = self.client.get(
            "/users/managers",
            headers=self.manager_one_headers,
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            {manager["id"] for manager in response.json()},
            {self.manager_one["id"], self.manager_two["id"]},
        )
        self.assertNotIn("email", response.json()[0])
        self.assertIn("is_active", response.json()[0])

    def test_authenticated_catalog_can_include_inactive_spaces(self):
        with TestingSessionLocal() as db:
            space = db.query(AdvertisingSpace).first()
            self.assertIsNotNone(space)
            space_id = space.id
            space.is_active = False
            db.commit()

        active_catalog = self.client.get(
            "/catalog/order-options",
            headers=self.manager_one_headers,
        )
        full_catalog = self.client.get(
            "/catalog/order-options?include_inactive=true",
            headers=self.manager_one_headers,
        )

        self.assertEqual(active_catalog.status_code, 200, active_catalog.text)
        self.assertEqual(full_catalog.status_code, 200, full_catalog.text)
        self.assertNotIn(
            space_id,
            {item["id"] for item in active_catalog.json()["advertising_spaces"]},
        )
        included_space = next(
            item
            for item in full_catalog.json()["advertising_spaces"]
            if item["id"] == space_id
        )
        self.assertFalse(included_space["is_active"])

    def test_billboard_split_period_and_prolongation_use_database_prices(self):
        catalog = self.client.get(
            "/catalog/order-options",
            headers=self.manager_one_headers,
        )
        self.assertEqual(catalog.status_code, 200, catalog.text)
        billboards = [
            item
            for item in catalog.json()["advertising_spaces"]
            if item["space_type"] == "billboard"
        ]
        self.assertGreaterEqual(len(billboards), 2)

        created = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json={
                "client_id": self.client_id,
                "order_type": "billboard",
                "status": "new",
                "vat_rate": "20.00",
                "discount_rate": "0.00",
                "segments": [
                    {
                        "advertising_space_id": billboards[0]["id"],
                        "period_start": "2026-06-21",
                        "period_end": "2026-06-30",
                        "need_printing": True,
                    },
                    {
                        "advertising_space_id": billboards[1]["id"],
                        "period_start": "2026-07-01",
                        "period_end": "2026-07-18",
                        "need_printing": False,
                    },
                ],
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        order = created.json()
        first_base = float(billboards[0]["base_price"])
        second_base = float(billboards[1]["base_price"])
        print_price = next(
            float(item["amount"])
            for item in catalog.json()["pricing_items"]
            if item["category"] == "billboard_print"
            and item["code"] == billboards[0]["size"]
        )
        expected_subtotal = first_base * 10 + print_price + second_base * 18
        self.assertEqual(float(order["amount_without_vat"]), expected_subtotal)
        self.assertEqual(len(order["segments"]), 2)
        self.assertEqual(order["rental_start"], "2026-06-21")
        self.assertEqual(order["rental_end"], "2026-07-18")

        prolonged = self.client.post(
            f"/orders/{order['id']}/prolong",
            headers=self.manager_one_headers,
            json={
                "segments": [
                    {
                        "advertising_space_id": billboards[0]["id"],
                        "period_start": "2026-07-19",
                        "period_end": "2026-07-25",
                    }
                ]
            },
        )
        self.assertEqual(prolonged.status_code, 200, prolonged.text)
        self.assertEqual(len(prolonged.json()["segments"]), 3)
        self.assertEqual(
            prolonged.json()["segments"][-1]["segment_kind"],
            "extension",
        )
        self.assertEqual(prolonged.json()["rental_end"], "2026-07-25")

    def test_billboard_cannot_be_booked_twice_for_overlapping_period(self):
        catalog = self.client.get(
            "/catalog/order-options",
            headers=self.admin_headers,
        ).json()
        billboard = next(
            space
            for space in catalog["advertising_spaces"]
            if space["space_type"] == "billboard"
        )
        payload = {
            "client_id": self.client_id,
            "order_type": "billboard",
            "segments": [
                {
                    "advertising_space_id": billboard["id"],
                    "period_start": "2027-01-01",
                    "period_end": "2027-01-19",
                }
            ],
        }
        first = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json=payload,
        )
        self.assertEqual(first.status_code, 201, first.text)

        conflict_payload = {
            **payload,
            "segments": [
                {
                    **payload["segments"][0],
                    "period_start": "2027-01-19",
                    "period_end": "2027-01-25",
                }
            ],
        }
        conflict = self.client.post(
            "/orders/",
            headers=self.manager_two_headers,
            json=conflict_payload,
        )
        self.assertEqual(conflict.status_code, 409, conflict.text)
        self.assertIn("уже зайнятий", conflict.json()["detail"])
        self.assertIn("20.01.2027", conflict.json()["detail"])

        available_payload = {
            **payload,
            "segments": [
                {
                    **payload["segments"][0],
                    "period_start": "2027-01-20",
                    "period_end": "2027-01-25",
                }
            ],
        }
        available = self.client.post(
            "/orders/",
            headers=self.manager_two_headers,
            json=available_payload,
        )
        self.assertEqual(available.status_code, 201, available.text)

    def test_one_order_cannot_duplicate_billboard_period(self):
        catalog = self.client.get(
            "/catalog/order-options",
            headers=self.admin_headers,
        ).json()
        billboard = next(
            space
            for space in catalog["advertising_spaces"]
            if space["space_type"] == "billboard"
        )
        response = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json={
                "client_id": self.client_id,
                "order_type": "billboard",
                "segments": [
                    {
                        "advertising_space_id": billboard["id"],
                        "period_start": "2027-01-01",
                        "period_end": "2027-01-10",
                    },
                    {
                        "advertising_space_id": billboard["id"],
                        "period_start": "2027-01-10",
                        "period_end": "2027-01-15",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn("поточне замовлення", response.json()["detail"])

    def test_billboard_prolongation_cannot_overlap_current_booking(self):
        catalog = self.client.get(
            "/catalog/order-options",
            headers=self.manager_one_headers,
        ).json()
        billboard = next(
            space
            for space in catalog["advertising_spaces"]
            if space["space_type"] == "billboard"
        )
        order = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json={
                "client_id": self.client_id,
                "order_type": "billboard",
                "segments": [
                    {
                        "advertising_space_id": billboard["id"],
                        "period_start": "2027-02-01",
                        "period_end": "2027-02-10",
                    }
                ],
            },
        ).json()

        conflict = self.client.post(
            f"/orders/{order['id']}/prolong",
            headers=self.manager_one_headers,
            json={
                "segments": [
                    {
                        "advertising_space_id": billboard["id"],
                        "period_start": "2027-02-10",
                        "period_end": "2027-02-15",
                    }
                ]
            },
        )
        self.assertEqual(conflict.status_code, 409, conflict.text)

    def test_cancelled_billboard_order_releases_space(self):
        catalog = self.client.get(
            "/catalog/order-options",
            headers=self.admin_headers,
        ).json()
        billboard = next(
            space
            for space in catalog["advertising_spaces"]
            if space["space_type"] == "billboard"
        )
        payload = {
            "client_id": self.client_id,
            "order_type": "billboard",
            "segments": [
                {
                    "advertising_space_id": billboard["id"],
                    "period_start": "2027-02-20",
                    "period_end": "2027-02-28",
                }
            ],
        }
        order = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json=payload,
        ).json()
        cancelled = self.client.patch(
            f"/orders/{order['id']}/status",
            headers=self.manager_one_headers,
            json={"status": "cancelled"},
        )
        self.assertEqual(cancelled.status_code, 200, cancelled.text)

        replacement = self.client.post(
            "/orders/",
            headers=self.manager_two_headers,
            json=payload,
        )
        self.assertEqual(replacement.status_code, 201, replacement.text)

    def test_led_overbooking_returns_optimal_impression_recommendation(self):
        catalog = self.client.get(
            "/catalog/order-options",
            headers=self.admin_headers,
        ).json()
        led = next(
            space
            for space in catalog["advertising_spaces"]
            if space["space_type"] == "led"
        )
        base_segment = {
            "advertising_space_id": led["id"],
            "period_start": "2027-03-01",
            "period_end": "2027-03-15",
        }
        existing = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json={
                "client_id": self.client_id,
                "order_type": "led",
                "segments": [
                    {
                        **base_segment,
                        "video_seconds": 60,
                        "impressions_per_day": 896,
                    }
                ],
            },
        )
        self.assertEqual(existing.status_code, 201, existing.text)

        rejected = self.client.post(
            "/orders/",
            headers=self.manager_two_headers,
            json={
                "client_id": self.client_id,
                "order_type": "led",
                "segments": [
                    {
                        **base_segment,
                        "period_end": "2027-03-10",
                        "video_seconds": 20,
                        "impressions_per_day": 600,
                    }
                ],
            },
        )
        self.assertEqual(rejected.status_code, 409, rejected.text)
        detail = rejected.json()["detail"]
        self.assertIn("64800 с/день", detail)
        self.assertIn("552 показів на день", detail)
        self.assertIn("01.03.2027–10.03.2027", detail)

        optimal = self.client.post(
            "/orders/",
            headers=self.manager_two_headers,
            json={
                "client_id": self.client_id,
                "order_type": "led",
                "segments": [
                    {
                        **base_segment,
                        "period_end": "2027-03-10",
                        "video_seconds": 20,
                        "impressions_per_day": 552,
                    }
                ],
            },
        )
        self.assertEqual(optimal.status_code, 201, optimal.text)

    def test_led_order_can_be_edited_without_counting_itself_twice(self):
        catalog = self.client.get(
            "/catalog/order-options",
            headers=self.admin_headers,
        ).json()
        led = next(
            space
            for space in catalog["advertising_spaces"]
            if space["space_type"] == "led"
        )
        created = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json={
                "client_id": self.client_id,
                "order_type": "led",
                "segments": [
                    {
                        "advertising_space_id": led["id"],
                        "period_start": "2027-04-01",
                        "period_end": "2027-04-10",
                        "video_seconds": 60,
                        "impressions_per_day": 1080,
                    }
                ],
            },
        )
        self.assertEqual(created.status_code, 201, created.text)

        updated = self.client.put(
            f"/orders/{created.json()['id']}",
            headers=self.manager_one_headers,
            json={"comment": "Перевірено без подвійного резервування"},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(
            updated.json()["comment"],
            "Перевірено без подвійного резервування",
        )

    def test_led_and_printing_prices_are_calculated_from_catalog(self):
        catalog = self.client.get(
            "/catalog/order-options",
            headers=self.admin_headers,
        ).json()
        led = next(
            space
            for space in catalog["advertising_spaces"]
            if space["space_type"] == "led"
        )
        led_order = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json={
                "client_id": self.client_id,
                "order_type": "led",
                "segments": [
                    {
                        "advertising_space_id": led["id"],
                        "period_start": "2026-06-10",
                        "period_end": "2026-06-12",
                        "video_seconds": 10,
                        "impressions_per_day": 100,
                    }
                ],
            },
        )
        self.assertEqual(led_order.status_code, 201, led_order.text)
        self.assertEqual(
            float(led_order.json()["amount_without_vat"]),
            float(led["base_price"]) * 10 * 100 * 3,
        )

        printing = self.client.post(
            "/orders/",
            headers=self.manager_one_headers,
            json={
                "client_id": self.client_id,
                "order_type": "printing",
                "segments": [
                    {
                        "product_type": "business_card",
                        "product_name": "Візитки",
                        "material_code": "coated_paper",
                        "size_code": "small",
                        "color_mode": "full_color",
                        "quantity": 100,
                    }
                ],
            },
        )
        self.assertEqual(printing.status_code, 201, printing.text)
        price_map = {
            (item["category"], item["code"]): float(item["amount"])
            for item in catalog["pricing_items"]
        }
        expected = 100 * (
            price_map[("print_product", "business_card")]
            + price_map[("print_material", "coated_paper")]
            + price_map[("print_size", "small")]
            + price_map[("print_color", "full_color")]
        )
        self.assertEqual(
            float(printing.json()["amount_without_vat"]),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
