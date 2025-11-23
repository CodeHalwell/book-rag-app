from flask import Blueprint, request, jsonify, render_template, session, Response, stream_with_context
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
import json
from threading import Thread
from queue import Queue, Empty
from langchain_core.callbacks import BaseCallbackHandler
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

class StreamHandler(BaseCallbackHandler):
    def __init__(self, queue):
        self.queue = queue
        self.streamed = False

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.streamed = True
        self.queue.put(token)

@app_routes.route('/', methods=['GET'])
def index():
    """
    The home page. 
    Loads up the chat history and renders the main UI.
    If it's dev mode and no user exists, we create a dummy user so you don't have to login.
    """
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
    """
    The main chat endpoint.
    Handles the user's message, runs the RAG graph, and streams the response back.
    It's a bit complex because of the streaming, but it keeps the UI snappy.
    """
    data = request.json
    user_query = data.get('query')
    session_id = data.get('session_id')
    
    # TODO: Replace with proper session-based auth
    user_id = session.get('user_id', 1)
    
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    if not session_id:
        return jsonify({'error': 'No session_id provided'}), 400

    q = Queue()
    handler = StreamHandler(q)

    def task():
        """
        Worker function that runs in a separate thread.
        It invokes the RAG graph and puts tokens into the queue as they are generated.
        """
        try:
            result = rag_graph.invoke(
                {"question": user_query},
                config={"configurable": {"stream_callback": handler}}
            )
            answer = result.get("answer", "Sorry, I could not generate an answer.")

            # If nothing was streamed (e.g. inappropriate question check blocked it), 
            # stream the answer now
            if not handler.streamed:
                q.put(answer)

            # Save to DB so we remember this conversation later
            with get_db() as db:
                create_chat_entry(db, user_id, user_query, answer, session_id)
            
            q.put(None) # Sentinel for end of stream

        except ValueError as e:
            logger.warning(f"Invalid input: {e}")
            q.put({"error": "Invalid request format"})
            q.put(None)
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            q.put({"error": "An internal error occurred"})
            q.put(None)

    def generator():
        """
        Yields chunks of data from the queue to the client.
        This allows the browser to display the answer piece by piece.
        """
        thread = Thread(target=task)
        thread.start()

        while True:
            try:
                token = q.get(timeout=60) # 60s timeout for generation
                if token is None:
                    break
                
                if isinstance(token, str) and token.startswith("Error:"):
                    yield json.dumps({"error": token.split(":", 1)[1].strip()}) + "\n"
                    break

                yield json.dumps({"answer": token}) + "\n"
            except Empty:
                yield json.dumps({"error": "Timeout waiting for response"}) + "\n"
                break

    return Response(stream_with_context(generator()), mimetype='application/x-ndjson')
