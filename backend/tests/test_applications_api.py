import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.models
from backend.database import Base, get_db
from backend.main import app
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


class ApplicationsApiTests(unittest.TestCase):
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
        manager = self.client.post(
            "/users/",
            headers=self.admin_headers,
            json={
                "username": "site.manager",
                "password": "password1",
                "role": "manager",
                "full_name": "Менеджер заявок",
            },
        )
        self.assertEqual(manager.status_code, 201, manager.text)
        self.manager = manager.json()
        self.manager_headers = self.login("site.manager", "password1")

    def login(self, username: str, password: str) -> dict[str, str]:
        response = self.client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['token']}"}

    def submit_application(self, **overrides) -> dict[str, object]:
        payload = {
            "full_name": "Олена Коваль",
            "phone": "+380501112233",
            "email": "olena@example.com",
            "service_type": "printing",
            "comment": "Потрібні 100 візиток",
            "source": "calculator",
            "calculation_data": {
                "service_type": "printing",
                "product_type": "business_card",
                "product_name": "Візитки",
                "material_code": "coated_paper",
                "material_name": "Крейдований папір",
                "size_code": "small",
                "size_name": "Малий",
                "color_mode": "full_color",
                "color_name": "Повноколірна",
                "quantity": 100,
                "estimated_total": "1250.00",
                "price_rows": [
                    {"label": "Візитки", "amount": "1250.00"}
                ],
            },
        }
        payload.update(overrides)
        response = self.client.post("/applications/", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_public_submission_and_authenticated_inbox(self):
        created = self.submit_application()

        self.assertEqual(created["status"], "new")
        self.assertIsNone(created["client_id"])
        self.assertEqual(created["estimated_total"], "1250.00")
        self.assertEqual(created["source"], "calculator")
        self.assertEqual(
            created["calculation_data"]["service_type"],
            "printing",
        )
        self.assertEqual(self.client.get("/applications/").status_code, 401)

        inbox = self.client.get(
            "/applications/?status=new",
            headers=self.manager_headers,
        )
        self.assertEqual(inbox.status_code, 200, inbox.text)
        self.assertEqual([item["id"] for item in inbox.json()], [created["id"]])

    def test_submission_without_service_is_regular_application(self):
        response = self.client.post(
            "/applications/",
            json={
                "full_name": "Звичайна заявка",
                "phone": "+380671234567",
                "email": "regular@example.com",
                "comment": "Потрібна консультація",
            },
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["service_type"], "other")
        self.assertEqual(response.json()["source"], "contact")
        self.assertIsNone(response.json()["calculation_data"])
        self.assertIsNone(response.json()["estimated_total"])

    def test_contact_form_drops_calculation_fields(self):
        response = self.client.post(
            "/applications/",
            json={
                "full_name": "Звичайна заявка",
                "phone": "+380671234567",
                "email": "regular@example.com",
                "service_type": "billboard",
                "source": "contact",
                "estimated_total": "99999.00",
            },
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertIsNone(response.json()["estimated_total"])
        self.assertIsNone(response.json()["calculation_data"])

    def test_calculator_type_mismatch_is_rejected(self):
        payload = {
            "full_name": "Помилкова заявка",
            "phone": "+380671234567",
            "email": "mismatch@example.com",
            "service_type": "led",
            "source": "calculator",
            "calculation_data": {
                "service_type": "printing",
                "product_type": "business_card",
                "product_name": "Візитки",
                "material_code": "coated_paper",
                "material_name": "Крейдований папір",
                "size_code": "small",
                "size_name": "Малий",
                "color_mode": "full_color",
                "color_name": "Повноколірна",
                "quantity": 100,
                "estimated_total": "1250.00",
                "price_rows": [],
            },
        }

        response = self.client.post("/applications/", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_public_catalog_is_available_without_login(self):
        response = self.client.get("/catalog/public-order-options")

        self.assertEqual(response.status_code, 200, response.text)
        self.assertGreater(len(response.json()["advertising_spaces"]), 0)
        self.assertGreater(len(response.json()["pricing_items"]), 0)

    def test_billboard_and_led_calculations_keep_separate_fields(self):
        catalog = self.client.get("/catalog/public-order-options").json()
        billboard = next(
            item
            for item in catalog["advertising_spaces"]
            if item["space_type"] == "billboard"
        )
        led = next(
            item
            for item in catalog["advertising_spaces"]
            if item["space_type"] == "led"
        )
        common = {
            "full_name": "Клієнт калькулятора",
            "phone": "+380671234567",
            "source": "calculator",
        }

        billboard_response = self.client.post(
            "/applications/",
            json={
                **common,
                "email": "billboard@example.com",
                "service_type": "billboard",
                "calculation_data": {
                    "service_type": "billboard",
                    "advertising_space_id": billboard["id"],
                    "location": billboard["location"],
                    "size": billboard["size"],
                    "period_start": "2026-06-12",
                    "period_end": "2026-06-20",
                    "days": 9,
                    "need_printing": True,
                    "estimated_total": "9450.00",
                    "price_rows": [],
                },
            },
        )
        led_response = self.client.post(
            "/applications/",
            json={
                **common,
                "email": "led@example.com",
                "service_type": "led",
                "calculation_data": {
                    "service_type": "led",
                    "advertising_space_id": led["id"],
                    "location": led["location"],
                    "size": led["size"],
                    "period_start": "2026-06-12",
                    "period_end": "2026-06-20",
                    "days": 9,
                    "video_seconds": 10,
                    "impressions_per_day": 100,
                    "estimated_total": "10800.00",
                    "price_rows": [],
                },
            },
        )

        self.assertEqual(billboard_response.status_code, 201, billboard_response.text)
        self.assertEqual(led_response.status_code, 201, led_response.text)
        billboard_data = billboard_response.json()["calculation_data"]
        led_data = led_response.json()["calculation_data"]
        self.assertIn("need_printing", billboard_data)
        self.assertNotIn("video_seconds", billboard_data)
        self.assertIn("video_seconds", led_data)
        self.assertNotIn("need_printing", led_data)

    def test_application_can_create_client_and_link_manager_order(self):
        application = self.submit_application()
        client_response = self.client.post(
            f"/applications/{application['id']}/create-client",
            headers=self.manager_headers,
        )
        self.assertEqual(client_response.status_code, 200, client_response.text)
        client_data = client_response.json()
        self.assertEqual(client_data["full_name"], application["full_name"])

        order_response = self.client.post(
            "/orders/",
            headers=self.manager_headers,
            json={
                "client_id": client_data["id"],
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
        self.assertEqual(order_response.status_code, 201, order_response.text)

        linked = self.client.patch(
            f"/applications/{application['id']}/link-order",
            headers=self.manager_headers,
            json={"order_id": order_response.json()["id"]},
        )
        self.assertEqual(linked.status_code, 200, linked.text)
        self.assertEqual(linked.json()["status"], "processed")
        self.assertEqual(linked.json()["client_id"], client_data["id"])
        self.assertEqual(linked.json()["order_id"], order_response.json()["id"])
        self.assertEqual(linked.json()["processed_by"], self.manager["id"])

    def test_processed_application_can_be_hidden_and_admin_can_delete(self):
        application = self.submit_application()
        processed = self.client.patch(
            f"/applications/{application['id']}/status",
            headers=self.manager_headers,
            json={"status": "processed"},
        )
        self.assertEqual(processed.status_code, 200, processed.text)

        hidden = self.client.patch(
            f"/applications/{application['id']}/visibility",
            headers=self.manager_headers,
            json={"is_hidden": True},
        )
        self.assertEqual(hidden.status_code, 200, hidden.text)
        self.assertTrue(hidden.json()["is_hidden"])

        regular = self.client.get("/applications/", headers=self.manager_headers)
        with_hidden = self.client.get(
            "/applications/?include_hidden=true",
            headers=self.manager_headers,
        )
        self.assertEqual(regular.json(), [])
        self.assertEqual(len(with_hidden.json()), 1)

        forbidden = self.client.delete(
            f"/applications/{application['id']}",
            headers=self.manager_headers,
        )
        self.assertEqual(forbidden.status_code, 403)

        deleted = self.client.delete(
            f"/applications/{application['id']}",
            headers=self.admin_headers,
        )
        self.assertEqual(deleted.status_code, 204)

    def test_new_application_cannot_be_hidden(self):
        application = self.submit_application()
        response = self.client.patch(
            f"/applications/{application['id']}/visibility",
            headers=self.manager_headers,
            json={"is_hidden": True},
        )
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
