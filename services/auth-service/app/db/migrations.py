from app.db.base import Base
from app.db.session import engine
from app.db.models import User, Role

def run_migrations():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")
