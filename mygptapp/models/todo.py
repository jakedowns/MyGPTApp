from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from mygptapp import db

class Todo(db.Model):
    name = "todo"
    __table_name__ = "todos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    description = Column(String)
    completed = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"))
    #user = relationship("User", back_populates="todos")
