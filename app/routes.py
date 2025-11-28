from flask import Blueprint, request, jsonify, render_template, session, Response, stream_with_context, redirect, url_for, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import logging
import os
import json
from threading import Thread
from queue import Queue, Empty
from langchain_core.callbacks import BaseCallbackHandler
from database.connection import get_db
from utils.crud import (
    get_user_by_id, 
    create_user, 
    get_user_chat_history, 
    create_chat_entry, 
    get_session_chat_history,
    authenticate_user,
    get_user_by_email
)
from rag.graph import build_graph
from app.extensions import csrf

logger = logging.getLogger(__name__)

app_routes = Blueprint('app_routes', __name__)
PROD_OR_DEV = os.getenv("CURRENT_STATE", "development")
rag_graph = build_graph()

# Check if React frontend is available
REACT_FRONTEND_EXISTS = os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist'))

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


def login_required(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Check if it's an API request
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('app_routes.login'))
        return f(*args, **kwargs)
    return decorated_function


# ============== API ROUTES FOR REACT FRONTEND ==============
# API routes are exempt from CSRF as they use session-based auth with SameSite cookies

@app_routes.route('/api/login', methods=['POST'])
@csrf.exempt
def api_login():
    """API endpoint for user login."""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Please enter both email and password.'}), 400
    
    with get_db() as db:
        user = authenticate_user(db, email, password)
        
        if user:
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session.permanent = True
            logger.info(f"User {email} logged in successfully")
            return jsonify({
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email
                }
            })
        else:
            logger.warning(f"Failed login attempt for {email}")
            return jsonify({'error': 'Invalid email or password.'}), 401


@app_routes.route('/api/register', methods=['POST'])
@csrf.exempt
def api_register():
    """API endpoint for user registration."""
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not name or not email or not password:
        return jsonify({'error': 'All fields are required.'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400
    
    with get_db() as db:
        existing_user = get_user_by_email(db, email)
        if existing_user:
            return jsonify({'error': 'An account with this email already exists.'}), 400
        
        try:
            user = create_user(db, name, email, password)
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session.permanent = True
            logger.info(f"New user registered: {email}")
            return jsonify({
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email
                }
            })
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return jsonify({'error': 'An error occurred. Please try again.'}), 500


@app_routes.route('/api/logout', methods=['POST'])
@csrf.exempt
def api_logout():
    """API endpoint for user logout."""
    user_email = session.get('user_email', 'unknown')
    session.clear()
    logger.info(f"User {user_email} logged out")
    return jsonify({'success': True})


@app_routes.route('/api/me', methods=['GET'])
@csrf.exempt
def api_me():
    """API endpoint to get current user."""
    if 'user_id' not in session:
        return jsonify(None), 401
    
    with get_db() as db:
        user = get_user_by_id(db, session['user_id'])
        if not user:
            session.clear()
            return jsonify(None), 401
        
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email
        })


@app_routes.route('/api/history', methods=['GET'])
@csrf.exempt
@login_required
def api_history():
    """API endpoint to get chat history."""
    user_id = session.get('user_id')
    
    with get_db() as db:
        history_objs = get_user_chat_history(db, user_id, limit=50)
        history = []
        for entry in reversed(history_objs):
            history.append({'role': 'user', 'content': entry.question})
            history.append({'role': 'assistant', 'content': entry.answer})
        return jsonify(history)


@app_routes.route('/api/chat', methods=['POST'])
@csrf.exempt
@login_required
@limiter.limit("10 per minute")
def api_chat():
    """API endpoint for chat with streaming response."""
    data = request.json
    user_query = data.get('query')
    session_id = data.get('session_id')
    
    user_id = session.get('user_id')
    
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    if not session_id:
        return jsonify({'error': 'No session_id provided'}), 400

    q = Queue()
    handler = StreamHandler(q)

    with get_db() as db:
        session_history = get_session_chat_history(db, session_id, limit=10)
    
    chat_history = []
    for entry in reversed(session_history):
        chat_history.append({"role": "user", "content": entry.question})
        chat_history.append({"role": "assistant", "content": entry.answer})
    
    logger.debug(f"Chat history for session {session_id}: {len(chat_history)} messages")

    def task():
        try:
            result = rag_graph.invoke(
                {"question": user_query, "chat_history": chat_history},
                config={"configurable": {"stream_callback": handler}}
            )
            answer = result.get("answer", "Sorry, I could not generate an answer.")

            if not handler.streamed:
                q.put(answer)

            with get_db() as db:
                create_chat_entry(db, user_id, user_query, answer, session_id)
            
            q.put(None)

        except ValueError as e:
            logger.warning(f"Invalid input: {e}")
            q.put({"error": "Invalid request format"})
            q.put(None)
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            q.put({"error": "An internal error occurred"})
            q.put(None)

    def generator():
        thread = Thread(target=task)
        thread.start()

        while True:
            try:
                token = q.get(timeout=60)
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


