import databases
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from . import settings
from .schemas import UserDB

database = databases.Database(
    settings.SQLALCHEMY_DATABASE_URL + settings.SQLALCHEMY_DBNAME
)
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL + settings.SQLALCHEMY_DBNAME)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
