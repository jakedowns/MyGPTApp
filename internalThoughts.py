import json
import os

thought_file = "thoughts.json"

class InternalThoughts()

	thought_state = {}

	def __init__(self):	
		# if thought_file does not exist, create it
		if not os.path.exists(thought_file):	
			with open(thought_file, "w") as f:
				f.write("{}")	

	def load_internal_thought_state():
		with open(thought_file, "r") as f:
			thought_state = json.load(f)
			return thought_state

	def get_thought_state():
		return thought_state	

	def write_internal_thought_state():
		with open(thought_file, "w") as f:
			json.dump(thought_state, f)	
