import unittest
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.models
from backend.database import Base, get_db
from backend.main import app
from backend.models.order_model import Order
from backend.services.auth_service import clear_sessions

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


class ClientsApiTests(unittest.TestCase):
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
        admin_login = self.client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        self.assertEqual(admin_login.status_code, 200, admin_login.text)
        self.admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['token']}"
        }
        manager = self.client.post(
            "/users/",
            headers=self.admin_headers,
            json={
                "username": "manager",
                "password": "manager123",
                "role": "manager",
                "full_name": "Тестовий менеджер",
            },
        )
        self.assertEqual(manager.status_code, 201, manager.text)
        manager_login = self.client.post(
            "/auth/login",
            json={"username": "manager", "password": "manager123"},
        )
        self.manager_headers = {
            "Authorization": f"Bearer {manager_login.json()['token']}"
        }

    def client_payload(self, **overrides):
        payload = {
            "client_type": "individual",
            "full_name": "Олена Коваль",
            "company_name": None,
            "phone": "+380 50 111 22 33",
            "email": "olena@example.com",
            "legal_address": None,
            "tax_number": None,
            "comment": None,
            "is_active": True,
        }
        payload.update(overrides)
        return payload

    def create_client(self, **overrides):
        response = self.client.post(
            "/clients/",
            headers=self.admin_headers,
            json=self.client_payload(**overrides),
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_individual_may_have_no_legal_address(self):
        created = self.create_client(legal_address=None)

        self.assertIsNone(created["legal_address"])

    def test_company_requires_name_and_legal_address(self):
        response = self.client.post(
            "/clients/",
            headers=self.admin_headers,
            json=self.client_payload(
                client_type="company",
                company_name="ТОВ Приклад",
                legal_address=None,
            ),
        )

        self.assertEqual(response.status_code, 422)

    def test_duplicate_phone_is_rejected_after_normalization(self):
        self.create_client()

        response = self.client.post(
            "/clients/",
            headers=self.admin_headers,
            json=self.client_payload(
                full_name="Інша Людина",
                phone="+380(50)111-22-33",
                email="other@example.com",
            ),
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("телефоном", response.json()["detail"])

    def test_search_and_type_filter(self):
        self.create_client()
        self.create_client(
            client_type="company",
            full_name="Ірина Менеджер",
            company_name="ТОВ Альфа",
            phone="+380671234567",
            email="office@alpha.ua",
            legal_address="Київ",
            tax_number="12345678",
        )

        filtered = self.client.get(
            "/clients/?client_type=company",
            headers=self.admin_headers,
        )
        searched = self.client.get(
            "/clients/?search=alpha.ua",
            headers=self.admin_headers,
        )

        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(len(filtered.json()), 1)
        self.assertEqual(filtered.json()[0]["company_name"], "ТОВ Альфа")
        self.assertEqual(len(searched.json()), 1)

    def test_update_client_and_recheck_duplicates(self):
        first = self.create_client()
        second = self.create_client(
            full_name="Марія Іваненко",
            phone="+380671234567",
            email="maria@example.com",
        )

        updated = self.client.put(
            f"/clients/{first['id']}",
            headers=self.admin_headers,
            json={"full_name": "Олена Коваль-Нова"},
        )
        duplicate = self.client.put(
            f"/clients/{second['id']}",
            headers=self.admin_headers,
            json={"email": "olena@example.com"},
        )

        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["full_name"], "Олена Коваль-Нова")
        self.assertEqual(duplicate.status_code, 409)

    def test_manager_cannot_fully_delete_client(self):
        created = self.create_client()

        response = self.client.delete(
            f"/clients/{created['id']}",
            headers=self.manager_headers,
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_delete_client_without_orders(self):
        created = self.create_client()

        response = self.client.delete(
            f"/clients/{created['id']}",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 204)

    def test_client_with_orders_cannot_be_deleted(self):
        created = self.create_client()
        with TestingSessionLocal() as db:
            db.add(
                Order(
                    order_number="ORD-00001",
                    client_id=created["id"],
                    order_type="printing",
                    status="new",
                    product_name="Візитки",
                    quantity=100,
                    vat_rate=Decimal("20.00"),
                    discount_rate=Decimal("0.00"),
                    amount_without_vat=Decimal("1000.00"),
                    discount_amount=Decimal("0.00"),
                    vat_amount=Decimal("200.00"),
                    total_amount=Decimal("1200.00"),
                )
            )
            db.commit()

        response = self.client.delete(
            f"/clients/{created['id']}",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("пов'язані замовлення", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
