import json
import datetime
from flask import jsonify, request, render_template
from mygptapp import db, app, rules
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

    if prompt.strip() == "/clear":
        # delete all messages for conversation id=1 and return success
        db.session.query(Message).filter(Message.convo_id == id).delete()
        db.session.commit()
        return jsonify({"success": True})

    bot = User.query.filter_by(username="bot").first()
    jakedowns = User.query.filter_by(username="jakedowns").first()
    conversation = Conversation.query.filter_by(id=1).first()

    # insert the user message in the db
    input = {
        "role": "user",
        "content": prompt,
        "user_id": jakedowns.id,
        "convo_id": 1,
        "is_inner_thought": False
    }

    schema = MessageCreateSchema()
    message_data = schema.load(input)
    message = Message(**message_data)
    db.session.add(message)
    db.session.commit()

    # get 10 most recent messages from db for current convo (temp hard-coded to id=1)
    recent_messages = db.session.query(Message).filter(Message.convo_id == 1).order_by(Message.id.desc()).limit(10).all()
    #reverse the order of the messages
    recent_messages = recent_messages[::-1]
    recent_messages = [OpenAIApiMessageSchema().dump(message) for message in recent_messages]

    print("recent_messages: ", recent_messages)

    # copy by value not by reference
    current_prompt = recent_messages[-1]["content"]

    # add a postscript to the last message
    recent_messages[-1]['content'] += rules.get_postscript()

    from mygptapp import api

    response = api.call_model(recent_messages)

    input = {
        "role": "assistant",
        "content": response['choices'][0]['message']['content'],
        "user_id": bot.id,
        "convo_id": 1,
        "is_inner_thought": False
    }

    # specify the bot holds the lock for the conversation
    conversation.bot_holds_lock = True

    # store the bot's response in the db
    message_data = schema.load(input)
    message = Message(**message_data)
    db.session.add(message)
    db.session.commit()

    # TODO: make this use queues and websockets
    # for now we just loop over them until we reach a response or an error or MAX_ATTEMPTS

    response_arr = [response]

    from mygptapp.actions import Actions
    actions = Actions()

    attempts = 0
    MAX_ATTEMPTS = 5
    while attempts < MAX_ATTEMPTS:
        response_arr = actions.process_latest_actions_in_response_arr(conversation, current_prompt, response_arr, attempts, MAX_ATTEMPTS)
        attempts+=1
        # if any of the actions in the response_arr are "respond" or start with "Error Encountered" then we can break out of the loop
        for response in response_arr:
            actions_array = []
            try:
                actions_array = actions.get_actions_from_response(response)
            except Exception as e:
                print("error getting actions from response: ", response)
                response_text = response['choices'][0]['message']['content']
                if response_text.strip().startswith("Error Encountered"):
                    attempts = MAX_ATTEMPTS
                    break
            for action in actions_array:
                # if action is a string for some reason, then we can break out of the loop
                if isinstance(action, str):
                    attempts = MAX_ATTEMPTS
                    break
                if "action" in action and action["action"] == "final_response":
                    print("breaking out of loop")
                    attempts = MAX_ATTEMPTS
                    break



    return jsonify(response_arr)


