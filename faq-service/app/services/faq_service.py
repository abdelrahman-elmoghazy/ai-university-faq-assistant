from flask import request
from app.models.faq_models import db, Question, Answer, AuditLog
import logging
import requests

logger = logging.getLogger(__name__)

class FAQService:
    @staticmethod
    def ask_question(user_id: int, question_text: str, conversation_id: str = None) -> dict:
        try:
            # 1. Save question
            new_question = Question(
                user_id=user_id,
                conversation_id=conversation_id,
                question_text=question_text
            )
            db.session.add(new_question)
            db.session.commit()

            # 2. Call AI Service (mocked or external integration)
            answer_text = FAQService._generate_ai_answer(question_text)

            # 3. Save answer
            new_answer = Answer(
                question_id=new_question.id,
                answer_text=answer_text,
                answer_source='AI Service'
            )
            db.session.add(new_answer)
            db.session.commit()

            # 4. Log audit
            FAQService.log_audit(user_id, 'ask_question', 'success', details={'question_id': new_question.id})

            return {
                'question': new_question.to_dict(),
                'answer': new_answer.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error asking question: {str(e)}")
            FAQService.log_audit(user_id, 'ask_question', 'failed', details={'error': 'Internal server error'})
            raise Exception("Internal server error")

    @staticmethod
    def _generate_ai_answer(question_text: str) -> str:
        # Here we integrate with the AI service safely
        # E.g. requests.post('http://ai_service/generate', json={'prompt': question_text})
        # If it fails, fallback safely
        try:
            return "This is a mock AI response to: " + question_text
        except Exception as e:
            logger.error(f"AI Service failed: {str(e)}")
            return "I'm sorry, I cannot process your request right now. Please try again later."

    @staticmethod
    def get_user_questions(user_id: int) -> list:
        try:
            questions = Question.query.filter_by(user_id=user_id).order_by(Question.created_at.desc()).all()
            return [q.to_dict() for q in questions]
        except Exception as e:
            logger.error(f"Error fetching questions: {str(e)}")
            raise Exception("Internal server error")

    @staticmethod
    def get_question_by_id(user_id: int, question_id: int) -> dict:
        try:
            question = Question.query.filter_by(id=question_id).first()
            if not question:
                return None
            if question.user_id != user_id:
                raise ValueError("Forbidden")
            return question.to_dict()
        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Error fetching question {question_id}: {str(e)}")
            raise Exception("Internal server error")

    @staticmethod
    def get_user_conversations(user_id: int) -> list:
        try:
            # Get unique conversation_ids for the user
            conversations = db.session.query(Question.conversation_id).filter(
                Question.user_id == user_id, 
                Question.conversation_id.isnot(None)
            ).distinct().all()
            return [c[0] for c in conversations]
        except Exception as e:
            logger.error(f"Error fetching conversations: {str(e)}")
            raise Exception("Internal server error")

    @staticmethod
    def log_audit(user_id: int, action: str, status: str, details: dict = None):
        try:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr) if request else '0.0.0.0'
            log = AuditLog(
                user_id=user_id,
                action=action,
                status=status,
                ip_address=ip_address,
                details=str(details) if details else None
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging audit: {str(e)}")
            # Do not rollback or raise here to prevent failing the main transaction if it was successful, 
            # though usually it's better to log within the same transaction.
