import unittest
from unittest.mock import Mock

from src.core.athlete_importer import AthleteImporter, normalize_api_url


class AthleteImporterApiTests(unittest.TestCase):
    def test_normalizes_frontend_api_v1_url(self):
        self.assertEqual(
            normalize_api_url("http://localhost:8000/api/v1/"),
            "http://localhost:8000",
        )

    def test_keeps_backend_origin_unchanged(self):
        self.assertEqual(
            normalize_api_url("https://backend.example.com/"),
            "https://backend.example.com",
        )

    def test_import_uses_hardware_endpoint_and_bearer_token(self):
        importer = AthleteImporter(
            "http://localhost:8000/api/v1",
            api_key="agent-token",
        )
        response = Mock()
        response.json.return_value = []
        response.raise_for_status.return_value = None
        importer.session.get = Mock(return_value=response)

        result = importer.import_athletes("event-123")

        self.assertEqual(result, {})
        importer.session.get.assert_called_once_with(
            "http://localhost:8000/api/events/event-123/athletes",
            params={},
            timeout=10,
        )
        self.assertEqual(
            importer.session.headers["Authorization"],
            "Bearer agent-token",
        )


if __name__ == "__main__":
    unittest.main()
