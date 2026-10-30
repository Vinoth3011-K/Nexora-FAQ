import requests
import json

BASE = "http://127.0.0.1:8000/api/v1"

print("--- 1. Testing Health Endpoint ---")
r = requests.get(f"{BASE}/health/")
print("Status:", r.status_code, "Body:", r.json())

print("\n--- 2. Testing FAQ Categories ---")
r = requests.get(f"{BASE}/faqs/categories/")
print("Status:", r.status_code, "Categories:", r.json().get('categories'))

print("\n--- 3. Testing FAQ Search (Query: 'hours') ---")
r = requests.get(f"{BASE}/faqs/search/?q=hours")
print("Status:", r.status_code, "Count:", r.json().get('count'))
if r.json().get('results'):
    first = r.json()['results'][0]
    print(f"Matched FAQ ID: {first['id']} | Question: {first['question']}")

print("\n--- 4. Testing RAG Chat Endpoint (Supported Question) ---")
payload = {"question": "What are your standard business hours?"}
r = requests.post(f"{BASE}/chat/", json=payload)
data = r.json()
print("Status:", r.status_code)
print("Answer:", data.get('answer'))
print("Matched:", data.get('matched'))
print("Conversation ID:", data.get('conversation_id'))
print("Sources:", json.dumps(data.get('sources'), indent=2))

print("\n--- 5. Testing RAG Chat Endpoint (Unsupported Fallback Question) ---")
payload_fallback = {"question": "How do I make chocolate ice cream?"}
r = requests.post(f"{BASE}/chat/", json=payload_fallback)
data_fb = r.json()
print("Status:", r.status_code)
print("Answer:", data_fb.get('answer'))
print("Matched:", data_fb.get('matched'))
print("Sources:", data_fb.get('sources'))

print("\n--- 6. Testing Conversations API ---")
r = requests.get(f"{BASE}/conversations/")
print("Status:", r.status_code, "Total Conversations:", r.json().get('count'))
