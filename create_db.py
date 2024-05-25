from app import db, app
from models import User  # Ensure all models are imported here

with app.app_context():
    db.create_all()
    print("Database tables created.")

