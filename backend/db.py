import psycopg2
from psycopg2.extras import RealDictCursor

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from models.user import UserORM

Base = declarative_base()

DATABASE_URL = "postgresql+psycopg2://user:password@tracker_postgres/db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Функция подключения к базе
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(db: Session, username: str):
    return db.query(UserORM).filter(UserORM.username == username).first()