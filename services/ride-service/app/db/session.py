import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.core.config import settings

load_dotenv()

# Database URL - can be configured via environment variables
# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql://localhost:password@postgres:5432/ridedb"
# )
# DATABASE_URL = "postgresql://postgres:password@localhost:5432/ridedb"
DATABASE_URL = "postgresql://postgres:password@postgres:5432/ridedb"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
