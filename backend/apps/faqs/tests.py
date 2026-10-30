from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.faqs.models import FAQ

class FAQApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='staffuser', password='password123', is_staff=True)
        
        self.faq1 = FAQ.objects.create(
            question="What are your standard business hours?",
            answer="We operate Monday to Friday 8:00 AM to 8:00 PM Eastern Time.",
            category="General Information",
            keywords=["hours", "schedule", "work"],
            is_active=True
        )
        self.faq2 = FAQ.objects.create(
            question="What is your refund policy?",
            answer="We offer a 14-day hassle-free money-back guarantee.",
            category="Refunds & Cancellations",
            keywords=["refund", "money back", "cancel"],
            is_active=True
        )
        self.inactive_faq = FAQ.objects.create(
            question="Old discontinued service question?",
            answer="This service is discontinued.",
            category="General Information",
            keywords=["old", "discontinued"],
            is_active=False
        )

    def test_list_active_faqs(self):
        response = self.client.get('/api/v1/faqs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return active FAQs for unauthenticated public
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)
        returned_ids = [item['id'] for item in results]
        self.assertIn(self.faq1.id, returned_ids)
        self.assertNotIn(self.inactive_faq.id, returned_ids)

    def test_faq_detail(self):
        response = self.client.get(f'/api/v1/faqs/{self.faq1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['question'], self.faq1.question)
        self.assertEqual(response.data['category'], self.faq1.category)

    def test_faq_categories_endpoint(self):
        response = self.client.get('/api/v1/faqs/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        categories = response.data['categories']
        self.assertIn('All', categories)
        self.assertIn('General Information', categories)
        self.assertIn('Refunds & Cancellations', categories)

    def test_faq_search_by_question(self):
        response = self.client.get('/api/v1/faqs/search/?q=business+hours')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [])
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.faq1.id)

    def test_faq_search_by_keyword(self):
        response = self.client.get('/api/v1/faqs/search/?q=schedule')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [])
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.faq1.id)

    def test_faq_category_filter(self):
        response = self.client.get('/api/v1/faqs/?category=Refunds+%26+Cancellations')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.faq2.id)

    def test_unauthenticated_cannot_create_faq(self):
        payload = {
            'question': 'Unauthorized new question?',
            'answer': 'Unauthorized answer.',
            'category': 'General'
        }
        response = self.client.post('/api/v1/faqs/', payload, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_authenticated_staff_can_create_faq(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'question': 'Authorized question created by admin?',
            'answer': 'Authorized answer here.',
            'category': 'Products & Services',
            'keywords': ['new', 'product']
        }
        response = self.client.post('/api/v1/faqs/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['question'], payload['question'])
        self.assertTrue(FAQ.objects.filter(question=payload['question']).exists())
