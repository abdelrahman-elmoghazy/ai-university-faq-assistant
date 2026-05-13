import logging
logger = logging.getLogger(__name__)

def process_document(payload: dict) -> dict:
    document_id = payload.get("document_id")
    content = payload.get("content", "")
    chunk_size = payload.get("chunk_size", 500)

    chunks = []
    for i in range(0, len(content), chunk_size):
        chunks.append({
            "document_id": document_id,
            "chunk_index": len(chunks),
            "content": content[i:i + chunk_size]
        })

    logger.info(f"Document {document_id} → {len(chunks)} chunks")
    return {"status": "success", "document_id": document_id, "chunks_count": len(chunks)}