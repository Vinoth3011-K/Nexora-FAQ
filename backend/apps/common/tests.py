from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

class HealthCheckApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_endpoint(self):
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['database'], 'connected')
        self.assertEqual(response.data['service'], 'company-faq-rag-backend')
