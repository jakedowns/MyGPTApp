from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from mygptapp import db

class Message(db.Model):
    name = "message"
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String)
    content = Column(String)
    created_at = db.Column(db.DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    #user = relationship("User", backref="messages")
    convo_id = Column(Integer, ForeignKey("conversations.id"))
    #conversation = relationship("Conversation", back_populates="messages")
    is_inner_thought = Column(Boolean, default=False)

    def __repr__(self):
        return f'<Message {self.id}: {self.content}>'

    @classmethod
    def get_recent_messages(cls, session, convo_id, num_messages=10):
        query = session.query(cls).\
            join(cls.conversation).\
            filter(cls.convo_id == convo_id).\
            order_by(cls.created_at.desc()).\
            limit(num_messages)

        recent_messages = query.all()

        return recent_messages