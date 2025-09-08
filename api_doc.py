from flask import Blueprint, request
from flask_restx import Api
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

api_doc_bp = Blueprint('api_doc', __name__)

restx_api = Api(
    api_doc_bp,
    title='FashionStore API',
    description='API for a fashion store with user auth, products, cart, and admin features',
    doc='/swagger/',
    security=[{'Bearer': []}],
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Enter your Bearer token in the format: Bearer <your-jwt-token>'
        }
    }
)

@api_doc_bp.before_request
def log_and_fix_auth_header():
    logger.debug("Request headers: %s", dict(request.headers))
    if 'Authorization' in request.headers and not request.headers['Authorization'].startswith('Bearer '):
        logger.debug("Fixing Authorization header: %s", request.headers['Authorization'])
        request.environ['HTTP_AUTHORIZATION'] = f"Bearer {request.headers['Authorization']}"
        logger.debug("Fixed headers: %s", dict(request.headers))

from routes import api_ns

restx_api.add_namespace(api_ns, path='/api')