from flask import Blueprint, request, jsonify, render_template
from rag.graph import build_graph
from database.connection import get_db
from utils.crud import create_chat_entry, get_user_chat_history, create_user, get_user_by_id
from dotenv import load_dotenv
import os
load_dotenv()

PROD_OR_DEV = os.getenv("CURRENT_STATE", "development")

app_routes = Blueprint('app_routes', __name__)

# Compile graph once on startup
rag_graph = build_graph()

@app_routes.route('/', methods=['GET'])
def index():
    with get_db() as db:
        user_id = 1
        user = get_user_by_id(db, user_id)

    if not user and PROD_OR_DEV == "development":
        create_user(db, "Test User", "test@example.com", "password")

    history_objs = get_user_chat_history(db, user_id, limit=50) 
    history = reversed(history_objs) 
    
    return render_template('chat.html', history=history)

@app_routes.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get('query')
    user_id = 1 # Default user
    
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        # 1. Invoke RAG
        # The graph expects a dict with "question"
        result = rag_graph.invoke({"question": user_query})
        answer = result.get("answer", "Sorry, I could not generate an answer.")

        # 2. Save to DB
        db = next(get_db())
        create_chat_entry(db, user_id, user_query, answer)

        return jsonify({'answer': answer})

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500
