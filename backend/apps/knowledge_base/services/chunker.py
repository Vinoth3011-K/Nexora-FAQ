import re
from typing import List, Dict, Any

class TextChunker:
    """
    Dedicated text chunking service that respects sentence boundaries and paragraph breaks.
    Supports configurable chunk size (in characters or words) and chunk overlap.
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive.")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be non-negative and less than chunk_size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Splits input text into a list of chunk dictionaries containing 'text', 'index', and 'metadata'.
        """
        if not text or not text.strip():
            return []

        clean_text = self._normalize_whitespace(text)
        sentences = self._split_into_sentences(clean_text)

        chunks = []
        current_chunk_sentences = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            
            # If a single sentence exceeds chunk size, split it into pieces
            if sentence_len > self.chunk_size:
                # Flush existing buffer
                if current_chunk_sentences:
                    chunk_str = " ".join(current_chunk_sentences).strip()
                    if chunk_str:
                        chunks.append(self._create_chunk(chunk_str, chunk_index, metadata))
                        chunk_index += 1
                    current_chunk_sentences = []
                    current_length = 0

                sub_chunks = self._split_long_sentence(sentence)
                for sc in sub_chunks:
                    chunks.append(self._create_chunk(sc, chunk_index, metadata))
                    chunk_index += 1
                continue

            if current_length + sentence_len + 1 > self.chunk_size and current_chunk_sentences:
                # Flush current chunk
                chunk_str = " ".join(current_chunk_sentences).strip()
                if chunk_str:
                    chunks.append(self._create_chunk(chunk_str, chunk_index, metadata))
                    chunk_index += 1

                # Calculate overlap: retain sentences from end of current chunk
                overlap_sentences = []
                overlap_len = 0
                for s in reversed(current_chunk_sentences):
                    if overlap_len + len(s) + 1 <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += len(s) + 1
                    else:
                        break

                current_chunk_sentences = overlap_sentences + [sentence]
                current_length = sum(len(s) + 1 for s in current_chunk_sentences)
            else:
                current_chunk_sentences.append(sentence)
                current_length += sentence_len + 1

        if current_chunk_sentences:
            chunk_str = " ".join(current_chunk_sentences).strip()
            if chunk_str:
                chunks.append(self._create_chunk(chunk_str, chunk_index, metadata))

        return chunks

    def _create_chunk(self, text: str, index: int, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        meta = dict(metadata or {})
        return {
            'text': text,
            'index': index,
            'char_count': len(text),
            'metadata': meta
        }

    def _normalize_whitespace(self, text: str) -> str:
        # Normalize carriage returns and multiple spaces
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _split_into_sentences(self, text: str) -> List[str]:
        # Split on sentence terminals while keeping formatting
        parts = re.split(r'(?<=[.!?])\s+|\n\n+', text)
        return [p.strip() for p in parts if p.strip()]

    def _split_long_sentence(self, sentence: str) -> List[str]:
        words = sentence.split(' ')
        sub_chunks = []
        current = []
        curr_len = 0

        for word in words:
            if curr_len + len(word) + 1 > self.chunk_size and current:
                sub_chunks.append(" ".join(current).strip())
                current = [word]
                curr_len = len(word)
            else:
                current.append(word)
                curr_len += len(word) + 1

        if current:
            sub_chunks.append(" ".join(current).strip())
        return sub_chunks
