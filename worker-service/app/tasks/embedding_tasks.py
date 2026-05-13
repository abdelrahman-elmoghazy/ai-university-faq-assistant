import logging, hashlib
logger = logging.getLogger(__name__)

def generate_embedding(payload: dict) -> dict:
    chunk_id = payload.get("chunk_id")
    content = payload.get("content", "")
    # Dummy embedding — استبدله بـ model حقيقي لو عندك
    embedding = [float(int(c, 16)) / 255 for c in hashlib.md5(content.encode()).hexdigest()]
    logger.info(f"Embedding generated for chunk {chunk_id}")
    return {"status": "success", "chunk_id": chunk_id}