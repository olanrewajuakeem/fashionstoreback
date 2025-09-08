from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_restx import Api
import bcrypt

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fashionstore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
app.config['DEBUG'] = True

# Initialize db
db = SQLAlchemy()
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Debug db initialization
with app.app_context():
    print("DB initialized:", db.session)

restx_api = Api(
    app,
    title='FashionStore API',
    description='API for FashionStore',
    doc='/swagger/',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Enter your Bearer token in the format: Bearer <your-jwt-token>'
        }
    }
)


from models import User
from api_doc import api_doc_bp
from routes import api_ns

restx_api.add_namespace(api_ns, path='/api')
app.register_blueprint(api_doc_bp, url_prefix='/')


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)