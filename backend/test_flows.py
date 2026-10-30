import os
import sys
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.conversations.models import Conversation, Message
from apps.faqs.models import FAQ

User = get_user_model()
test_user, _ = User.objects.get_or_create(username='flow_tester@nexora.com', defaults={'email': 'flow_tester@nexora.com'})
test_user.set_password('password123')
test_user.save()

client = Client(SERVER_NAME='localhost')
client.force_login(test_user)

print("=" * 60)
print("RUNNING COMPREHENSIVE RAG CHATBOT VERIFICATION TEST")
print("=" * 60)

# Initial State
initial_conv_count = Conversation.objects.count()
print(f"[Initial] Total existing conversations in database: {initial_conv_count}")

# -------------------------------------------------------------
# Test 1: Ask a question and verify real answer & sources appear
# -------------------------------------------------------------
print("\n--- Test 1: Ask a question (RAG + Groq) ---")
q1 = "What are your standard business hours?"
res1 = client.post(
    '/api/v1/chat/',
    data=json.dumps({'question': q1}),
    content_type='application/json'
)
assert res1.status_code == 200, f"Expected 200, got {res1.status_code}: {res1.content}"
data1 = res1.json()
conv_id = data1.get('conversation_id')
answer1 = data1.get('answer')
sources1 = data1.get('sources', [])
matched1 = data1.get('matched')

print(f"Status: {res1.status_code}")
print(f"Conversation ID: {conv_id}")
print(f"Answer: {answer1[:120]}...")
print(f"Matched: {matched1}")
print(f"Sources count: {len(sources1)}")
for s in sources1:
    print(f"  - Source ID: {s.get('faq_id') or s.get('id')} | Title: {s.get('question') or s.get('title')} | Score: {s.get('relevance_score')}")

assert conv_id is not None, "conversation_id should not be None"
assert len(answer1) > 0, "Answer should not be empty"
assert len(sources1) > 0, "Sources should be returned for a valid business hours question"
first_source_id = sources1[0].get('faq_id') or sources1[0].get('id')
print(">>> Test 1 PASSED: Real answer and verified sources returned.")

# -------------------------------------------------------------
# Test 2: Open a source by actual FAQ/document ID
# -------------------------------------------------------------
print(f"\n--- Test 2: Open source details for Source #{first_source_id} ---")
res2 = client.get(f'/api/v1/faqs/{first_source_id}/')
assert res2.status_code == 200, f"Expected 200, got {res2.status_code}: {res2.content}"
data2 = res2.json()
print(f"Status: {res2.status_code}")
print(f"Source #{data2.get('id')}")
print(f"Question: {data2.get('question')}")
print(f"Answer: {data2.get('answer')[:120]}...")
print(f"Category: {data2.get('category')}")
assert data2.get('id') == first_source_id, "Source ID should match requested ID"
print(">>> Test 2 PASSED: Source details retrieved accurately with actual ID.")

# -------------------------------------------------------------
# Test 3: Click 'Ask Chatbot about this' -> Follow-up in SAME conversation
# -------------------------------------------------------------
print(f"\n--- Test 3: 'Ask Chatbot about this' follow-up in SAME conversation ({conv_id}) ---")
followup_question = data2.get('question')
res3 = client.post(
    '/api/v1/chat/',
    data=json.dumps({
        'question': followup_question,
        'conversation_id': conv_id
    }),
    content_type='application/json'
)
assert res3.status_code == 200, f"Expected 200, got {res3.status_code}: {res3.content}"
data3 = res3.json()
conv_id_turn2 = data3.get('conversation_id')
print(f"Status: {res3.status_code}")
print(f"Conversation ID returned: {conv_id_turn2}")
print(f"Answer: {data3.get('answer')[:120]}...")
assert conv_id_turn2 == conv_id, f"Conversation ID must be reused! Expected {conv_id}, got {conv_id_turn2}"

conv_obj = Conversation.objects.get(id=conv_id)
messages_count = conv_obj.messages.count()
print(f"Messages in this conversation so far: {messages_count}")
assert messages_count == 4, f"Expected 4 messages (2 user, 2 assistant), got {messages_count}"
print(">>> Test 3 PASSED: Follow-up question submitted into originating conversation, reusing same conversation ID.")

# -------------------------------------------------------------
# Test 4: Send another message and confirm same conversation continues
# -------------------------------------------------------------
print(f"\n--- Test 4: Send 3rd message in same conversation ({conv_id}) ---")
res4 = client.post(
    '/api/v1/chat/',
    data=json.dumps({
        'question': "Can you summarize our discussion about this topic?",
        'conversation_id': conv_id
    }),
    content_type='application/json'
)
assert res4.status_code == 200
data4 = res4.json()
assert data4.get('conversation_id') == conv_id, "Conversation ID must remain identical on 3rd turn"
conv_obj.refresh_from_db()
print(f"Conversation ID: {data4.get('conversation_id')}")
print(f"Answer: {data4.get('answer')[:120]}...")
print(f"Total messages in conversation: {conv_obj.messages.count()}")
assert conv_obj.messages.count() == 6, f"Expected 6 messages, got {conv_obj.messages.count()}"
print(">>> Test 4 PASSED: Conversation continued seamlessly across multiple turns.")

# -------------------------------------------------------------
# Test 5: Verify no new conversation is created during operations
# -------------------------------------------------------------
print("\n--- Test 5: Verify no unexpected conversations were created ---")
final_conv_count = Conversation.objects.count()
print(f"Initial count: {initial_conv_count} | Current count: {final_conv_count}")
# Exactly 1 new conversation should have been created across all 3 turns!
assert final_conv_count == initial_conv_count + 1, (
    f"Expected exactly 1 new conversation created for the 3 messages, but got {final_conv_count - initial_conv_count}"
)

# Also check for empty conversations in database
empty_convs = [c for c in Conversation.objects.all() if c.messages.count() == 0]
print(f"Empty conversations in database: {len(empty_convs)}")
assert len(empty_convs) == 0, f"No empty conversations should exist, found {len(empty_convs)}"
print(">>> Test 5 PASSED: No duplicate or empty conversations created.")

# -------------------------------------------------------------
# Test 6: Verify existing conversations still load after refresh
# -------------------------------------------------------------
print("\n--- Test 6: Verify conversations list & details endpoint (simulating page reload) ---")
res6_list = client.get('/api/v1/conversations/')
assert res6_list.status_code == 200
convs_list = res6_list.json()
# Check results
results = convs_list.get('results', convs_list) if isinstance(convs_list, dict) else convs_list
print(f"Retrieved {len(results)} conversations from list endpoint")
target_conv_in_list = next((c for c in results if str(c.get('id')) == str(conv_id)), None)
assert target_conv_in_list is not None, f"Conversation {conv_id} should appear in conversation list"
print(f"Found conversation in list: {target_conv_in_list.get('title')} (Messages count: {target_conv_in_list.get('message_count')})")

res6_detail = client.get(f'/api/v1/conversations/{conv_id}/')
assert res6_detail.status_code == 200
detail_data = res6_detail.json()
print(f"Detail endpoint retrieved conversation: {detail_data.get('id')}")
print(f"Messages count in detail: {len(detail_data.get('messages', []))}")
assert len(detail_data.get('messages', [])) == 6, f"Expected 6 messages in conversation detail, got {len(detail_data.get('messages', []))}"
print(">>> Test 6 PASSED: Existing conversation and messages load accurately after refresh.")

print("\n" + "=" * 60)
print("ALL 6 TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
