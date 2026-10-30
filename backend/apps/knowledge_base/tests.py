from django.test import TestCase
from apps.faqs.models import FAQ
from apps.knowledge_base.models import DocumentChunk
from apps.knowledge_base.services.chunker import TextChunker
from apps.knowledge_base.services.embedding_service import MockEmbeddingProvider
from apps.knowledge_base.services.ingestion_service import IngestionService
from apps.knowledge_base.services.vector_search import VectorSearchService, cosine_similarity

class TextChunkerTests(TestCase):
    def test_chunking_short_text(self):
        chunker = TextChunker(chunk_size=200, chunk_overlap=30)
        text = "This is a simple short sentence. Another sentence follows it."
        chunks = chunker.split_text(text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['text'], text)

    def test_chunking_multi_sentence_respects_size(self):
        chunker = TextChunker(chunk_size=60, chunk_overlap=15)
        text = "Sentence number one is here. Sentence number two is somewhat longer. Sentence three is right here."
        chunks = chunker.split_text(text)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertLessEqual(c['char_count'], 100)

    def test_empty_text_returns_empty_list(self):
        chunker = TextChunker()
        self.assertEqual(chunker.split_text(""), [])
        self.assertEqual(chunker.split_text("   \n\t  "), [])


class EmbeddingServiceTests(TestCase):
    def test_mock_embedding_dimension_and_determinism(self):
        provider = MockEmbeddingProvider(dimension=1536)
        text = "What are your standard business hours?"
        vec1 = provider.generate_embedding(text)
        vec2 = provider.generate_embedding(text)
        
        self.assertEqual(len(vec1), 1536)
        self.assertEqual(vec1, vec2)

    def test_mock_embedding_different_texts(self):
        provider = MockEmbeddingProvider(dimension=1536)
        vec_hours = provider.generate_embedding("business hours")
        vec_refund = provider.generate_embedding("refund policy")
        self.assertNotEqual(vec_hours, vec_refund)

    def test_cosine_similarity_identical_vectors(self):
        v = [0.6, 0.8]
        score = cosine_similarity(v, v)
        self.assertAlmostEqual(score, 1.0, places=4)

    def test_cosine_similarity_orthogonal_vectors(self):
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        score = cosine_similarity(v1, v2)
        self.assertAlmostEqual(score, 0.0, places=4)


class IngestionAndVectorSearchTests(TestCase):
    def setUp(self):
        self.faq = FAQ.objects.create(
            question="What are your standard business hours?",
            answer="Our customer care teams operate Monday through Friday, 8:00 AM to 8:00 PM Eastern Time.",
            category="General Information",
            keywords=["hours", "schedule", "work"]
        )

    def test_ingestion_creates_chunks(self):
        ingestion = IngestionService()
        chunk_count = ingestion.ingest_faq(self.faq)
        self.assertGreaterEqual(chunk_count, 1)
        self.assertTrue(DocumentChunk.objects.filter(faq=self.faq).exists())

    def test_vector_search_retrieves_relevant_faq(self):
        ingestion = IngestionService()
        ingestion.ingest_faq(self.faq)

        search_service = VectorSearchService()
        results = search_service.search("What are your business hours?")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['faq_id'], self.faq.id)
        self.assertGreater(results[0]['relevance_score'], 0.2)
