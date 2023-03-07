import openai
import json
import datetime
from flask import jsonify, request, render_template
from mygptapp import db, app, bing_search_api
from mygptapp.models import Message, User, Conversation
from mygptapp.schemas import MessageSchema, MessageCreateSchema, OpenAIApiMessageSchema
from marshmallow import ValidationError
from mygptapp.url_scraper import UrlScraper
from mygptapp.rules import Rules

rules = Rules()

# Create a Marshmallow schema for validating and deserializing Messages
message_schema = MessageSchema()

@app.route('/')
def index():
    return render_template('index.html')

# create a bootup route which gets all messages
@app.route('/bootup')
def bootup():
    # get all messages from db for current convo (temp hard-coded to id=1)
    messages = db.session.query(Message).filter(Message.convo_id == 1).all()
    # sqla-flask json response
    return [MessageSchema().dump(message) for message in messages]

def process_scrape_results(original_prompt, scraper):
    print("scraper: ", scraper)
    # convert the scraper object to a message
    scrape_results_as_message = "Scrape Results for Url: " + scraper.url
    scrape_results_as_message += "\n"
    scrape_results_as_message += "title: " + scraper.title
    scrape_results_as_message += "\n"
    scrape_results_as_message += "text: " + scraper.text
    scrape_results_as_message += "\n------------------"
    scrape_results_as_message += "\n"
    # bake scrape_results into a "chat"
    messages = []
    messages.append({"role": "user", "content": original_prompt})
    messages.append({"role": "system", "content": scrape_results_as_message})
    messages.append({"role": "system", "content": rules.get_response_rules_text()})
    messages.append({"role": "system", "content": "Please respond with your next action request based on the scrape results. If the answer to the original question is not in the scrape results, please use a think action to think about what you might do next to resolve the question."})

    print("calling the model with a followup prompt: ", messages)



def search_results_to_message(query, search_results):
    search_results_as_message = "Relevant Search Results for Query: " + query
    search_results_as_message += "\n"
    for result in search_results:
        search_results_as_message += "result title: " + result['name']
        search_results_as_message += "\n"
        search_results_as_message += "result url: " + result['url']
        search_results_as_message += "\n"
        search_results_as_message += "result snippet: " + result['snippet']
        search_results_as_message += "\n"
    return search_results_as_message


# TODO: put this in a module
def process_web_search_results(original_prompt, query, search_results):
    print("search_results: ", search_results)

    # check for errors
    if "error" in search_results:
        print("error in search_results: ", search_results["error"])
        return search_results

    # bake search_results into a "chat"
    messages = []
    messages.append({"role": "user", "content": original_prompt})
    search_results_as_message = search_results_to_message(query, search_results)
    messages.append({"role": "assistant", "content": search_results_as_message})
    messages.append({"role": "system", "content": "Please respond with your next action request based on the web results. remember that snippets are usually stale, so use a scrape_url action to get the latest page content."})
    messages.append({"role": "system", "content": rules.get_response_rules_text()})

    print("calling the model with a followup prompt: ", messages)

    followup_response = call_model(messages)
    followup_response["search_results_as_message"] = search_results_as_message
    print("followup_response: ", followup_response)

    # save followup response to db in conversation id=2
    bot = User.query.filter_by(username="bot").first()
    #jakedowns = User.query.filter_by(username="jakedowns").first()
    message = Message(
        role="assistant",
        content=followup_response['choices'][0]['message']['content'],
        user_id=bot.id,
        is_inner_thought=False,
        convo_id=1)
    db.session.add(message)
    db.session.commit()
    return followup_response

def call_model(messages):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        #prompt=prompt,
        # temperature=0.7,
        # max_tokens=256,
        # top_p=1,
        # frequency_penalty=0,
        # presence_penalty=0
        messages=messages
    )

def perform_action(conversation, original_prompt, action, response_arr, attempt, max_attempts):
    #if action is a string for some reason, just return the response_arr unchanged
    if isinstance(action, str):
        return response_arr

    print("perform_action: ", action, attempt, max_attempts)

    if action is not None and "action" not in action:
        print("action is not None and action does not contain an action key")
        return response_arr

    if action is not None and "action" in action and action["action"] != "respond":
        action_response = handle_action(original_prompt, action, attempt, max_attempts)

        if action_response is not None and "action" in action_response and action_response["action"] == "web_search":
            # stub an extra message that contains the search results
            response_arr.append({
                'choices': [
                    {
                        'message': {
                            'role': 'assistant',
                            'content': action_response["search_results_as_message"]
                        }
                    }
                ]
            })
            # forget the search_results_as_message key so it doesn't get duplicated in our response
            action_response["search_results_as_message"] = None
        if action_response is not None:
            response_arr.append(action_response)

    if action is not None and action["action"] == "respond":
        # release the lock
        conversation.bot_holds_lock = False
        db.session.commit()

    return response_arr


