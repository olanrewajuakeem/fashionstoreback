from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Product, Cart, Contact, Newsletter
import bcrypt
from datetime import datetime

api = Blueprint('api', __name__)


def is_admin(user_id):
    user = User.query.get(user_id)
    return user.is_admin

@api.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    new_user = User(email=email, password=hashed_password.decode('utf-8'))
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token, 'is_admin': user.is_admin}), 200

@api.route('/newsletter', methods=['POST'])
def newsletter():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    
    if Newsletter.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already subscribed'}), 400
    
    new_subscription = Newsletter(email=email)
    db.session.add(new_subscription)
    db.session.commit()
    
    return jsonify({'message': 'Subscribed to newsletter'}), 201

@api.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    
    if not all([name, email, message]):
        return jsonify({'message': 'All fields are required'}), 400
    
    new_contact = Contact(name=name, email=email, message=message)
    db.session.add(new_contact)
    db.session.commit()
    
    return jsonify({'message': 'Message sent successfully'}), 201

@api.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'image_url': p.image_url,
        'stock': p.stock
    } for p in products]), 200

@api.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = Product.query.get(product_id)
    if not product or product.stock < quantity:
        return jsonify({'message': 'Product not available or insufficient stock'}), 400
    
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    return jsonify({'message': 'Added to cart'}), 201

@api.route('/cart', methods=['GET'])
@jwt_required()
def view_cart():
    user_id = get_jwt_identity()
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': item.id,
        'product_id': item.product_id,
        'name': item.product.name,
        'price': item.product.price,
        'quantity': item.quantity,
        'image_url': item.product.image_url
    } for item in cart_items]), 200

@api.route('/cart/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    user_id = get_jwt_identity()
    cart_item = Cart.query.filter_by(id=item_id, user_id=user_id).first()
    if not cart_item:
        return jsonify({'message': 'Item not found in cart'}), 404
    
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Item removed from cart'}), 200

@api.route('/admin/products', methods=['POST'])
@jwt_required()
def create_product():
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    image_url = data.get('image_url')
    stock = data.get('stock')
    
    if not all([name, description, price, image_url, stock]):
        return jsonify({'message': 'All fields are required'}), 400
    
    new_product = Product(name=name, description=description, price=price, image_url=image_url, stock=stock)
    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({'message': 'Product created'}), 201

@api.route('/admin/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'message': 'Admin access required'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)
    product.image_url = data.get('image_url', product.image_url)
    product.stock = data.get('stock', product.stock)
    
    db.session.commit()
    return jsonify({'message': 'Product updated'}), 200

@api.route('/admin/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'message': 'Admin access required'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'}), 200

@api.route('/admin/products', methods=['GET'])
@jwt_required()
def get_all_products_admin():
    user_id = get_jwt_identity()
    if not is_admin(user_id):
        return jsonify({'message': 'Admin access required'}), 403
    
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'image_url': p.image_url,
        'stock': p.stock
    } for p in products]), 200