from sqlalchemy import func, or_
from mygptapp import app, db
from mygptapp.models import Memory

class Memories:
    def remember(self, memory):
        memory = Memory(memory=memory)
        db.session.add(memory)
        db.session.commit()
        return memory

    def memories_as_message(self, memories):
        message = ""
        for memory in memories:
            message += f"\n- id:{memory.id} {memory.memory}"
        return message

    def memory_as_message(self, memory):
        return f"Memory: {memory.memory}"

    def get_recent_memories(self):
        memories = Memory.query.order_by(Memory.created_at.desc()).limit(10).all()
        return memories

    def recall(self, query):
        if query == "*":
            memories = Memory.query.all()
        elif query == "random":
            memories = Memory.query.order_by(func.random()).limit(1).all()
        else:
            # fuzzy search
            memories = Memory.query.filter(or_(*[Memory.memory.ilike(f'%{word}%') for word in query.split()]))
        return memories