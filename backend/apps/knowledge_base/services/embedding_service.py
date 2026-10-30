import math
import hashlib
import logging
import re
from typing import List
from django.conf import settings

logger = logging.getLogger(__name__)

STOP_WORDS = {
    'what', 'is', 'how', 'do', 'does', 'did', 'i', 'the', 'a', 'an', 'and', 'or', 
    'of', 'to', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'up', 'about', 
    'into', 'over', 'after', 'make', 'can', 'could', 'would', 'should', 'you', 
    'your', 'we', 'our', 'my', 'me', 'us', 'it', 'its', 'this', 'that', 'these', 
    'those', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had'
}


class BaseEmbeddingProvider:
    """
    Abstract interface for embedding generation.
    """
    def generate_embedding(self, text: str) -> List[float]:
        raise NotImplementedError

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.generate_embedding(t) for t in texts]


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic, word-token-based embedding generator with stop-word filtering.
    Content words contribute deterministic vector components, so overlapping domain terms
    yield proportional cosine similarity without requiring external paid API calls.
    """
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def _hash_token(self, token: str) -> List[float]:
        digest = hashlib.md5(token.encode('utf-8')).digest()
        vec = []
        for i in range(self.dimension):
            byte_val = digest[i % len(digest)]
            # Deterministic projection for this token
            val = math.sin((byte_val + i * 3) * 0.1)
            vec.append(val)
        return vec

    def generate_embedding(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dimension

        clean_text = text.lower()
        all_tokens = re.findall(r'\b[a-z0-9_-]{2,}\b', clean_text)
        
        # Filter stop words to emphasize semantic content terms
        filtered_tokens = [t for t in all_tokens if t not in STOP_WORDS]
        tokens = filtered_tokens if filtered_tokens else all_tokens

        if not tokens:
            tokens = [clean_text.strip()]

        accumulated = [0.0] * self.dimension
        for token in tokens:
            token_vec = self._hash_token(token)
            for i in range(self.dimension):
                accumulated[i] += token_vec[i]

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in accumulated))
        if norm > 0:
            accumulated = [round(v / norm, 6) for v in accumulated]
        return accumulated


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI Embedding Provider using official OpenAI SDK.
    Supports text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002.
    """
    def __init__(self, api_key: str, model: str = 'text-embedding-3-small', dimension: int = 1536):
        if not api_key:
            raise ValueError("OpenAI API key is missing. Set EMBEDDING_API_KEY in .env.")
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, timeout=20.0)
        except ImportError:
            raise ImportError("openai package is not installed. Please install requirements.")

    def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension

        clean_text = text.replace('\n', ' ')
        try:
            response = self.client.embeddings.create(
                input=[clean_text],
                model=self.model
            )
            vec = response.data[0].embedding
            if len(vec) != self.dimension:
                logger.warning(f"Embedding dimension mismatch: expected {self.dimension}, got {len(vec)}")
            return vec
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise RuntimeError(f"Embedding provider error: {str(e)}")

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        cleaned_texts = [t.replace('\n', ' ') for t in texts]
        try:
            response = self.client.embeddings.create(
                input=cleaned_texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            raise RuntimeError(f"Embedding provider batch error: {str(e)}")


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """
    Local Sentence Transformers embedding provider using all-MiniLM-L6-v2 (384 dimensions).
    Runs locally and offline without external paid API calls or API keys.
    """
    _model_instance = None
    _loaded_model_name = None

    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2', dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self.model = self._get_or_load_model(self.model_name)

    @classmethod
    def _get_or_load_model(cls, model_name: str):
        if cls._model_instance is None or cls._loaded_model_name != model_name:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer embedding model: {model_name}")
                cls._model_instance = SentenceTransformer(model_name)
                cls._loaded_model_name = model_name
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer model '{model_name}': {e}", exc_info=True)
                raise RuntimeError(f"SentenceTransformer load failure: {e}")
        return cls._model_instance

    def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension

        clean_text = text.replace('\n', ' ').strip()
        try:
            vec = self.model.encode(clean_text, convert_to_numpy=True).tolist()
            if len(vec) != self.dimension:
                logger.warning(
                    f"SentenceTransformer dimension mismatch: expected {self.dimension}, got {len(vec)}"
                )
            return [round(float(v), 6) for v in vec]
        except Exception as e:
            logger.error(f"SentenceTransformer embedding generation failed: {e}", exc_info=True)
            raise RuntimeError(f"SentenceTransformer embedding error: {e}")

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        cleaned_texts = [t.replace('\n', ' ').strip() if t else "" for t in texts]
        try:
            vecs = self.model.encode(cleaned_texts, convert_to_numpy=True).tolist()
            return [[round(float(v), 6) for v in vec] for vec in vecs]
        except Exception as e:
            logger.error(f"SentenceTransformer batch embedding generation failed: {e}", exc_info=True)
            raise RuntimeError(f"SentenceTransformer batch embedding error: {e}")


class EmbeddingService:
    """
    Central Embedding Service orchestrator.
    Configured via Django settings / environment variables.
    """
    def __init__(self):
        provider_name = getattr(settings, 'EMBEDDING_PROVIDER', 'sentence-transformers').lower()
        self.dimension = int(getattr(settings, 'EMBEDDING_DIMENSION', 384))
        self.model_name = getattr(settings, 'EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        self.api_key = getattr(settings, 'EMBEDDING_API_KEY', '')

        if provider_name in ('sentence-transformers', 'sentence_transformers', 'local', 'huggingface'):
            try:
                self.provider = SentenceTransformerEmbeddingProvider(
                    model_name=self.model_name,
                    dimension=self.dimension
                )
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to MockEmbeddingProvider.")
                self.provider = MockEmbeddingProvider(dimension=self.dimension)
        elif provider_name == 'openai':
            if not self.api_key:
                logger.warning("EMBEDDING_API_KEY is not configured for OpenAI. Falling back to SentenceTransformer.")
                try:
                    self.provider = SentenceTransformerEmbeddingProvider(
                        model_name=self.model_name,
                        dimension=self.dimension
                    )
                except Exception as e:
                    logger.warning(f"SentenceTransformer fallback failed ({e}). Using MockEmbeddingProvider.")
                    self.provider = MockEmbeddingProvider(dimension=self.dimension)
            else:
                self.provider = OpenAIEmbeddingProvider(
                    api_key=self.api_key, 
                    model=self.model_name, 
                    dimension=self.dimension
                )
        elif provider_name == 'mock':
            self.provider = MockEmbeddingProvider(dimension=self.dimension)
        else:
            logger.warning(f"Unknown embedding provider '{provider_name}'. Defaulting to SentenceTransformer.")
            try:
                self.provider = SentenceTransformerEmbeddingProvider(
                    model_name=self.model_name,
                    dimension=self.dimension
                )
            except Exception as e:
                logger.warning(f"SentenceTransformer fallback failed ({e}). Using MockEmbeddingProvider.")
                self.provider = MockEmbeddingProvider(dimension=self.dimension)

    def get_embedding(self, text: str) -> List[float]:
        return self.provider.generate_embedding(text)

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        return self.provider.generate_embeddings_batch(texts)
