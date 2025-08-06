from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import datetime

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(String, default="idle")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, index=True)
    host = Column(String, index=True)
    port = Column(Integer)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
