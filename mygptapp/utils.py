from mygptapp import db, socketio
from mygptapp.schemas import FrontendMessageSchema, MessageCreateSchema
from mygptapp.models import Message

def save_and_emit_message(user_id, convo_id, role, content, options={}):
    print("save_and_emit_message ", content, options)

    options["is_inner_thought"] = options["is_inner_thought"] if "is_inner_thought" in options else False

    options["clientid"] = options["clientid"] if "clientid" in options else "broadcast"

    input = {
        "role": role,
        "content": content,
        "user_id": user_id,
        "convo_id": convo_id,
        "is_inner_thought": options["is_inner_thought"]
    }

    # store the bot's response in the db
    schema = MessageCreateSchema()
    message_data = schema.load(input)
    message = Message(**message_data)
    db.session.add(message)
    db.session.commit()

    fe_schema = FrontendMessageSchema()

    # emit the latest response to the client
    socketio.emit('message', {
        "event":"bot_response",
        "message": fe_schema.dump(message)
    },room=options["clientid"])