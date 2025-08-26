from app import create_app
from models import db, User
import bcrypt

app = create_app()
with app.app_context():
    email = "admin@example.com"
    password = "admin123"
    email = "admin@exampe.com"
    password = "admin1234"
    if not User.query.filter_by(email=email).first(): 
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        admin = User(email=email, password=hashed_password.decode('utf-8'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully")
    else:
        print("Admin user already exists")