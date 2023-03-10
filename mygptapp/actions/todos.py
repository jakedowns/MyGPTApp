from mygptapp import app, db
from mygptapp.models import Todo

class Todos:
    def get_todos_as_message(self) -> str:
        todos = self.get_todos()
        message = ""
        i = 1
        for todo in todos:
            message += f"\n- {'[x]' if todo.completed else '[ ]'} `{todo.id}` {'~~' if todo.completed else ''}{todo.title}{'~~' if todo.completed else ''}"
            i += 1
        return message

    def get_todos(self):
        # sorted by completed, then by id
        todos = Todo.query.order_by(Todo.completed.asc(), Todo.id.asc()).all()
        return todos

    def add_todo(self, title):
        todo = Todo(title=title)
        db.session.add(todo)
        db.session.commit()
        return todo

    def remove_todo(self, id):
        todo = Todo.query.filter_by(id=id).first()
        db.session.delete(todo)
        db.session.commit()
        return todo

    def toggle_todo(self, id):
        todo = Todo.query.filter_by(id=id).first()
        todo.completed = not todo.completed
        db.session.commit()
        return todo

    def update_todo(self, id, title):
        todo = Todo.query.filter_by(id=id).first()
        todo.title = title
        db.session.commit()
        return todo