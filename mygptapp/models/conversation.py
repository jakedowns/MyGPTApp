from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from mygptapp import db

class Conversation(db.Model):
    name = "conversation"
    table_name = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    #user = relationship("User", back_populates="conversations")
    assistant_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    #assistant = relationship("User", foreign_keys=[assistant_id], backref="assistant_conversations")
    bot_holds_lock = Column(Boolean, default=False)
    #messages = relationship("Message", back_populates="conversation")