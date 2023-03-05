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
app.config['TEMPLATES_AUTO_RELOAD'] = True # Reload templates on change
app.jinja_env.auto_reload = True

def messages_from_rows_to_objects(messages):
	messages_as_array_of_objects = []
	for message in messages:
		print(json.dumps(message))
		messages_as_array_of_objects.append({   
			# 0 = id
			"role": message[1],
			"content": message[2],
			"created_at": message[3]	
		});
	return messages_as_array_of_objects	

@app.route('/')
def index():
	return render_template('index.html')

# create a bootup route which gets all messages
@app.route('/bootup')
def bootup():
	messages = store.get_all_messages()
	return jsonify(messages_from_rows_to_objects(messages))

@app.route('/gpt', methods=['POST'])
def get_gpt_response():
	prompt = request.json.get('prompt')
	store.insert_message('user', prompt)
	messages = store.get_messages_for_prompt(10);
	response = openai.ChatCompletion.create(
		model="gpt-3.5-turbo",
		#prompt=prompt,
		# temperature=0.7,
		# max_tokens=256,
		# top_p=1,
		# frequency_penalty=0,
		# presence_penalty=0
		messages=messages_from_rows_to_objects(messages)
	)
	store.insert_message('assistant', response['choices'][0]['message']['content'])
	return jsonify(response)

if __name__ == '__main__':
	extra_files = ['templates/index.html', 'app.py', 'chatdb.py']
	app.run(port=8888, debug=True, extra_files=extra_files)
