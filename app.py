from flask import Flask, jsonify, request, render_template
import json
import os
import openai
from dotenv import load_dotenv 
load_dotenv()

from chatdb import MessageStore

store = MessageStore()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# create a bootup route which gets all messages
@app.route('/bootup')
def bootup():
    messages = store.get_all_messages()
    return jsonify(messages)

@app.route('/gpt', methods=['POST'])
def get_gpt_response():
    prompt = request.json.get('prompt')
    store.insert_message('user', prompt)
    messages = store.get_messages_for_prompt(10);
    
    for message in messages:
        print(json.dumps(message))

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        #prompt=prompt,
        # temperature=0.7,
        # max_tokens=256,
        # top_p=1,
        # frequency_penalty=0,
        # presence_penalty=0
        messages=messages
    )
    store.insert_message('assistant', response['choices'][0]['message']['content'])
    return jsonify(response)

if __name__ == '__main__':
    app.run(port=8888)
