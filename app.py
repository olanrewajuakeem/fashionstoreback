# app.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes import api as api_blueprint
from api_docs import api_doc_bp
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
   
    db.init_app(app)
    Migrate(app, db)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
    JWTManager(app)
    

    logger.debug("Registering api_blueprint")
    app.register_blueprint(api_blueprint, url_prefix='/api')
    logger.debug("Registering api_doc_bp")
    app.register_blueprint(api_doc_bp, url_prefix='/api-docs')
    
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)