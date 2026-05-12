from flask import jsonify, request
from app.services.faq_service import FAQService

class FAQController:
    @staticmethod
    def ask_question():
        try:
            user_id = request.user_id
            data = request.sanitized_data
            question_text = data.get('question_text')
            conversation_id = data.get('conversation_id')

            result = FAQService.ask_question(user_id, question_text, conversation_id)
            return jsonify(result), 201
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

    @staticmethod
    def get_questions():
        try:
            user_id = request.user_id
            questions = FAQService.get_user_questions(user_id)
            return jsonify({'questions': questions}), 200
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

    @staticmethod
    def get_question(question_id):
        try:
            user_id = request.user_id
            question = FAQService.get_question_by_id(user_id, question_id)
            if not question:
                return jsonify({'error': 'Resource not found', 'message': 'Question not found'}), 404
            return jsonify({'question': question}), 200
        except ValueError as e:
            return jsonify({'error': 'Forbidden', 'message': 'You do not have access to this resource'}), 403
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

    @staticmethod
    def get_conversations():
        try:
            user_id = request.user_id
            conversations = FAQService.get_user_conversations(user_id)
            return jsonify({'conversations': conversations}), 200
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

    @staticmethod
    def get_history():
        # History is essentially the questions with their answers, which get_questions already returns in the to_dict()
        try:
            user_id = request.user_id
            questions = FAQService.get_user_questions(user_id)
            return jsonify({'history': questions}), 200
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
