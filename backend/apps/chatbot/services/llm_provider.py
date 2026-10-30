import logging
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Nexora Assistant, a friendly, intelligent, and helpful AI support assistant for Nexora Technologies.
Your goal is to converse naturally and warmly with users—just like ChatGPT—while remaining strictly accurate and faithful to Nexora's verified company documents.

Communication & Tone Guidelines:
- Conversational & Natural: Speak like a helpful, friendly human expert. Be warm, approachable, and direct. Never use stiff or robotic phrases like "Based on the retrieved context provided above..." or "According to Document Context #1...".
- Direct Answer First: Address the user's specific question directly in your very first sentence.
- Adaptive Length: Keep responses concise for quick or simple questions (1-3 sentences) and provide structured, detailed answers only when the topic requires it.
- Clean Formatting: Use simple formatting. Use bold text for key terms and bullet points only when listing multiple distinct items. Avoid unnecessary markdown headings (###), excessive dividers, or repetitive boilerplate.
- Context & Follow-Up Awareness: Pay close attention to the conversation history. When a user asks follow-up questions (e.g., "Can I get a refund after 10 days?", "Can you explain that in simple words?"), understand what they are referring to from previous turns and respond seamlessly without restarting the conversation.

Knowledge & Grounding Rules:
1. The company documents provided under "Verified Company Context" are your single source of truth for company facts, policies, pricing, numbers, features, and dates.
2. NEVER invent or assume rules, pricing, refund windows, subscription tiers, SLA numbers, or policies not present in the context.
3. If the user asks about a policy or topic that is NOT covered in the verified company context:
   - Honestly and clearly state what you know, and politely explain that you don't have verified details on that specific point.
   - Never guess or pretend a policy is verified when it isn't.
   - Offer the user a helpful path forward (such as contacting support@nexora-example.com or live chat).
4. If the user asks to simplify, rephrase, or explain something from the previous conversation, explain it clearly in simple, everyday words using the facts already established.
"""


def build_chat_messages(question: str, retrieved_context: str, conversation_history: list = None) -> list:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if retrieved_context and retrieved_context.strip():
        messages.append({
            "role": "system",
            "content": f"Verified Company Context:\n{retrieved_context.strip()}"
        })
    else:
        messages.append({
            "role": "system",
            "content": "Verified Company Context: [No new company documents retrieved for this specific message. Rely on established conversation history if this is a follow-up or clarification; otherwise explain what needs confirmation.]"
        })

    if conversation_history:
        for turn in conversation_history:
            role = "user" if turn.get('sender') == 'user' else "assistant"
            content = (turn.get('text') or '').strip()
            if content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": question})
    return messages


def clean_markdown_output(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace('\u202f', ' ')
            .replace('\u00a0', ' ')
            .replace(r'\*', '*')
            .replace(r'\_', '_')
            .replace(r'\#', '#')
            .replace(r'\[', '[')
            .replace(r'\]', ']')
            .strip()
    )


class BaseLLMProvider:
    def generate_response(self, question: str, retrieved_context: str, conversation_history: list = None) -> str:
        raise NotImplementedError


class MockLLMProvider(BaseLLMProvider):
    def generate_response(self, question: str, retrieved_context: str, conversation_history: list = None) -> str:
        q_lower = (question or "").lower()

        if any(w in q_lower for w in ['simple', 'simplify', 'explain that', 'what do you mean', 'in other words']):
            if conversation_history:
                for turn in reversed(conversation_history):
                    if turn.get('sender') == 'assistant' and turn.get('text'):
                        return f"In simple terms: {turn.get('text')}"

        if not retrieved_context or not retrieved_context.strip():
            if conversation_history:
                return (
                    "Based on our earlier discussion, that specific detail isn't fully detailed in our documentation. "
                    "I recommend reaching out to our team at support@nexora-example.com so we can confirm it for you."
                )
            return (
                "I couldn't find enough verified information in our company FAQ to answer that. "
                "Please reach out to our team at support@nexora-example.com for assistance."
            )

        answers = []
        for line in retrieved_context.split('\n'):
            line = line.strip()
            if line.startswith("Answer:"):
                ans_text = line[len("Answer:"):].strip()
                if ans_text and ans_text not in answers:
                    answers.append(ans_text)

        if answers:
            return " ".join(answers)

        return retrieved_context.strip()


class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = 'gpt-4o-mini'):
        if not api_key:
            raise ValueError("OpenAI API key is missing. Configure LLM_API_KEY in .env.")
        self.api_key = api_key
        self.model = model

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, timeout=25.0)
        except ImportError:
            raise ImportError("openai package is not installed.")

    def generate_response(self, question: str, retrieved_context: str, conversation_history: list = None) -> str:
        messages = build_chat_messages(question, retrieved_context, conversation_history)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=700
            )
            return clean_markdown_output(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI completion request failed: {e}")
            raise RuntimeError(f"LLM generation failed: {str(e)}")


class GroqLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = 'openai/gpt-oss-20b'):
        if not api_key:
            raise ValueError("Groq API key is missing. Configure LLM_API_KEY in .env.")
        self.api_key = api_key
        self.model = model

        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key, timeout=25.0)
        except ImportError:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key, 
                    base_url="https://api.groq.com/openai/v1",
                    timeout=25.0
                )
            except ImportError:
                raise ImportError("Neither 'groq' nor 'openai' package is installed.")

    def generate_response(self, question: str, retrieved_context: str, conversation_history: list = None) -> str:
        messages = build_chat_messages(question, retrieved_context, conversation_history)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=700
            )
            return clean_markdown_output(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Groq completion request failed: {e}")
            raise RuntimeError(f"Groq generation failed: {str(e)}")


def get_llm_provider() -> BaseLLMProvider:
    provider_name = getattr(settings, 'LLM_PROVIDER', 'mock').lower()
    api_key = getattr(settings, 'LLM_API_KEY', '')
    model = getattr(settings, 'LLM_MODEL', 'gpt-4o-mini')

    if provider_name == 'openai':
        if not api_key:
            logger.warning("LLM_API_KEY is not set for OpenAI. Falling back to MockLLMProvider.")
            return MockLLMProvider()
        return OpenAILLMProvider(api_key=api_key, model=model)
    elif provider_name == 'groq':
        if not api_key:
            logger.warning("LLM_API_KEY is not set for Groq. Falling back to MockLLMProvider.")
            return MockLLMProvider()
        return GroqLLMProvider(api_key=api_key, model=model)
    else:
        return MockLLMProvider()
