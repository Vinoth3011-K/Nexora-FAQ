from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.conversations.models import Conversation, Message

User = get_user_model()

class ConversationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testconv@nexora.com', email='testconv@nexora.com', password='password123')
        self.client.force_authenticate(user=self.user)
        self.conversation = Conversation.objects.create(
            user=self.user,
            title="Billing inquiry",
            session_id="session-xyz"
        )
        self.msg1 = Message.objects.create(
            conversation=self.conversation,
            sender='user',
            text='Can I update invoice details?'
        )
        self.msg2 = Message.objects.create(
            conversation=self.conversation,
            sender='assistant',
            text='Yes, workspace admins can update invoice details anytime.',
            category='Pricing & Payments'
        )

    def test_list_conversations(self):
        response = self.client.get('/api/v1/conversations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_filter_conversations_by_session_id(self):
        response = self.client.get('/api/v1/conversations/?session_id=session-xyz')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['session_id'], 'session-xyz')

    def test_retrieve_conversation_details(self):
        response = self.client.get(f'/api/v1/conversations/{self.conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Billing inquiry')
        self.assertEqual(len(response.data['messages']), 2)

    def test_clear_conversation(self):
        response = self.client.post(f'/api/v1/conversations/{self.conversation.id}/clear/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.messages.count(), 0)

    def test_delete_conversation(self):
        response = self.client.delete(f'/api/v1/conversations/{self.conversation.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Conversation.objects.filter(id=self.conversation.id).exists())
