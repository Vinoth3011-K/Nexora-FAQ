import logging
from typing import Dict, Any
from django.conf import settings
from apps.knowledge_base.services.vector_search import VectorSearchService
from apps.chatbot.services.llm_provider import get_llm_provider, BaseLLMProvider

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE = (
    "I couldn't find enough information in our company FAQ knowledge base to answer that question. "
    "Please contact our support team at support@nexora-example.com or reach out via live chat during business hours."
)


class RAGService:
    def __init__(
        self, 
        vector_search_service: VectorSearchService = None, 
        llm_provider: BaseLLMProvider = None
    ):
        self.vector_search = vector_search_service or VectorSearchService()
        self.llm_provider = llm_provider or get_llm_provider()
        self.similarity_threshold = float(getattr(settings, 'RAG_SIMILARITY_THRESHOLD', 0.25))

    def answer_question(self, question: str, conversation_history: list = None) -> Dict[str, Any]:
        clean_question = question.strip() if question else ""
        if not clean_question:
            return {
                'answer': "Please ask a question and I'll be happy to help!",
                'sources': [],
                'matched': False,
                'status': 'error',
            }

        history = conversation_history or []

        try:
            retrieved_chunks = self.vector_search.search(clean_question)
        except Exception as e:
            logger.error(f"Error during vector retrieval: {e}", exc_info=True)
            retrieved_chunks = []

        sufficient_chunks = [
            chunk for chunk in retrieved_chunks 
            if chunk.get('relevance_score', 0.0) >= self.similarity_threshold
        ]

        # If primary search has low relevance, attempt follow-up search with previous user query
        if not sufficient_chunks and history:
            last_user_query = next(
                (turn['text'].strip() for turn in reversed(history) if turn.get('sender') == 'user' and turn.get('text')),
                None,
            )

            if last_user_query and last_user_query.lower() != clean_question.lower():
                try:
                    followup_chunks = self.vector_search.search(f"{last_user_query} {clean_question}")
                    sufficient_chunks = [
                        c for c in followup_chunks 
                        if c.get('relevance_score', 0.0) >= self.similarity_threshold
                    ]
                except Exception as e:
                    logger.error(f"Error during contextual follow-up retrieval: {e}", exc_info=True)

        context_blocks = []
        sources = []
        seen_faq_ids = set()

        for idx, chunk in enumerate(sufficient_chunks, start=1):
            context_blocks.append(f"--- Document Context #{idx} ---\n{chunk['text']}")

            faq_id = chunk.get('faq_id')
            if faq_id and faq_id not in seen_faq_ids:
                seen_faq_ids.add(faq_id)
                sources.append({
                    'faq_id': faq_id,
                    'question': chunk.get('title') or chunk.get('text', '')[:60],
                    'category': chunk.get('category'),
                    'relevance_score': round(float(chunk.get('relevance_score', 0.0)), 4),
                })
            elif not faq_id and chunk.get('document_id'):
                sources.append({
                    'document_id': chunk.get('document_id'),
                    'title': chunk.get('title', 'Document'),
                    'relevance_score': round(float(chunk.get('relevance_score', 0.0)), 4),
                })

        sources.sort(key=lambda s: s.get('relevance_score', 0.0), reverse=True)
        assembled_context = "\n\n".join(context_blocks)

        has_sufficient_context = len(sufficient_chunks) > 0
        has_relevant_history = len(history) > 0

        if not has_sufficient_context and not has_relevant_history:
            return {
                'answer': FALLBACK_MESSAGE,
                'sources': [],
                'matched': False,
                'status': 'success',
            }

        try:
            generated_answer = self.llm_provider.generate_response(
                clean_question, 
                assembled_context, 
                conversation_history=history,
            )
        except Exception as e:
            logger.error(f"Error during LLM generation: {e}", exc_info=True)
            return {
                'answer': "Our AI support service is momentarily experiencing high demand. Please try again in a moment or contact support@nexora-example.com.",
                'sources': sources,
                'matched': has_sufficient_context,
                'status': 'partial_failure',
            }

        return {
            'answer': generated_answer,
            'sources': sources,
            'matched': has_sufficient_context or has_relevant_history,
            'status': 'success',
        }
