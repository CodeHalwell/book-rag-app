"""Tests for API endpoints."""
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Test that index route returns 200."""
    response = client.get('/')
    assert response.status_code == 200

def test_chat_route_requires_query(client):
    """Test that chat route requires a query."""
    response = client.post('/chat', json={})
    assert response.status_code == 400

def test_chat_route_with_valid_query(client):
    """Test that chat route processes valid queries."""
    response = client.post('/chat', json={'query': 'Test question'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'answer' in data

def test_chat_route_invalid_json(client):
    """Test that invalid JSON is handled."""
    response = client.post('/chat', data='invalid json', content_type='application/json')
    assert response.status_code in [400, 500]