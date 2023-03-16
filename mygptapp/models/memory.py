# a data model for the LLM to remember things outside of ephemeral conversations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from mygptapp import db
from datetime import datetime

class Memory(db.Model):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True)
    memory = Column(String(1000), nullable=False)
    created_at = Column(DateTime, nullable=False)

    def __init__(self, memory):
        self.memory = memory
        self.created_at = datetime.now()

    def __repr__(self):
        return f"Memory('{self.memory}', '{self.created_at}')"