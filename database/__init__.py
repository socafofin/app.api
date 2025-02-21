from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    load_dotenv()
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
    
    return app