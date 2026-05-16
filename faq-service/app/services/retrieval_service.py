from app.models.faq_models import db, Chunk, Document
from sqlalchemy import or_
import logging

logger = logging.getLogger(__name__)

class RetrievalService:
    @staticmethod
    def get_top_chunks(user_id: int, question_text: str, limit: int = 3) -> list:
        """
        Retrieve relevant document chunks for a specific user based on keyword matching.
        Enforces security by joining with the Documents table to check uploaded_by.
        """
        try:
            logger.info(f"Performing vector similarity search for user {user_id}")
            from app.utils.embedding_service import EmbeddingService
            query_vector = EmbeddingService.generate_embedding(question_text)

            # Query chunks joined with documents to verify ownership
            query = db.session.query(Chunk.chunk_text)\
                .join(Document, Chunk.document_id == Document.id)\
                .filter(Document.uploaded_by == user_id)\
                .order_by(Chunk.embedding.cosine_distance(query_vector))\
                .limit(limit)

            results = query.all()
            
            if results:
                return [r[0] for r in results]

            # Fallback to keyword search if vector search returns nothing
            keywords = [w.lower() for w in question_text.split() if len(w) > 3]
            if not keywords: keywords = [question_text.lower()]
            filters = [Chunk.chunk_text.ilike(f"%{kw}%") for kw in keywords]
            
            query = db.session.query(Chunk.chunk_text)\
                .join(Document, Chunk.document_id == Document.id)\
                .filter(Document.uploaded_by == user_id)\
                .filter(or_(*filters))\
                .limit(limit)

            results = query.all()
            return [r[0] for r in results]
        except Exception as e:
            # Silently fail retrieval but log it (RAG should be resilient)
            import logging
            logging.getLogger(__name__).error(f"Retrieval error: {e}")
            return []
