from app.db.session import engine, Base
# Import models so SQLAlchemy knows about them before creating tables
from app.models import Organization, User, Document

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init_db()