@app.route('/gpt', methods=['POST'])
def get_gpt_response():
    prompt = request.json.get('prompt')

    if prompt.strip() == "/clear":
        # delete all messages for conversation id=1 and return success
        db.session.query(Message).filter(Message.convo_id == 1).delete()
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

    response = call_model(recent_messages)

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

    attempts = 0
    MAX_ATTEMPTS = 3
    while attempts < MAX_ATTEMPTS:
        response_arr = process_latest_actions_in_response_arr(conversation, current_prompt, response_arr, attempts, MAX_ATTEMPTS)
        attempts+=1
        # if any of the actions in the response_arr are "respond" or start with "Error Encountered" then we can break out of the loop
        for response in response_arr:
            actions_array = []
            try:
                actions_array = get_actions_from_response(response)
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
                if action["action"] == "respond":
                    print("breaking out of loop")
                    attempts = MAX_ATTEMPTS
                    break



    return jsonify(response_arr)

def get_actions_from_response(response):
    latest_response_content = response['choices'][0]['message']['content']
    actions_array = []
    try:
        actions_array = json.loads(latest_response_content)
        # if it's an object and not an array, wrap it in an array
        if isinstance(actions_array, dict):
            actions_array = [actions_array]
    except Exception as e:
        print("error parsing json: ", latest_response_content)

    return actions_array

def process_latest_actions_in_response_arr(conversation, current_prompt, response_arr, attempt, max_attempts):
    # get the latest response
    latest_response = response_arr[-1]
    # get the latest response message.content and see if it contains an action request

    actions_array = []
    try:
        actions_array = get_actions_from_response(latest_response)
    except Exception as e:
        response_arr.append({
            'choices': [
                {
                    'message': {
                        'role': 'system',
                        'content': "Error Encountered, invalid json response: " + latest_response
                    }
                }
            ]
        })
        return response_arr

    # todo: limit the number of actions
    for action in actions_array:
        response_arr = perform_action(conversation, current_prompt, action, response_arr, attempt, max_attempts)

    return response_arr



def handle_action(current_prompt, action_obj, attempt, max_attempts):
    print("action_obj: ", action_obj)
    action = action_obj["action"]
    response = None # no additional response payload to include

    # if query key is not present or parameters["query"] is None
    if(action == "web_search" and ("query" not in action_obj or action_obj["query"] is None)):
        raise Exception("query parameter is required for web_search action")

    # TODO: queue these as followups and return a status like "Searching the Web for: XYZ"

    # switch on the action
    if(action == "request_clarification"):
        pass
    elif(action == "web_search"):
        search_results = bing_search_api.searchAndReturnTopNResults(action_obj["query"], 3)
        response = process_web_search_results(current_prompt, action_obj["query"], search_results)
        response["action"] = "web_search"
        pass
    elif(action == "search_inner_thoughts"):
        pass
    elif(action == "think"):
        # 1. write action_obj["thought"] to db
        bot = User.query.filter_by(username="bot").first()
        thoughtMessage = Message(user_id=bot.id, role="assistant", content=action_obj["thought"], convo_id=1, is_inner_thought=True)
        db.session.add(thoughtMessage)
        db.session.commit()

        # 2. get a response from OpenAI
        response = call_model([action_obj["thought"] + rules.get_response_rules_text()], attempt, max_attempts)

        # 3. store the response to the db
        thoughtMessage = Message(user_id=bot.id, role="assistant", content=response['choices'][0]['message']['content'], convo_id=1, is_inner_thought=True)
        db.session.add(thoughtMessage)
        db.session.commit()
        pass
    elif(action == "respond"):
        pass
    elif(action == "scrape_url"):
        scraper = UrlScraper(action_obj["url"])
        response = process_scrape_results(current_prompt, scraper)
    else:
        print("unknown action: ", action)
        pass

    return response
