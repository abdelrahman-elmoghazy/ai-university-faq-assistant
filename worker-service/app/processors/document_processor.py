import os
import io
import logging
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from app.utils.encryption import decrypt_file_data
from app.models.faq_models import SessionLocal, Document, Chunk

logger = logging.getLogger(__name__)

class DocumentProcessor:
    @staticmethod
    def process_document(document_id: int):
        db = SessionLocal()
        try:
            # 1. Load metadata
            doc = db.query(Document).filter(Document.id == document_id).first()
            if not doc:
                logger.error(f"Document {document_id} not found in DB")
                return

            doc.upload_status = "processing"
            db.commit()

            # 2. Read encrypted file
            if not os.path.exists(doc.file_path):
                raise FileNotFoundError(f"File not found at {doc.file_path}")

            with open(doc.file_path, "rb") as f:
                encrypted_data = f.read()

            # 3. Decrypt
            plaintext_data = decrypt_file_data(encrypted_data)
            logger.info("document decrypted")

            # 4. Extract Text
            text = DocumentProcessor._extract_text(plaintext_data, doc.file_name)
            if not text:
                raise ValueError("No text could be extracted from document")
            logger.info("text extracted")

            # 5. Chunk
            chunks = DocumentProcessor._chunk_text(text)

            # 6. Save Chunks
            # Clear old chunks if re-processing
            db.query(Chunk).filter(Chunk.document_id == document_id).delete()
            
            from app.utils.embedding_service import EmbeddingService
            for i, chunk_text in enumerate(chunks):
                embedding = EmbeddingService.generate_embedding(chunk_text)
                new_chunk = Chunk(
                    document_id=document_id,
                    chunk_text=chunk_text,
                    chunk_index=i,
                    embedding=embedding,
                    embedding_status="completed"
                )
                db.add(new_chunk)
            logger.info("chunks inserted with embeddings")

            doc.upload_status = "processed"
            db.commit()
            # logger.info(f"Document {document_id} processed successfully: {len(chunks)} chunks created.")

        except Exception as e:
            db.rollback()
            logger.exception(f"Error processing document {document_id}: {e}")
            if doc:
                doc.upload_status = "failed"
                db.commit()
        finally:
            db.close()

    @staticmethod
    def _extract_text(data: bytes, filename: str) -> str:
        ext = os.path.splitext(filename.lower())[1]
        
        if ext == ".txt":
            return data.decode("utf-8", errors="ignore")
        
        elif ext == ".pdf":
            reader = PdfReader(io.BytesIO(data))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        
        elif ext == ".docx":
            doc = DocxDocument(io.BytesIO(data))
            return "\n".join([para.text for para in doc.paragraphs])
        
        return ""

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list:
        """Simple sliding window chunking."""
        if not text:
            return []
        
        # Clean text slightly
        text = " ".join(text.split())
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start += chunk_size - overlap
            
        return chunks
