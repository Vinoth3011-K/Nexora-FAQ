from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.faqs.models import FAQ
from apps.conversations.models import Conversation
from apps.knowledge_base.services.ingestion_service import IngestionService

User = get_user_model()

class ChatAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testchat@nexora.com', email='testchat@nexora.com', password='password123')
        self.client.force_authenticate(user=self.user)
        self.faq = FAQ.objects.create(
            question="What are your standard business hours?",
            answer="Our customer care teams operate Monday through Friday, 8:00 AM to 8:00 PM Eastern Time.",
            category="General Information",
            keywords=["hours", "schedule", "work"],
            is_active=True
        )
        # Ingest into vector store
        ingestion = IngestionService()
        ingestion.ingest_faq(self.faq)

    def test_empty_chat_request_returns_bad_request(self):
        response = self.client.post('/api/v1/chat/', {'question': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_with_relevant_question(self):
        payload = {'question': 'What are your standard business hours?'}
        response = self.client.post('/api/v1/chat/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('8:00 AM to 8:00 PM', response.data['answer'])
        self.assertTrue(response.data['matched'])
        self.assertIsNotNone(response.data.get('conversation_id'))
        self.assertGreaterEqual(len(response.data['sources']), 1)
        self.assertEqual(response.data['sources'][0]['faq_id'], self.faq.id)

    def test_chat_creates_and_persists_conversation(self):
        payload = {'question': 'What are your standard business hours?'}
        response = self.client.post('/api/v1/chat/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conv_id = response.data['conversation_id']
        
        conversation = Conversation.objects.get(id=conv_id)
        self.assertEqual(conversation.messages.count(), 2) # 1 user, 1 assistant

        # Send follow up in same conversation
        followup_payload = {
            'question': 'What are your standard business hours?',
            'conversation_id': conv_id
        }
        resp2 = self.client.post('/api/v1/chat/', followup_payload, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        conversation.refresh_from_db()
        self.assertEqual(conversation.messages.count(), 4) # 2 user, 2 assistant

    def test_unsupported_question_returns_fallback(self):
        payload = {'question': 'How do I bake a chocolate cake with cherries?'}
        response = self.client.post('/api/v1/chat/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['matched'])
        self.assertIn("couldn't find enough information", response.data['answer'])
