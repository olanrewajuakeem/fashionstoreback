1. Clone the repository

2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   
venv\Scripts\activate      

3. install dependencies
pip install -r requirements.txt

4. Create .env
 Flask settings
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db

6. Database Setup
flask db init
flask db migrate
flask db upgrade

7. Run the app
flask run


