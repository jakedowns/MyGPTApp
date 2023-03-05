import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Get prompt from command line argument
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('prompt', type=str, help='The prompt for the OpenAI API')
args = parser.parse_args()

print(args.prompt)

response = openai.Completion.create(
  model="text-davinci-003",
  prompt=args.prompt,
  temperature=0.7,
  max_tokens=256,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)

print(response)
