import sys
import os

# Add the backend directory to sys.path so 'app' can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.db import engine, Base
from app.models import Organization, User, Document

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
