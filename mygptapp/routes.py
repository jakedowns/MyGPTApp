import json
import datetime
import redis
from flask_socketio import emit, join_room, leave_room
from mygptapp.actions.receive_user_message import receive_user_message
from flask import jsonify, request, render_template
from mygptapp import db, app, socketio, rules
from mygptapp.models import Message, User, Conversation
from mygptapp.schemas import MessageSchema, MessageCreateSchema, OpenAIApiMessageSchema
import threading

connected_clients = set()

# Create a Marshmallow schema for validating and deserializing Messages
message_schema = MessageSchema()

heartbeat_started = 0
heartbeat_time = 5

# every second send a broadcast to all clients
# def send_message():
#     print("current number of clients: ", len(connected_clients))
#     print("current client ids: ", connected_clients)
#     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     socketio.emit('message', {'data': 'Server Heartbeat ' + timestamp }, broadcast=True)
#     threading.Timer(heartbeat_time, send_message).start()

# if(heartbeat_started == 0):
#     threading.Timer(heartbeat_time, send_message).start()

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
    clientid = request.json.get('clientid')

    status_response_obj = receive_user_message({
        "prompt": prompt,
        "convo_id": id,
        "clientid": clientid,
        "_socketio": socketio
    })

    socketio.emit('message', {
        "event":"received",
        "message_id": status_response_obj["message_id"] if "message_id" in status_response_obj else None,
    },room=clientid)

    return jsonify(status_response_obj)

@app.route('/scrape/<url>')
def scrape_url(url):
    from mygptapp.actions.scrape_url import ScrapeURL
    scraper = ScrapeURL(url)
    scraper.scrape_pyppeteer_fg(url)
    return jsonify(scraper.get_response())

@socketio.on('connect')
def handle_connect():
    print('Client connected: '+str(request.sid))
    connected_clients.add(request.sid)
    emit('connect', {'data': 'Connected', 'clientid': request.sid, 'clients': len(connected_clients)}, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    connected_clients.remove(request.sid)
    print('Client disconnected ',request.sid)

@socketio.on('join')
def on_join(data):
    if not 'room' in data:
        emit('message', {
            "event": "error",
            "message": "room is required"
        })
        return
    room = data['room']
    join_room(room)
    print(f'Client {request.sid} joined room "{room}"')
    emit('join_success', {'room': room}, room=room)

@socketio.on('leave')
def on_leave(data):
    # username = data['username']
    room = data['room']
    leave_room(room)
    print(f'Client {request.sid} left room "{room}"')
    # emit('leave', {'clientid': request.sid, 'room': room}, room=room)

@socketio.on('last_message_id')
def on_last_message_id(data):
    if not 'clientid' in data or 'last_message_id' not in data:
        emit('message', {
            "event": "error",
            "message": "clientid and last_message_id are required"
        })
        return
    # check if the client missed any messages
    # if so, send them to the client
    room = data['clientid']
    # get all messages for convo 1
    messages = db.session.query(Message).filter(Message.convo_id == 1).all()
    # get the last message id in the convo
    if len(messages) == 0:
        return
    last_message_id = messages[-1].id
    # compare the last message id in the convo to the last message id the client has
    if last_message_id > data['last_message_id']:
        # if the client missed messages, send them to the client
        emit('message', {
            "event": "missed_messages",
            "messages": [MessageSchema().dump(message) for message in messages]
        }, room=room)

@socketio.on('message')
def handle_message(message):
    print('received message from client ' + str(request.sid) + ': ' + message)

    # req_data = json.loads(message)
    # action = req_data['action']

    # if action == "interrupt_bot":
    #     # get the conversation
    #     conversation = Conversation.query.filter_by(id=1).first()
    #     # set the bot to not hold the lock
    #     conversation.bot_holds_lock = False
    #     # commit the changes
    #     db.session.commit()