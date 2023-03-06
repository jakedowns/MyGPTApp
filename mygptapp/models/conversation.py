from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from mygptapp import db

class Conversation(db.Model):
    name = "conversation"
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    #user = relationship("User", back_populates="conversations")
    bot_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    #bot = relationship("User", foreign_keys=[bot_id], backref="bot_conversations")
    bot_holds_lock = Column(Boolean, default=False)
    #messages = relationship("Message", back_populates="conversation")