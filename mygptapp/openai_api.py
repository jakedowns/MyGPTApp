import openai

class OpenAIAPI:
    def call_model(self, messages):
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