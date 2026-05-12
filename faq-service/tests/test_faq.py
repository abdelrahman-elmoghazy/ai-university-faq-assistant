import pytest
from flask import Flask
from app import create_app
from app.models.faq_models import db
import jwt
from config.settings import get_config

@pytest.fixture
def app():
    # Use testing config
    import os
    os.environ['FLASK_ENV'] = 'testing'
    app = create_app()
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def valid_token(app):
    payload = {
        'user_id': 1,
        'username': 'testuser',
        'roles': ['user']
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config.get('JWT_ALGORITHM', 'HS256'))

@pytest.fixture
def auth_headers(valid_token):
    return {
        'Authorization': f'Bearer {valid_token}',
        'Content-Type': 'application/json'
    }

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_ask_question_no_auth(client):
    response = client.post('/api/faq/ask', json={'question_text': 'What is AI?'})
    assert response.status_code == 401

def test_ask_question_empty_payload(client, auth_headers):
    response = client.post('/api/faq/ask', json={}, headers=auth_headers)
    assert response.status_code == 400
    assert 'Missing question_text' in response.json['message']

def test_ask_question_success(client, auth_headers):
    response = client.post('/api/faq/ask', json={'question_text': 'What is AI?'}, headers=auth_headers)
    assert response.status_code == 201
    data = response.json
    assert 'question' in data
    assert 'answer' in data
    assert data['question']['question_text'] == 'What is AI?'
    assert data['question']['user_id'] == 1

def test_get_questions(client, auth_headers):
    # First, create a question
    client.post('/api/faq/ask', json={'question_text': 'What is AI?'}, headers=auth_headers)
    
    # Then get questions
    response = client.get('/api/faq/questions', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    assert len(data['questions']) == 1
    assert data['questions'][0]['question_text'] == 'What is AI?'

def test_get_question_by_id_success(client, auth_headers):
    # First, create a question
    res = client.post('/api/faq/ask', json={'question_text': 'What is AI?'}, headers=auth_headers)
    question_id = res.json['question']['id']
    
    response = client.get(f'/api/faq/questions/{question_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['question']['id'] == question_id

def test_get_question_by_id_forbidden(client, app):
    # First user creates question
    payload1 = {'user_id': 1, 'username': 'testuser'}
    token1 = jwt.encode(payload1, app.config['JWT_SECRET_KEY'], algorithm=app.config.get('JWT_ALGORITHM', 'HS256'))
    headers1 = {'Authorization': f'Bearer {token1}', 'Content-Type': 'application/json'}
    res = client.post('/api/faq/ask', json={'question_text': 'What is AI?'}, headers=headers1)
    question_id = res.json['question']['id']
    
    # Second user tries to access
    payload2 = {'user_id': 2, 'username': 'anotheruser'}
    token2 = jwt.encode(payload2, app.config['JWT_SECRET_KEY'], algorithm=app.config.get('JWT_ALGORITHM', 'HS256'))
    headers2 = {'Authorization': f'Bearer {token2}', 'Content-Type': 'application/json'}
    
    response = client.get(f'/api/faq/questions/{question_id}', headers=headers2)
    assert response.status_code == 403
    assert 'Forbidden' in response.json['error']

def test_oversized_payload(client, auth_headers):
    long_question = "A" * 2000
    response = client.post('/api/faq/ask', json={'question_text': long_question}, headers=auth_headers)
    assert response.status_code == 400
    assert 'less than 1000' in response.json['message']
