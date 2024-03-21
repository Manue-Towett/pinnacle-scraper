import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

password = urllib.parse.quote_plus("t&fjBze@#8XsW49dZx")

engine = create_engine(f"postgresql://towett:{password}@/postgres")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()