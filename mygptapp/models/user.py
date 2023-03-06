from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from mygptapp import db

class User(db.Model):
    name = "user"
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    #messages = relationship("Message", backref="user", lazy="dynamic")
    #todos = relationship("ToDo", back_populates="owner")
    #conversations = relationship("Conversation", back_populates="user")
