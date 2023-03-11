# MyGPTApp:

<!-- MarkdownTOC autolink="true" style="ordered" -->

1. [Example Usage Video:](#example-usage-video)
1. [Setup Tutorial Video:](#setup-tutorial-video)
1. [Pre-requisites:](#pre-requisites)
1. [Setup](#setup)
1. [Using the App](#using-the-app)
	1. [Chat Commands:](#chat-commands)
	1. [Example Prompts:](#example-prompts)
	1. [Configuration:](#configuration)

<!-- /MarkdownTOC -->

### Example Usage Video:
[Click to Watch on Youtube](https://www.youtube.com/watch?v=bL7aMW3KQP0)

### Setup Tutorial Video:
[#ComingSoon]()

### How It Works



### Pre-requisites:

> This app requires the following API keys:
>
> OpenAI API: `https://platform.openai.com/account/api-keys`
>
> Bing Web Search API: `https://portal.azure.com/`

### Setup

1. Clone Repo: https://github.com/jakedowns/MyGPTApp

 	> if you are running on windows, i recommend running this app under WSL2 > Ubuntu 20.04 LTS

1. Clone the .env.example file to .env `cp .env.example .env`

1. Add your API keys to `.env` file

	> ```
	> OPENAI_API_KEY=XXX
	> BING_SEARCH_API_KEY=XXX
	> ```

1. cd into MyGPTApp and run `pip install -r requirements.txt`

1. Run the Server: `python __main__.py`

1. Visit the Server in your browser: `http://127.0.0.1:8000/`

### Using the App

- This app is still very buggy, so make sure to monitor the Python and JS console for errors.
- The bot sometimes breaks character and stops returning valid JSON. If the entire response is not valid JSON (i.e. if the bot includes text OUTSIDE the json object in it's response, the server will be unable to parse the JSON and therefore be unable to run any command issued by the bot.) Sometimes, you can get the bot back into character by reminding it to refer to it's instructions, or to be sure to return only JSON, but most of the time, you'll have to Clear the chat and start over once this happens.

### Chat Commands:

`/clear` Erases all the messages in the conversation and clears the chat.

### Example Prompts:

- `what is the current weather in NYC?` - it should do a web_search, followed by a scrape_url, and a final_response
- `what is google's current stock price?` - (ditto)
- `render a graph of the software development lifecycle. make it a LR graph. use subgraphs to keep things organized. make the background black, make all text white, make edges white, make nodes and subgraphs black with white borders and white text.`

you can also issue follow-up prompts in response to a graph like,
- `connect the user and server nodes with a bi-directional edges labeled "request" and "response"`
- `remove the PHP node from the graph`

### Configuration:

`mygptapp/actions/receive_user_message.py`

- `NUM_RECENT_MSGS`

> this is the number of messages from the convo history to include when calling `ChatGPT3.5Turbo` We must limit this to not go over the max number of tokens per request

- `MAX_ATTEMPTS`

> This is the max number of times the bot can issue a command to be processed in response to a "base prompt"
>
> beyond this number, the server will yield control back to the user, ignoring any further commands
>
> the higher the number, the longer the bot can continue to think and perform actions, but the longer the user will have to wait for a final response
>
> TODO: I don't currently expose anything like "you have used 2 of your 5 action turns for the current base prompt, you have 3 actions remaining" but it would probably be helpful

`mygptapp/actions/__init__.py` - `ACTION_LIMIT`

> This is the number of actions that will be executed per "sub-turn" (the number of sub-turns is defined by `MAX_ATTEMPTS`)
>
> I have it set to 1 for now because, sometimes the bot tries to be too clever about planning ahead in terms of how it tries to plan ahead with it's handling of results from web_search / scrape_url (imagining variables and things) so, i've found it's better to limit things to running one action at a time.
>
> IF YOU CHANGE THIS VALUE make sure you update the `preamble` so the bot knows that the server won't just be looking at the first action in each response



`mygptapp/rules.py: Rules@get_preamble_text` - This method contains the preamble text that is sent with your prompts to GPT3.5Turbo. It is based on the [Act as a Linux Terminal](https://github.com/f/awesome-chatgpt-prompts#act-as-a-linux-terminal) from the [Awesome ChatGPT Prompts Repo](https://github.com/f/awesome-chatgpt-prompts)

`mygptapp/rules.py: Rules@get_actions_list` - This method contains the list of actions the bot can respond with. The current "response actions" available are:

> 1. request_clarification
> 1. web_search
> 1. think
> 1. respond
> 1. final_response
> 1. scrape_url
> 1. commentary
> 1. render_graph
