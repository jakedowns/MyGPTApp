from flask import jsonify, request, render_template
import openai
from mygptapp import db, app
from mygptapp.models import Message, User, Conversation
from mygptapp.schemas import MessageSchema, MessageCreateSchema, OpenAIApiMessageSchema
from marshmallow import ValidationError

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


@app.route('/gpt', methods=['POST'])
def get_gpt_response():
    prompt = request.json.get('prompt')

    bot = User.query.filter_by(username="bot").first()
    jakedowns = User.query.filter_by(username="jakedowns").first()
    conversation = Conversation.query.filter_by(id=1).first()

    # insert the user message in the db
    input = {
        "role": "user",
        "content": prompt,
        "user_id": jakedowns.id,
        "convo_id": 1
    }

    schema = MessageCreateSchema()
    message_data = schema.load(input)
    message = Message(**message_data)
    db.session.add(message)
    db.session.commit()

    # get 10 most recent messages from db for current convo (temp hard-coded to id=1)
    recent_messages = db.session.query(Message).filter(Message.convo_id == 1).order_by(Message.id.desc()).limit(10).all()
    recent_messages = [OpenAIApiMessageSchema().dump(message) for message in recent_messages]

    print("recent_messages: ", recent_messages)

    # add a postscript to the last message
    recent_messages[-1]['content'] += "\n(postscript) the preceding message was sent by a human, it is the 'base prompt' or 'primary prompt' you are responding to. please respond in the form of an \"action request\" using one of the following actions. your response should look like '[action=ACTION_NAME, ?param1='', ...]' you can also use the side_action on a new line to suggest new actions or ask about the postscript instructions."

    recent_messages[-1]['content'] += "the following actions are available. please choose the appropriate one:"
    recent_messages[-1]['content'] += "\n1. [action=request_clarification, text=\"please clarify ... (add your own clarification request here)\"], "
    recent_messages[-1]['content'] += "\n2. [action=web_search, query=\"web query goes here\"], "
    recent_messages[-1]['content'] += "\n3. [action=search_inner_thoughts, query=\"inner thoughts query goes here\"], "
    recent_messages[-1]['content'] += "\n4. [action=think, thought=\"thought to think about goes here\"] // this action writes to your inner_thought side chat to help you fulfill the prompt. example: [action=think, thought=\"i think i should try to answer the prompt by searching the web for the answer\"]"
    recent_messages[-1]['content'] += "\n5. [action=respond, response=\"response to the original prompt goes here\"] // this action ends your thought process for the current prompt and yields control of the chat back to the human "
    recent_messages[-1]['content'] += "\n you have currently used 0 of your 3 actions for this prompt. you will get 3 opportunities to use actions per base prompt, try to action=respond as soon as possible, but don't be shy about using all action turns if you need them. there is also a side_action you can use at any time, \n [side_action=suggest, suggestion=\"example: id like to propose a new action type named X with the parameters Y and Z\"] // use this side_action to suggest edits to this postscript, or suggest new actions or changes to the action policy, this particular action will be hidden from the user and is for the system maintainer only. it is not required, it does not count against your available total turns for the base prompt and can be sent back alongside your required action selection.) if you have any questions about this postscript, please use [side_action=maintainer_question, question=''] do not use a primary action to refer to this postscript as it should be an invisible mechanic to the end user. \n"


    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        #prompt=prompt,
        # temperature=0.7,
        # max_tokens=256,
        # top_p=1,
        # frequency_penalty=0,
        # presence_penalty=0
        messages=recent_messages
    )

    input = {
        "role": "assistant",
        "content": response['choices'][0]['message']['content'],
        "user_id": bot.id,
        "convo_id": 1
    }

    # specify the bot holds the lock for the conversation
    conversation.bot_holds_lock = True

    # store the bot's response in the db
    message_data = schema.load(input)
    message = Message(**message_data)
    db.session.add(message)
    db.session.commit()

    # TODO: queue a follow-up job for the bot to reflect
    # the bot should check: did my previous response satisfy the original prompt?
    # Y: release lock
    # N: think AGAIN, perhaps more info is needed, or actions need to be performed before the bot can consider the prompt satisfied (check how many inner_thought cycles we have left, if we're out of them, the last cycle MUST release the lock)

    # if the bots response is an action request, then we need to queue a follow-up job for the bot to perform the action
    if(input["content"].startswith("[action=")):
        action = input["content"].split(",")[0].split("=")[1]
        parameters = input["content"].split(",")[1].split("=")[1].split("]")[0]
        print("action: ", action)
        print("parameters: ", parameters)
        # switch on the action
        if(action == "request_clarification"):
            pass
        elif(action == "web_search"):
            pass
        elif(action == "search_inner_thoughts"):
            pass
        elif(action == "think"):
            pass
        elif(action == "respond"):
            pass
        else:
            print("unknown action: ", action)
            pass

    return jsonify(response)