import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

DESKTOP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESKTOP_ROOT))

from services.api_client import ApiClient, ApiError
from services.application_tracker import NewApplicationTracker


class FakeResponse:
    def __init__(self, payload: object):
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self) -> bytes:
        return self.body


class ApiClientTests(unittest.TestCase):
    def setUp(self):
        self.client = ApiClient("http://127.0.0.1:8000", timeout=2)

    @patch("services.api_client.urlopen")
    def test_get_orders_builds_filters(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse([{"id": 1, "status": "new"}])

        result = self.client.get_orders(status="new", client_id=3)

        self.assertEqual(result[0]["id"], 1)
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIn("/orders/?", request.full_url)
        self.assertIn("status=new", request.full_url)
        self.assertIn("client_id=3", request.full_url)
        self.assertIn("limit=500", request.full_url)

    @patch("services.api_client.urlopen")
    def test_update_order_status_sends_json(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse({"id": 7, "status": "in_progress"})

        result = self.client.update_order_status(7, "in_progress")

        self.assertEqual(result["status"], "in_progress")
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "PATCH")
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {"status": "in_progress"},
        )

    @patch("services.api_client.urlopen")
    def test_create_client_sends_json(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse({"id": 3, "full_name": "Олена"})
        payload = {
            "client_type": "individual",
            "full_name": "Олена",
            "phone": "+380501112233",
        }

        result = self.client.create_client(payload)

        self.assertEqual(result["id"], 3)
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data.decode("utf-8")), payload)

    @patch("services.api_client.urlopen")
    def test_delete_client_sends_authorization_header(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(None)
        self.client.token = "session-token"

        self.client.delete_client(5)

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "DELETE")
        self.assertEqual(
            request.get_header("Authorization"),
            "Bearer session-token",
        )

    @patch("services.api_client.urlopen")
    def test_login_stores_token_and_returns_user(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(
            {
                "token": "abc123",
                "user": {
                    "id": 4,
                    "username": "manager",
                    "role": "manager",
                    "full_name": "Менеджер",
                },
            }
        )

        user = self.client.login("manager", "manager123")

        self.assertEqual(user["id"], 4)
        self.assertEqual(self.client.token, "abc123")

    @patch("services.api_client.urlopen")
    def test_new_orders_include_unassigned_applications(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse([])

        self.client.get_new_orders()

        request = mocked_urlopen.call_args.args[0]
        self.assertIn("status=new", request.full_url)
        self.assertIn("include_unassigned=true", request.full_url)

    @patch("services.api_client.urlopen")
    def test_update_client_sends_put(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse({"id": 5, "full_name": "Олена Нова"})

        result = self.client.update_client(5, {"full_name": "Олена Нова"})

        self.assertEqual(result["full_name"], "Олена Нова")
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "PUT")
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {"full_name": "Олена Нова"},
        )

    def test_get_all_clients_reads_all_pages(self):
        self.client.get_clients = Mock(
            side_effect=[
                [{"id": 1}, {"id": 2}],
                [{"id": 3}],
            ]
        )

        result = self.client.get_all_clients(page_size=2)

        self.assertEqual([client["id"] for client in result], [1, 2, 3])
        self.assertEqual(self.client.get_clients.call_count, 2)

    def test_get_all_orders_reads_all_pages(self):
        self.client.get_orders = Mock(
            side_effect=[
                [{"id": 1}, {"id": 2}],
                [{"id": 3}],
            ]
        )

        result = self.client.get_all_orders(page_size=2)

        self.assertEqual([order["id"] for order in result], [1, 2, 3])
        self.assertEqual(self.client.get_orders.call_count, 2)

    @patch("services.api_client.urlopen")
    def test_create_order_sends_post(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(
            {"id": 8, "order_number": "ORD-00008"}
        )
        payload = {
            "client_id": 1,
            "order_type": "printing",
            "product_name": "Візитки",
            "quantity": 100,
        }

        result = self.client.create_order(payload)

        self.assertEqual(result["order_number"], "ORD-00008")
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data.decode("utf-8")), payload)

    @patch("services.api_client.urlopen")
    def test_update_order_sends_put(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse({"id": 8, "status": "paused"})

        self.client.update_order(8, {"status": "paused"})

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "PUT")
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {"status": "paused"},
        )

    @patch("services.api_client.urlopen")
    def test_prolong_order_sends_segments(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse({"id": 8, "segments": []})
        segments = [
            {
                "advertising_space_id": 2,
                "period_start": "2026-07-01",
                "period_end": "2026-07-07",
            }
        ]

        self.client.prolong_order(8, segments)

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {"segments": segments},
        )

    @patch("services.api_client.urlopen")
    def test_get_order_catalog(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(
            {"advertising_spaces": [], "pricing_items": []}
        )

        result = self.client.get_order_catalog(include_inactive=True)

        self.assertEqual(result["advertising_spaces"], [])
        request = mocked_urlopen.call_args.args[0]
        self.assertIn("/catalog/order-options", request.full_url)
        self.assertIn("include_inactive=true", request.full_url)

    def test_new_order_stats_reuses_supplied_orders(self):
        stats = self.client.get_new_orders_stats(
            [
                {"order_type": "billboard"},
                {"order_type": "led"},
                {"order_type": "printing"},
                {"order_type": "printing"},
            ]
        )

        self.assertEqual(
            stats,
            {"total": 4, "billboard": 1, "led": 1, "printing": 2},
        )

    @patch("services.api_client.urlopen")
    def test_get_applications_builds_inbox_filters(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse([{"id": 12, "status": "new"}])

        result = self.client.get_applications(
            status="new",
            include_hidden=True,
        )

        self.assertEqual(result[0]["id"], 12)
        request = mocked_urlopen.call_args.args[0]
        self.assertIn("/applications/?", request.full_url)
        self.assertIn("status=new", request.full_url)
        self.assertIn("include_hidden=true", request.full_url)

    @patch("services.api_client.urlopen")
    def test_link_application_order_sends_order_id(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(
            {"id": 12, "status": "processed", "order_id": 8}
        )

        result = self.client.link_application_order(12, 8)

        self.assertEqual(result["order_id"], 8)
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "PATCH")
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {"order_id": 8},
        )

    @patch("services.api_client.urlopen")
    def test_http_error_uses_backend_detail(self, mocked_urlopen):
        mocked_urlopen.side_effect = HTTPError(
            "http://127.0.0.1:8000/orders/",
            404,
            "Not Found",
            hdrs=None,
            fp=BytesIO('{"detail":"Замовлення не знайдено"}'.encode("utf-8")),
        )

        with self.assertRaisesRegex(ApiError, "Замовлення не знайдено"):
            self.client.get_orders()

    @patch("services.api_client.urlopen")
    def test_connection_error_is_wrapped(self, mocked_urlopen):
        mocked_urlopen.side_effect = URLError("connection refused")

        with self.assertRaisesRegex(ApiError, "Не вдалося підключитися"):
            self.client.health_check()

    def test_application_tracker_reports_only_arrivals_after_baseline(self):
        tracker = NewApplicationTracker()

        self.assertEqual(tracker.update([{"id": 1}, {"id": 2}]), [])
        self.assertEqual(
            tracker.update([{"id": 3}, {"id": 2}, {"id": 1}]),
            [{"id": 3}],
        )
        self.assertEqual(tracker.update([{"id": 3}, {"id": 2}]), [])


if __name__ == "__main__":
    unittest.main()
