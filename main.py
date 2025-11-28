from flask import Flask, send_from_directory
from datetime import timedelta
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

def validate_environment():
    """Validate required environment variables."""
    required_vars = [
        "OPENAI_API_KEY",
        "FLASK_SECRET_KEY",
        "VECTOR_STORE_NAME",
        "VECTOR_STORE_DB_PATH"
    ]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    env = os.getenv("CURRENT_STATE", "development")
    if missing:
        if env == "production":
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
        else:
            print(f"⚠️  Warning: Missing env vars: {', '.join(missing)}")

def create_app():
    validate_environment()
    
    # Initialize database tables
    from database.create_user_db import init_db
    init_db()
    
    # Check if React frontend build exists
    frontend_dist = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
    use_react_frontend = os.path.exists(frontend_dist)
    
    if use_react_frontend:
        print("✅ React frontend detected, serving SPA")
        # Serve React frontend
        app = Flask(__name__, 
                    static_folder=frontend_dist,
                    static_url_path='',
                    template_folder='app/templates')
    else:
        print("📄 Using Jinja templates (React frontend not built)")
        # Use Jinja templates
        app = Flask(__name__, 
                    template_folder='app/templates', 
                    static_folder='app/static')
    
    # Secret key validation
    secret_key = os.getenv('FLASK_SECRET_KEY')
    if not secret_key or secret_key == 'your-secret-key-here':
        if os.getenv('CURRENT_STATE') == 'production':
            raise ValueError("FLASK_SECRET_KEY must be set in production")
        print("⚠️  Generating random secret key for development")
        secret_key = secrets.token_hex(32)
    
    app.config['SECRET_KEY'] = secret_key
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Remember login for 7 days
    
    # Enable CSRF protection
    from app.extensions import csrf
    csrf.init_app(app)
    
    # Import routes here to avoid circular import
    from app.routes import app_routes, limiter
    
    # Initialize rate limiter
    limiter.init_app(app)
    
    app.register_blueprint(app_routes)
    
    # If React frontend exists, serve it for non-API routes
    if use_react_frontend:
        @app.route('/')
        @app.route('/<path:path>')
        def serve_react(path=''):
            # Don't intercept API routes or static files
            if path.startswith('api/') or path.startswith('static/'):
                return app.send_static_file(path)
            
            # Serve static files (js, css, etc.)
            file_path = os.path.join(frontend_dist, path)
            if os.path.isfile(file_path):
                return send_from_directory(frontend_dist, path)
            
            # For all other routes, serve index.html (React handles routing)
            return send_from_directory(frontend_dist, 'index.html')
    
    return app

# Create app instance for Flask CLI discovery (flask run)
app = create_app()

if __name__ == '__main__':
    debug = os.getenv('CURRENT_STATE', 'development') != 'production'
    app.run(debug=debug)
