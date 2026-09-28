from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

from config.config_file import DATABASE_FILE

Base = declarative_base()
engine = create_engine(DATABASE_FILE, connect_args={"check_same_thread": False},
                       poolclass=StaticPool, echo=False)
