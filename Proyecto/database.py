from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models import Base

# Configure engine with proper encoding settings
if DATABASE_URL.startswith("postgresql"):
    # For PostgreSQL, add encoding parameters
    engine = create_engine(
        DATABASE_URL, connect_args={"client_encoding": "utf8", "options": "-c client_encoding=utf8"}
    )
else:
    # For SQLite and other databases
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
