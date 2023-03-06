from flask import jsonify, request, render_template
import openai
from gpt3 import db, Message

# Create a Marshmallow schema for validating and deserializing Messages
message_schema = Message.MessageSchema()

@app.route('/')
def index():
    return render_template('index.html')

# create a bootup route which gets all messages
@app.route('/bootup')
def bootup():
    # get all messages from db for current convo (temp hard-coded to id=1)
    messages = db.session.query(Message).filter(Message.convo_id == 1).all()
    # sqla-flask json response
    return [Message.MessageSchema().dump(message) for message in messages]


@app.route('/gpt', methods=['POST'])
def get_gpt_response():
    prompt = request.json.get('prompt')

    # insert the user message in the db
    input = {
        "role": "user",
        "content": prompt
    }

    schema = Message.MessageCreateSchema()
    message = schema.load(input)
    db.session.add(message)
    db.session.commit()

    # get 10 most recent messages from db for current convo (temp hard-coded to id=1)
    recent_messages = db.session.query(Message).filter(Message.convo_id == 1).order_by(Message.id.desc()).limit(10).all()
    recent_messages = [Message.OpenAIApiMessageSchema().dump(message) for message in recent_messages]

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
        "content": response['choices'][0]['message']['content']
    }

    schema = Message.MessageCreateSchema()
    message = schema.load(input)
    db.session.add(message)
    db.session.commit()

    return jsonify(response)