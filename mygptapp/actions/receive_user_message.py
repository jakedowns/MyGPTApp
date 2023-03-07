from flask import request, jsonify
from mygptapp.models import Message, Conversation, User
from mygptapp.schemas import MessageCreateSchema, OpenAIApiMessageSchema
from mygptapp import db, rules, app, socketio

import threading

def process_user_input(options):
    with app.app_context():
        # jakedowns = User.query.filter_by(username="jakedowns").first()
        bot = User.query.filter_by(username="bot").first()
        conversation = Conversation.query.filter_by(id=1).first()

        # get N most recent messages from db for current convo (temp hard-coded to id=1)
        recent_messages = db.session.query(Message).filter(Message.convo_id == 1).order_by(Message.id.desc()).limit(5).all()
        #reverse the order of the messages
        recent_messages = recent_messages[::-1]
        recent_messages = [OpenAIApiMessageSchema().dump(message) for message in recent_messages]

        # print("recent_messages: ", recent_messages)

        # copy by value not by reference
        current_prompt = recent_messages[-1]["content"]

        # add a system message
        ps_msg = {
            "role": "system",
            "content": rules.get_postscript()
        }
        recent_messages.append(ps_msg)

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
        schema = MessageCreateSchema()
        message_data = schema.load(input)
        message = Message(**message_data)
        db.session.add(message)
        db.session.commit()

        response_arr = [response]

        from mygptapp.actions import Actions
        actions = Actions()

        attempts = 0
        MAX_ATTEMPTS = 5
        while attempts < MAX_ATTEMPTS:
            response_arr = actions.process_latest_actions_in_response_arr(conversation, current_prompt, response_arr, attempts, MAX_ATTEMPTS)

            print("attempt ", str(attempts) + " of " + str(MAX_ATTEMPTS))
            print("response_arr length: ", len(response_arr))

            # emit the latest response to the client
            socketio.emit('message', {"event":"bot_response","response":response_arr[-1]})

            attempts+=1

            if isinstance(response_arr, str):
                MAX_ATTEMPTS = 5
                break

            # control-yeilding actions:
            # - final_response
            # - error
            # - request_clarification

            # see if we have MORE actions to process or if we're done and can break out of the loop
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
                    if "action" in action and (action["action"] == "final_response" or action["action"] == "error" or action["action"] == "request_clarification"):
                        print("breaking out of loop")
                        attempts = MAX_ATTEMPTS
                        break

        # yield control to the main thread
        conversation.bot_holds_lock = False
        db.session.commit()
        socketio.emit('message', {"event":"lock_released", "convo_id":1})

def receive_user_message(options):
    convo_id = options["convo_id"]
    prompt = options["prompt"]

    if prompt.strip() == "/clear":
        # delete all messages for conversation id=1 and return success
        db.session.query(Message).filter(Message.convo_id == convo_id).delete()
        db.session.commit()
        return {"success": True}

    jakedowns = User.query.filter_by(username="jakedowns").first()

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

    # Start a new thread to perform the background task
    thread = threading.Thread(target=process_user_input, args=[options])
    thread.start()

    return {"success": True}