from flask import request, jsonify
from mygptapp.models import Message, Conversation, User
from mygptapp.schemas import MessageCreateSchema, OpenAIApiMessageSchema
from mygptapp import db, rules, app, socketio
import asyncio
from mygptapp.utils import save_and_emit_message

import threading

# def process_user_input(options):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

#     loop.run_until_complete(process_user_input_async(options))
#     loop.close()

async def process_user_input_async(options):
    # the max number of times the bot can issue a command to be processed in response to a "base prompt"
    # beyond this number, the server will yield control back to the user, ignoring any further commands
    # the higher the number, the longer the bot can continue to think and perform actions, but the longer the user will have to wait for a final response
    MAX_ATTEMPTS = 5

    # the number of most recent messages to send to the chat GPT model to constitute the conversation history
    NUM_RECENT_MSGS = 5

    with app.app_context():
        # jakedowns = User.query.filter_by(username="jakedowns").first()
        bot = User.query.filter_by(username="bot").first()
        conversation = Conversation.query.filter_by(id=1).first()

        # get N most recent messages from db for current convo (temp hard-coded to id=1)
        recent_messages = db.session.query(Message).filter(Message.convo_id == 1).order_by(Message.id.desc()).limit(NUM_RECENT_MSGS).all()
        #reverse the order of the messages
        recent_messages = recent_messages[::-1]
        recent_messages = [OpenAIApiMessageSchema().dump(message) for message in recent_messages]

        # print("recent_messages: ", recent_messages)

        # copy by value not by reference
        current_prompt = recent_messages[-1]["content"]

        # prepend rules.get_preamble_text() to the list of messages
        recent_messages.insert(0, {
            "role": "assistant",
            "content": rules.get_preamble_text(),
        })

        from mygptapp import api

        response = api.call_model(recent_messages)

        # specify the bot holds the lock for the conversation
        conversation.bot_holds_lock = True
        db.session.commit()

        save_and_emit_message(
            bot.id,
            1, # convo_id
            "assistant",
            response['choices'][0]['message']['content'],
            options
        )

        response_arr = [response]

        from mygptapp.actions import Actions
        actions = Actions()

        # this is our "sub-turn" loop
        # the bot will continue to process actions until it has no more actions to process, or until it has reached the max number of sub-turns
        attempts = 0
        prev_response_arr_length = len(response_arr)
        while attempts < MAX_ATTEMPTS:
            response_arr = await actions.process_latest_actions_in_response_arr(conversation, current_prompt, response_arr, attempts, MAX_ATTEMPTS)

            if(len(response_arr) == prev_response_arr_length):
                print("no new actions were added to the response_arr")
                break

            print("attempt ", str(attempts) + " of " + str(MAX_ATTEMPTS))
            print("response_arr length: ", len(response_arr))

            attempts+=1
            prev_response_arr_length = len(response_arr)

            # if response_arr is a string, then we can break out of the loop
            if isinstance(response_arr, str) or len(response_arr) == 0:
                MAX_ATTEMPTS = 5
                break

            # control-yeilding actions:
            # - final_response
            # - request_clarification
            # - error

            # see if we have MORE actions to process or if we're done and can break out of the loop
            #for response in response_arr:
            latest_response = response_arr[-1]
            actions_array = []
            try:
                actions_array = actions.get_actions_from_response(latest_response)
            except Exception as e:
                print("error getting actions from response: ", latest_response)
                response_text = latest_response['choices'][0]['message']['content']
                if response_text.strip().startswith("Error Encountered"):
                    attempts = MAX_ATTEMPTS
                    break
            #for action in actions_array:
            if len(actions_array) == 0:
                attempts = MAX_ATTEMPTS
                break

            else:
                action = actions_array[0]
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
        options["_socketio"].emit('message', {"event":"lock_released", "convo_id":1}, room=options["clientid"])

def receive_user_message(options):
    convo_id = options["convo_id"]
    prompt = options["prompt"]

    if prompt.strip() == "/clear":
        # delete all messages for conversation id=1 and return success
        db.session.query(Message).filter(Message.convo_id == convo_id).delete()
        db.session.commit()
        # release lock and emit the lock released event
        conversation = Conversation.query.filter_by(id=convo_id).first()
        conversation.bot_holds_lock = False
        db.session.commit()
        options["_socketio"].emit('message', {"event":"lock_released", "convo_id":convo_id}, room=options["clientid"])
        return {"success": True, "message_id": -1}

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
    options["_socketio"] = socketio
    socketio.start_background_task(start_background_task, options)

    return {"success": True, "message_id": message.id}

def start_background_task(options):
    print("starting background task. options: ",options)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = asyncio.ensure_future(process_user_input_async(options))

    def stop_loop_on_completion(future):
        loop.stop()

    task.add_done_callback(stop_loop_on_completion)
    loop.run_forever()