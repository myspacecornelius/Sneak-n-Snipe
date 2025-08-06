from sqlalchemy import Column, Integer, String
from database import Base

class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, index=True)
    host = Column(String, index=True)
    port = Column(Integer)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
