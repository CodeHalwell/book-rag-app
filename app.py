from flask import Flask
from flask_wtf.csrf import CSRFProtect
# from app.routes import app_routes, limiter
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
    
    app = Flask(__name__)
    
    # Secret key validation
    secret_key = os.getenv('FLASK_SECRET_KEY')
    if not secret_key or secret_key == 'your-secret-key-here':
        if os.getenv('CURRENT_STATE') == 'production':
            raise ValueError("FLASK_SECRET_KEY must be set in production")
        print("⚠️  Generating random secret key for development")
        secret_key = secrets.token_hex(32)
    
    app.config['SECRET_KEY'] = secret_key
    
    # Enable CSRF protection
    CSRFProtect(app)
    
    # Import routes here to avoid circular import
    from app.routes import app_routes, limiter
    
    # Initialize rate limiter
    limiter.init_app(app)
    
    app.register_blueprint(app_routes)
    return app

if __name__ == '__main__':
    app = create_app()
    debug = os.getenv('CURRENT_STATE', 'development') != 'production'
    app.run(debug=debug)