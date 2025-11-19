from flask import Flask
from app.routes import app_routes
import os
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    app.register_blueprint(app_routes)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)