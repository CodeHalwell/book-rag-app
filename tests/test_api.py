"""Tests for API endpoints."""
import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from app.py directly, assuming it's in the root
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", project_root / "app.py")
app_module = importlib.util.module_from_spec(spec)
sys.modules["app_module"] = app_module
# Hack to make "app" a package so "from app.routes" works inside app.py
import app
sys.modules["app"] = app
spec.loader.exec_module(app_module)
create_app = app_module.create_app

@pytest.fixture
def client():
    # Set template folder explicitly to app/templates
    app = create_app()
    app.template_folder = str(project_root / "app" / "templates")
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