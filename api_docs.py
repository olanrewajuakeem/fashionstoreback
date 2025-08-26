from flask_restx import Api, Resource, fields
from flask import Blueprint, request, Response
from routes import signup, login, get_products, add_to_cart, view_cart, remove_from_cart, newsletter, contact, create_product, get_all_products_admin, update_product, delete_product
import logging
import json


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

api_doc_bp = Blueprint('api_doc', __name__)

restx_api = Api(api_doc_bp,
                title='Fashion Store API',
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
                })

@api_doc_bp.before_request
def log_and_fix_auth_header():
    logger.debug("Request headers: %s", dict(request.headers))
    if 'Authorization' in request.headers and not request.headers['Authorization'].startswith('Bearer '):
        logger.debug("Fixing Authorization header: %s", request.headers['Authorization'])
        request.environ['HTTP_AUTHORIZATION'] = f"Bearer {request.headers['Authorization']}"
        logger.debug("Fixed headers: %s", dict(request.headers))

user_model = restx_api.model('User', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

product_model = restx_api.model('Product', {
    'name': fields.String(required=True, description='Product name'),
    'description': fields.String(required=True, description='Product description'),
    'price': fields.Float(required=True, description='Product price'),
    'image_url': fields.String(required=True, description='Product image URL'),
    'stock': fields.Integer(required=True, description='Product stock')
})

cart_model = restx_api.model('Cart', {
    'product_id': fields.Integer(required=True, description='Product ID'),
    'quantity': fields.Integer(required=True, description='Quantity')
})

contact_model = restx_api.model('Contact', {
    'name': fields.String(required=True, description='Contact name'),
    'email': fields.String(required=True, description='Contact email'),
    'message': fields.String(required=True, description='Contact message')
})

newsletter_model = restx_api.model('Newsletter', {
    'email': fields.String(required=True, description='Newsletter email')
})

def handle_response(response):
    logger.debug("Handling response: %s, type: %s", response, type(response))
    if isinstance(response, Response):
        try:
            data = json.loads(response.get_data(as_text=True))
            status_code = response.status_code
            logger.debug("Extracted from Response: data=%s, status=%s", data, status_code)
            return data, status_code
        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", str(e))
            return {"message": "Invalid response format"}, 500
    elif isinstance(response, tuple):
        logger.debug("Response is tuple: %s", response)
        data, status = response[0], response[1] if len(response) > 1 else 200
        if isinstance(data, Response):
            try:
                data = json.loads(data.get_data(as_text=True))
                logger.debug("Extracted from tuple's Response: data=%s, status=%s", data, status)
                return data, status
            except json.JSONDecodeError as e:
                logger.error("JSON decode error in tuple: %s", str(e))
                return {"message": "Invalid response format"}, 500
        return data, status
    else:
        logger.debug("Response is direct data: %s", response)
        return response, 200

@restx_api.route('/signup')
class Signup(Resource):
    @restx_api.expect(user_model)
    @restx_api.doc(responses={201: 'Created', 400: 'Bad Request'})
    def post(self):
        logger.debug("Calling signup endpoint")
        try:
            response = signup()
            return handle_response(response)
        except Exception as e:
            logger.error("Error in signup: %s", str(e))
            return {"message": f"Error: {str(e)}"}, 500

@restx_api.route('/login')
class Login(Resource):
    @restx_api.expect(user_model)
    @restx_api.doc(responses={200: 'Success', 401: 'Unauthorized'})
    def post(self):
        logger.debug("Calling login endpoint")
        response = login()
        return handle_response(response)

@restx_api.route('/products')
class Products(Resource):
    @restx_api.doc(responses={200: 'Success'})
    def get(self):
        logger.debug("Calling get_products endpoint")
        response = get_products()
        return handle_response(response)

@restx_api.route('/cart')
class Cart(Resource):
    @restx_api.expect(cart_model)
    @restx_api.doc(responses={201: 'Created', 400: 'Bad Request'}, security='Bearer')
    def post(self):
        logger.debug("Calling add_to_cart endpoint, Headers: %s", dict(request.headers))
        response = add_to_cart()
        return handle_response(response)

    @restx_api.doc(responses={200: 'Success'}, security='Bearer')
    def get(self):
        logger.debug("Calling view_cart endpoint, Headers: %s", dict(request.headers))
        response = view_cart()
        return handle_response(response)

@restx_api.route('/cart/<int:item_id>')
class CartItem(Resource):
    @restx_api.doc(responses={200: 'Success', 404: 'Not Found'}, security='Bearer')
    def delete(self, item_id):
        logger.debug("Calling remove_from_cart endpoint with item_id: %s, Headers: %s", item_id, dict(request.headers))
        request.view_args = {'item_id': item_id}
        response = remove_from_cart(item_id)
        return handle_response(response)

@restx_api.route('/newsletter')
class Newsletter(Resource):
    @restx_api.expect(newsletter_model)
    @restx_api.doc(responses={201: 'Created', 400: 'Bad Request'})
    def post(self):
        logger.debug("Calling newsletter endpoint")
        response = newsletter()
        return handle_response(response)

@restx_api.route('/contact')
class Contact(Resource):
    @restx_api.expect(contact_model)
    @restx_api.doc(responses={201: 'Created', 400: 'Bad Request'})
    def post(self):
        logger.debug("Calling contact endpoint")
        response = contact()
        return handle_response(response)

@restx_api.route('/admin/products')
class AdminProducts(Resource):
    @restx_api.expect(product_model)
    @restx_api.doc(responses={201: 'Created', 403: 'Forbidden'}, security='Bearer')
    def post(self):
        logger.debug("Calling create_product endpoint, Headers: %s", dict(request.headers))
        response = create_product()
        return handle_response(response)

    @restx_api.doc(responses={200: 'Success', 403: 'Forbidden'}, security='Bearer')
    def get(self):
        logger.debug("Calling get_all_products_admin endpoint, Headers: %s", dict(request.headers))
        response = get_all_products_admin()
        return handle_response(response)

@restx_api.route('/admin/products/<int:product_id>')
class AdminProduct(Resource):
    @restx_api.expect(product_model)
    @restx_api.doc(responses={200: 'Success', 403: 'Forbidden', 404: 'Not Found'}, security='Bearer')
    def put(self, product_id):
        logger.debug("Calling update_product endpoint with product_id: %s, Headers: %s", product_id, dict(request.headers))
        request.view_args = {'product_id': product_id}
        response = update_product(product_id)
        return handle_response(response)

    @restx_api.doc(responses={200: 'Success', 403: 'Forbidden', 404: 'Not Found'}, security='Bearer')
    def delete(self, product_id):
        logger.debug("Calling delete_product endpoint with product_id: %s, Headers: %s", product_id, dict(request.headers))
        request.view_args = {'product_id': product_id}
        response = delete_product(product_id)
        return handle_response(response)

api_ns = restx_api.namespace('api', description='Main API endpoints')