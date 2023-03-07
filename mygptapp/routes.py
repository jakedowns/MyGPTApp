import json
import datetime
from flask_socketio import emit
from mygptapp.actions.receive_user_message import receive_user_message
from flask import jsonify, request, render_template
from mygptapp import db, app, socketio, rules
from mygptapp.models import Message, User, Conversation
from mygptapp.schemas import MessageSchema, MessageCreateSchema, OpenAIApiMessageSchema
# from marshmallow import ValidationError

# Create a Marshmallow schema for validating and deserializing Messages
message_schema = MessageSchema()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convo/<id>/messages')
def get_convo_messages(id):
    # get all messages from db for current convo (temp hard-coded to id=1)
    messages = db.session.query(Message).filter(Message.convo_id == id).all()
    # sqla-flask json response
    return [MessageSchema().dump(message) for message in messages]

@app.route('/convo/<id>/message', methods=['POST'])
def post_user_message_to_convo(id):
    prompt = request.json.get('prompt')
    socketio.emit('message', {"event":"received","prompt":prompt})
    status_response_obj = receive_user_message({
        "prompt": prompt,
        "convo_id": id
    })
    return jsonify(status_response_obj)


@socketio.on('connect')
def test_connect():
    emit('connect', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)

    # req_data = json.loads(message)
    # action = req_data['action']

    # if action == "interrupt_bot":
    #     # get the conversation
    #     conversation = Conversation.query.filter_by(id=1).first()
    #     # set the bot to not hold the lock
    #     conversation.bot_holds_lock = False
    #     # commit the changes
    #     db.session.commit()