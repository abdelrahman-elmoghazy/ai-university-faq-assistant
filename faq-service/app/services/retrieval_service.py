from app.models.faq_models import db, Chunk, Document
from sqlalchemy import or_
import logging

logger = logging.getLogger(__name__)

class RetrievalService:
    @staticmethod
    def get_top_chunks(user_id: int, question_text: str, limit: int = 3) -> list:
        """
        Retrieve relevant document chunks for a specific user based on vector or keyword matching.
        Enforces security by joining with the Documents table to check uploaded_by or visibility.
        """
        try:
            # 6. Direct debug query to count available public chunks
            public_chunks_available = db.session.query(db.func.count(Chunk.id))\
                .join(Document, Chunk.document_id == Document.id)\
                .filter(Document.visibility == 'public').scalar() or 0

            logger.info(f"RAG Global Check - User ID: {user_id}, Public Chunks Available: {public_chunks_available}")

            from app.utils.embedding_service import EmbeddingService
            query_vector = EmbeddingService.generate_embedding(question_text)

            cosine_dist = Chunk.embedding.cosine_distance(query_vector)

            # Query chunks joined with documents to verify ownership or public visibility
            # Filter by a cosine distance threshold (e.g. < 0.65) to discard random mock embeddings and trigger fallback
            query = db.session.query(Chunk.chunk_text, Chunk.document_id, Document.visibility, Document.uploaded_by)\
                .join(Document, Chunk.document_id == Document.id)\
                .filter(or_(Document.uploaded_by == user_id, Document.visibility == 'public'))\
                .filter(cosine_dist < 0.65)\
                .order_by((Document.visibility == 'public').desc(), cosine_dist)\
                .limit(limit)

            results = query.all()
            
            # Log debug metrics for vector search
            retrieved_chunks_count = len(results)
            retrieved_public_chunks_count = sum(1 for r in results if r[2] == 'public')
            retrieved_private_chunks_count = sum(1 for r in results if r[2] != 'public')
            document_ids_used = list(set(r[1] for r in results))

            logger.info(f"RAG Vector Search Debug - User ID: {user_id}, Public Chunks Available: {public_chunks_available}, "
                        f"Retrieved Chunks: {retrieved_chunks_count}, Public Chunks: {retrieved_public_chunks_count}, "
                        f"Private Chunks: {retrieved_private_chunks_count}, Doc IDs: {document_ids_used}")

            if results:
                return [r[0] for r in results]

            # Fallback to keyword search if vector search returns nothing (or is filtered out by distance threshold)
            logger.info(f"Vector search returned no close matches. Falling back to keyword search for user {user_id}")
            
            # Extract meaningful query terms from the list
            meaningful_terms = ['public', 'university', 'support', 'office', 'located']
            keywords = [w.lower() for w in question_text.split() if w.lower() in meaningful_terms]
            if not keywords:
                keywords = [w.lower() for w in question_text.split() if len(w) > 3]
            if not keywords:
                keywords = [question_text.lower()]
                
            filters = [Chunk.chunk_text.ilike(f"%{kw}%") for kw in keywords]
            
            # Query keyword matches. Prioritize public exact matches by sorting Document.visibility == 'public' DESC
            query = db.session.query(Chunk.chunk_text, Chunk.document_id, Document.visibility, Document.uploaded_by)\
                .join(Document, Chunk.document_id == Document.id)\
                .filter(or_(Document.uploaded_by == user_id, Document.visibility == 'public'))\
                .filter(or_(*filters))\
                .order_by((Document.visibility == 'public').desc(), Chunk.id.desc())\
                .limit(limit)

            results = query.all()

            # Log debug metrics for keyword search fallback
            retrieved_chunks_count = len(results)
            retrieved_public_chunks_count = sum(1 for r in results if r[2] == 'public')
            retrieved_private_chunks_count = sum(1 for r in results if r[2] != 'public')
            document_ids_used = list(set(r[1] for r in results))

            logger.info(f"RAG Keyword Search Fallback Debug - User ID: {user_id}, Public Chunks Available: {public_chunks_available}, "
                        f"Retrieved Chunks: {retrieved_chunks_count}, Public Chunks: {retrieved_public_chunks_count}, "
                        f"Private Chunks: {retrieved_private_chunks_count}, Doc IDs: {document_ids_used}")

            return [r[0] for r in results]
        except Exception as e:
            # Silently fail retrieval but log it (RAG should be resilient)
            import logging
            logging.getLogger(__name__).error(f"Retrieval error: {e}")
            return []
