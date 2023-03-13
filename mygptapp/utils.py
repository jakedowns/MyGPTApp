from mygptapp import db, socketio
from mygptapp.schemas import FrontendMessageSchema, MessageCreateSchema
from mygptapp.models import Message

def save_and_emit_message(user_id, convo_id, role, content, options={}):
    print("save_and_emit_message ", {"content":content, "options":options})

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

    # emit the latest response to the client
    emit_message(message, options)

# message = {role,content}
def emit_message(message,options={}):
    fe_schema = FrontendMessageSchema()

    # if the message is a string, wrap it
    if isinstance(message, str):
        message = wrap_message_as_bot_message(message)

    options["clientid"] = options["clientid"] if "clientid" in options else "broadcast"
    socketio.emit('message', {
        "event":"bot_response",
        "message": fe_schema.dump(message)
    },room=options["clientid"])

def wrap_message_as_bot_message(message) -> str:
    return {
        "role": "assistant",
        "content": message,
    }