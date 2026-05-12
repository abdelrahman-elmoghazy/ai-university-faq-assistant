import json
from functools import wraps
from flask import request, jsonify

MAX_QUESTION_LENGTH = 1000

def validate_question_payload(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Invalid input', 'message': 'Request must be JSON'}), 400
            
        data = request.get_json()
        question_text = data.get('question_text')
        
        if question_text is None:
            return jsonify({'error': 'Invalid input', 'message': 'Missing question_text'}), 400
            
        if not isinstance(question_text, str):
            return jsonify({'error': 'Invalid input', 'message': 'question_text must be a string'}), 400
            
        question_text = question_text.strip()
        
        if len(question_text) == 0:
            return jsonify({'error': 'Invalid input', 'message': 'question_text cannot be empty'}), 400
            
        if len(question_text) > MAX_QUESTION_LENGTH:
            return jsonify({'error': 'Invalid input', 'message': f'question_text must be less than {MAX_QUESTION_LENGTH} characters'}), 400
            
        # Store sanitized data back in request context
        request.sanitized_data = data
        request.sanitized_data['question_text'] = question_text
        
        return f(*args, **kwargs)
    return decorated
