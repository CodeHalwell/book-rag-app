from flask import Blueprint, request, jsonify, render_template, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
from database.connection import get_db
from utils.crud import get_user_by_id, create_user, get_user_chat_history, create_chat_entry
from rag.graph import build_graph

logger = logging.getLogger(__name__)

app_routes = Blueprint('app_routes', __name__)
PROD_OR_DEV = os.getenv("CURRENT_STATE", "development")
rag_graph = build_graph()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app_routes.route('/', methods=['GET'])
def index():
    with get_db() as db:
        # TODO: Replace with proper session-based auth
        user_id = session.get('user_id', 1)
        user = get_user_by_id(db, user_id)

        if not user and PROD_OR_DEV == "development":
            user = create_user(db, "Test User", "test@example.com", "password")
            session['user_id'] = user.id

        history_objs = get_user_chat_history(db, user_id, limit=50) 
        history = reversed(history_objs) 
    
    return render_template('chat.html', history=history)

@app_routes.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    data = request.json
    user_query = data.get('query')
    
    # TODO: Replace with proper session-based auth
    user_id = session.get('user_id', 1)
    
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        result = rag_graph.invoke({"question": user_query})
        answer = result.get("answer", "Sorry, I could not generate an answer.")

        with get_db() as db:
            create_chat_entry(db, user_id, user_query, answer)

        return jsonify({'answer': answer})

    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        return jsonify({'error': 'Invalid request format'}), 400
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred'}), 500
