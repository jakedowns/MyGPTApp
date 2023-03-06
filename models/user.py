from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from gpt3 import db

class User(db.Model):
    name = "user"
    table_name = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    #messages = relationship("Message", backref="user", lazy="dynamic")
    #todos = relationship("ToDo", back_populates="owner")
