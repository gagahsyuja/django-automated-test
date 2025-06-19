from django.test import TestCase
from ninja.testing import TestClient
from simplelms.urls import api

class HelloTest(TestCase):
    def test_hello(self):
        response = self.client.get("/api/v1/hello/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"msg": "Hello World"})
