from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from models import User, Product, Cart as CartModel, Contact as ContactModel, Newsletter as NewsletterModel
import bcrypt
from datetime import datetime

api_ns = Namespace('api', description='Main API endpoints')


# API Models (Schemas)

user_model = api_ns.model('UserInput', {
    'username': fields.String(required=False, description='Username (optional, required for signup)'),
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

product_model = api_ns.model('ProductInput', {
    'name': fields.String(required=True, description='Product name'),
    'description': fields.String(required=True, description='Product description'),
    'price': fields.Float(required=True, description='Product price'),
    'image_url': fields.String(required=True, description='Product image URL'),
    'stock': fields.Integer(required=True, description='Product stock'),
    'category': fields.String(required=True, description='Product category')
})

cart_model = api_ns.model('CartInput', {
    'product_id': fields.Integer(required=True, description='Product ID'),
    'quantity': fields.Integer(required=True, description='Quantity')
})

contact_model = api_ns.model('ContactInput', {
    'name': fields.String(required=True, description='Contact name'),
    'email': fields.String(required=True, description='Contact email'),
    'message': fields.String(required=True, description='Contact message')
})

newsletter_model = api_ns.model('NewsletterInput', {
    'email': fields.String(required=True, description='Newsletter email')
})


# Helpers

def is_admin(user_id):
    user = User.query.get(user_id)
    return user.is_admin if user else False



# Auth Routes

@api_ns.route('/signup')
class Signup(Resource):
    @api_ns.expect(user_model)
    @api_ns.doc(responses={201: 'Created', 400: 'Bad Request'})
    def post(self):
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {'message': 'Email and password are required'}, 400

        if User.query.filter_by(email=email).first():
            return {'message': 'Email already exists'}, 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(username=username, email=email, password=hashed_password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()

        return {'message': 'User created successfully'}, 201


@api_ns.route('/login')
class Login(Resource):
    @api_ns.expect(user_model)
    @api_ns.doc(responses={200: 'Success', 401: 'Unauthorized'})
    def post(self):
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return {'message': 'Invalid credentials'}, 401

        access_token = create_access_token(identity=user.id)
        return {'access_token': access_token, 'is_admin': user.is_admin}, 200



# Newsletter Routes

@api_ns.route('/newsletter')
class NewsletterResource(Resource):
    @api_ns.expect(newsletter_model)
    @api_ns.doc(responses={201: 'Created', 400: 'Bad Request'})
    def post(self):
        data = request.get_json()
        email = data.get('email')

        if not email:
            return {'message': 'Email is required'}, 400

        if NewsletterModel.query.filter_by(email=email).first():
            return {'message': 'Email already subscribed'}, 400

        new_subscription = NewsletterModel(email=email, created_at=datetime.utcnow())
        db.session.add(new_subscription)
        db.session.commit()

        return {'message': 'Subscribed to newsletter'}, 201



# Contact Routes

@api_ns.route('/contact')
class ContactResource(Resource):
    @api_ns.expect(contact_model)
    @api_ns.doc(responses={201: 'Created', 400: 'Bad Request'})
    def post(self):
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')

        if not all([name, email, message]):
            return {'message': 'All fields are required'}, 400

        new_contact = ContactModel(name=name, email=email, message=message, created_at=datetime.utcnow())
        db.session.add(new_contact)
        db.session.commit()

        return {'message': 'Message sent successfully'}, 201



# Product Routes

@api_ns.route('/products')
class Products(Resource):
    @api_ns.doc(responses={200: 'Success'}, params={'category': 'Filter products by category'})
    def get(self):
        category = request.args.get('category')
        query = Product.query
        if category:
            query = query.filter_by(category=category)
        products = query.all()
        return [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': p.price,
            'image_url': p.image_url,
            'stock': p.stock,
            'category': p.category
        } for p in products], 200


@api_ns.route('/products/<int:product_id>')
class ProductItem(Resource):
    @api_ns.doc(responses={200: 'Success', 404: 'Not Found'})
    def get(self, product_id):
        product = Product.query.get(product_id)
        if not product:
            return {'message': 'Product not found'}, 404
        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'image_url': product.image_url,
            'stock': product.stock,
            'category': product.category
        }, 200



# Cart Routes

@api_ns.route('/cart')
class Cart(Resource):
    @api_ns.expect(cart_model)
    @api_ns.doc(responses={201: 'Created', 400: 'Bad Request'}, security='Bearer')
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        product = Product.query.get(product_id)
        if not product or product.stock < quantity:
            return {'message': 'Product not available or insufficient stock'}, 400

        cart_item = CartModel.query.filter_by(user_id=user_id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartModel(user_id=user_id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)

        db.session.commit()
        return {'message': 'Added to cart'}, 201

    @api_ns.doc(responses={200: 'Success'}, security='Bearer')
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        cart_items = CartModel.query.filter_by(user_id=user_id).all()
        return [{
            'id': item.id,
            'product_id': item.product_id,
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity,
            'image_url': item.product.image_url,
            'category': item.product.category
        } for item in cart_items], 200


@api_ns.route('/cart/<int:item_id>')
class CartItem(Resource):
    @api_ns.doc(responses={200: 'Success', 404: 'Not Found'}, security='Bearer')
    @jwt_required()
    def delete(self, item_id):
        user_id = get_jwt_identity()
        cart_item = CartModel.query.filter_by(id=item_id, user_id=user_id).first()
        if not cart_item:
            return {'message': 'Item not found in cart'}, 404

        db.session.delete(cart_item)
        db.session.commit()
        return {'message': 'Item removed from cart'}, 200

    @api_ns.expect(cart_model)
    @api_ns.doc(responses={200: 'Success', 400: 'Bad Request', 404: 'Not Found'}, security='Bearer')
    @jwt_required()
    def put(self, item_id):
        user_id = get_jwt_identity()
        cart_item = CartModel.query.filter_by(id=item_id, user_id=user_id).first()
        if not cart_item:
            return {'message': 'Item not found in cart'}, 404

        data = request.get_json()
        quantity = data.get('quantity')
        if not quantity or quantity < 1:
            return {'message': 'Invalid quantity'}, 400

        product = Product.query.get(cart_item.product_id)
        if product.stock < quantity:
            return {'message': 'Insufficient stock'}, 400

        cart_item.quantity = quantity
        db.session.commit()
        return {'message': 'Cart item updated'}, 200



# Admin Product Routes

@api_ns.route('/admin/products')
class AdminProducts(Resource):
    @api_ns.expect(product_model)
    @api_ns.doc(responses={201: 'Created', 403: 'Forbidden'}, security='Bearer')
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return {'message': 'Admin access required'}, 403

        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        price = data.get('price')
        image_url = data.get('image_url')
        stock = data.get('stock')
        category = data.get('category')

        if not all([name, description, price, image_url, stock, category]):
            return {'message': 'All fields are required'}, 400

        new_product = Product(
            name=name,
            description=description,
            price=price,
            image_url=image_url,
            stock=stock,
            category=category
        )
        db.session.add(new_product)
        db.session.commit()

        return {'message': 'Product created'}, 201

    @api_ns.doc(responses={200: 'Success', 403: 'Forbidden'}, security='Bearer')
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return {'message': 'Admin access required'}, 403

        products = Product.query.all()
        return [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': p.price,
            'image_url': p.image_url,
            'stock': p.stock,
            'category': p.category
        } for p in products], 200


@api_ns.route('/admin/products/<int:product_id>')
class AdminProduct(Resource):
    @api_ns.expect(product_model)
    @api_ns.doc(responses={200: 'Success', 403: 'Forbidden', 404: 'Not Found'}, security='Bearer')
    @jwt_required()
    def put(self, product_id):
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return {'message': 'Admin access required'}, 403

        product = Product.query.get(product_id)
        if not product:
            return {'message': 'Product not found'}, 404

        data = request.get_json()
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)
        product.image_url = data.get('image_url', product.image_url)
        product.stock = data.get('stock', product.stock)
        product.category = data.get('category', product.category)

        db.session.commit()
        return {'message': 'Product updated'}, 200

    @api_ns.doc(responses={200: 'Success', 403: 'Forbidden', 404: 'Not Found'}, security='Bearer')
    @jwt_required()
    def delete(self, product_id):
        user_id = get_jwt_identity()
        if not is_admin(user_id):
            return {'message': 'Admin access required'}, 403

        product = Product.query.get(product_id)
        if not product:
            return {'message': 'Product not found'}, 404

        db.session.delete(product)
        db.session.commit()
        return {'message': 'Product deleted'}, 200
