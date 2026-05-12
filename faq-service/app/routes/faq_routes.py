from flask import Blueprint
from app.controllers.faq_controller import FAQController
from app.middleware.auth_middleware import token_required
from app.validators.faq_validators import validate_question_payload

faq_bp = Blueprint('faq', __name__)

@faq_bp.route('/ask', methods=['POST'])
@token_required
@validate_question_payload
def ask_question():
    return FAQController.ask_question()

@faq_bp.route('/questions', methods=['GET'])
@token_required
def get_questions():
    return FAQController.get_questions()

@faq_bp.route('/questions/<int:question_id>', methods=['GET'])
@token_required
def get_question(question_id):
    return FAQController.get_question(question_id)

@faq_bp.route('/conversations', methods=['GET'])
@token_required
def get_conversations():
    return FAQController.get_conversations()

@faq_bp.route('/history', methods=['GET'])
@token_required
def get_history():
    return FAQController.get_history()
