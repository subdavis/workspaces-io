import databases

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from . import settings
from .schemas import UserDB

# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

database = databases.Database(settings.SQLALCHEMY_DATABASE_URL)
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