# ============== LEGACY TEMPLATE ROUTES ==============
# Only register these if React frontend is NOT available

if not REACT_FRONTEND_EXISTS:
    @app_routes.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle user login (template version)."""
        if 'user_id' in session:
            return redirect(url_for('app_routes.index'))
        
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Please enter both email and password.', 'error')
                return render_template('login.html')
            
            with get_db() as db:
                user = authenticate_user(db, email, password)
                
                if user:
                    session['user_id'] = user.id
                    session['user_name'] = user.name
                    session['user_email'] = user.email
                    session.permanent = True
                    logger.info(f"User {email} logged in successfully")
                    return redirect(url_for('app_routes.index'))
                else:
                    logger.warning(f"Failed login attempt for {email}")
                    flash('Invalid email or password.', 'error')
        
        return render_template('login.html')


    @app_routes.route('/register', methods=['GET', 'POST'])
    def register():
        """Handle user registration (template version)."""
        if 'user_id' in session:
            return redirect(url_for('app_routes.index'))
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not name or not email or not password:
                flash('All fields are required.', 'error')
                return render_template('register.html')
            
            if len(password) < 8:
                flash('Password must be at least 8 characters.', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('register.html')
            
            with get_db() as db:
                existing_user = get_user_by_email(db, email)
                if existing_user:
                    flash('An account with this email already exists.', 'error')
                    return render_template('register.html')
                
                try:
                    user = create_user(db, name, email, password)
                    session['user_id'] = user.id
                    session['user_name'] = user.name
                    session['user_email'] = user.email
                    session.permanent = True
                    logger.info(f"New user registered: {email}")
                    flash('Account created successfully!', 'success')
                    return redirect(url_for('app_routes.index'))
                except Exception as e:
                    logger.error(f"Error creating user: {e}")
                    flash('An error occurred. Please try again.', 'error')
        
        return render_template('register.html')


    @app_routes.route('/logout')
    def logout():
        """Handle user logout."""
        user_email = session.get('user_email', 'unknown')
        session.clear()
        logger.info(f"User {user_email} logged out")
        flash('You have been logged out.', 'success')
        return redirect(url_for('app_routes.login'))


    @app_routes.route('/', methods=['GET'])
    @login_required
    def index():
        """The home page (template version)."""
        user_id = session.get('user_id')
        user_name = session.get('user_name', 'User')
        
        with get_db() as db:
            user = get_user_by_id(db, user_id)
            if not user:
                session.clear()
                return redirect(url_for('app_routes.login'))
            
            history_objs = get_user_chat_history(db, user_id, limit=50) 
            history = reversed(history_objs) 
        
        return render_template('chat.html', history=history, user_name=user_name)


    @app_routes.route('/chat', methods=['POST'])
    @login_required
    @limiter.limit("10 per minute")
    def chat():
        """The main chat endpoint (template version)."""
        data = request.json
        user_query = data.get('query')
        session_id = data.get('session_id')
        
        user_id = session.get('user_id')
        
        if not user_query:
            return jsonify({'error': 'No query provided'}), 400
        
        if not session_id:
            return jsonify({'error': 'No session_id provided'}), 400

        q = Queue()
        handler = StreamHandler(q)

        with get_db() as db:
            session_history = get_session_chat_history(db, session_id, limit=10)
        
        chat_history = []
        for entry in reversed(session_history):
            chat_history.append({"role": "user", "content": entry.question})
            chat_history.append({"role": "assistant", "content": entry.answer})
        
        logger.debug(f"Chat history for session {session_id}: {len(chat_history)} messages")

        def task():
            try:
                result = rag_graph.invoke(
                    {"question": user_query, "chat_history": chat_history},
                    config={"configurable": {"stream_callback": handler}}
                )
                answer = result.get("answer", "Sorry, I could not generate an answer.")

                if not handler.streamed:
                    q.put(answer)

                with get_db() as db:
                    create_chat_entry(db, user_id, user_query, answer, session_id)
                
                q.put(None)

            except ValueError as e:
                logger.warning(f"Invalid input: {e}")
                q.put({"error": "Invalid request format"})
                q.put(None)
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                q.put({"error": "An internal error occurred"})
                q.put(None)

        def generator():
            thread = Thread(target=task)
            thread.start()

            while True:
                try:
                    token = q.get(timeout=60)
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
