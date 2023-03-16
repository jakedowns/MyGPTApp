import json
from mygptapp import db, rules
from mygptapp import bing_search_api, socketio
from mygptapp.models import Message, User
from mygptapp.actions.memories import Memories
from mygptapp.actions.web_search import WebSearch
#from mygptapp.actions.scrape_url import ScrapeUrl
from mygptapp.actions.graphviz_api import GraphVizApi
from mygptapp.actions.todos import Todos
from mygptapp.utils import save_and_emit_message, emit_message

todos = Todos()
web_search = WebSearch()
graphviz_api = GraphVizApi()
memories = Memories()

ACTION_LIMIT = 1 # 5

# process_latest_actions_in_response_arr -> (get_actions_from_response -> (handle_action -> perform_action))
class Actions:
    async def process_latest_actions_in_response_arr(self, conversation, current_prompt, response_arr, attempt, max_attempts, options={}):
        # get the latest response
        latest_response = response_arr[-1]
        # get the latest response message.content and see if it contains an action request

        actions_array = []
        try:
            actions_array = self.get_actions_from_response(latest_response)
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

        if len(actions_array) > 0:
            current_action = 0
            while current_action < ACTION_LIMIT and current_action < len(actions_array):
                action = actions_array[current_action]
                response_arr = await self.perform_action(conversation, current_prompt, action, response_arr, attempt, max_attempts, options)
                current_action += 1

                # emit a socketio event to the client with the most recent entry in the response_arr
                # socketio.emit('message', {
                #     "event":"bot_response",
                #     "message": response_arr[-1]
                #     }, room="broadcast")


        return response_arr

    async def perform_action(self, conversation, original_prompt, action, response_arr, attempt, max_attempts, options={}):
        #if action is a string for some reason, just return the response_arr unchanged
        if isinstance(action, str):
            return response_arr

        print("perform_action: ", action, attempt, max_attempts)

        if action is not None and "action" not in action:
            print("action is not None and action does not contain an action key")
            return response_arr

        if action is not None and "action" in action and action["action"] != "respond":
            action_response = await self.handle_action(original_prompt, action, attempt, max_attempts, options)

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

            if action_response is not None and "action" in action_response and action_response["action"] == "scrape_url":
                # stub an extra message that contains the scrape results
                response_arr.append({
                    'choices': [
                        {
                            'message': {
                                'role': 'assistant',
                                'content': action_response["scrape_result_message"]
                            }
                        }
                    ]
                })
                # forget the scrape_result_message key so it doesn't get duplicated in our response
                action_response["scrape_result_message"] = None

            if action_response is not None:
                response_arr.append(action_response)

        if action is not None and ( action["action"] == "respond" or ("release_lock" in action and action["release_lock"] == True )):
            # release the lock
            conversation.bot_holds_lock = False
            db.session.commit()

        return response_arr

    def get_actions_from_response(self, response):
        if not response or 'choices' not in response or len(response['choices']) == 0:
            return []
        latest_response_content = response['choices'][0]['message']['content']
        actions_array = []
        try:
            actions_array = json.loads(latest_response_content)
            # if it's an object and not an array, wrap it in an array
            if isinstance(actions_array, dict) and "actions" not in actions_array:
                actions_array = [actions_array]
            elif isinstance(actions_array, dict) and "actions" in actions_array:
                actions_array = actions_array["actions"]
            elif isinstance(actions_array, list):
                pass
        except Exception as e:
            print("error parsing json: ", latest_response_content)
        print("\n----\n")
        print("current actions array:", actions_array)
        return actions_array


    async def handle_action(self, current_prompt, action_obj, attempt, max_attempts, options={}):
        print("handle_action action_obj: ", action_obj)
        action = action_obj["action"]
        response = None # no additional response payload to include
        bot = User.query.filter_by(username="bot").first()

        # if query key is not present or parameters["query"] is None
        if(action == "web_search" and ("query" not in action_obj or action_obj["query"] is None)):
            raise Exception("query parameter is required for web_search action")

        # TODO: queue these as followups and return a status like "Searching the Web for: XYZ"

        # switch on the action
        if(action == "request_clarification"):
            pass
        elif(action == "web_search" or action == "search_web"):
            search_results = bing_search_api.searchAndReturnTopNResults(action_obj["query"], 3)

            save_and_emit_message(
                user_id=bot.id,
                role="assistant",
                content=web_search.search_results_to_message(action_obj["query"], search_results),
                convo_id=1,
                options=options
            )

            response = web_search.process_web_search_results(current_prompt, action_obj["query"], search_results)
            response["action"] = "web_search"

            save_and_emit_message(
                user_id=bot.id,
                role="assistant",
                content=response['choices'][0]['message']['content'],
                convo_id=1,
                options=options
            )
            pass
        elif(action == "render_graph"):
            graph_url = graphviz_api.render_graphviz_graph_from_dotlang_string(action_obj["dotlang_string"])
            msg_txt = f"![{graph_url}]({graph_url})\n[View]({graph_url})" if not graph_url.startswith("Error") else graph_url;

            response = {
                "role": "assistant",
                "content": msg_txt,
                "action": "render_graph"
            }

            # store the message to the db and emit it to the client
            save_and_emit_message(
                user_id=bot.id,
                role="assistant",
                content=response['content'],
                convo_id=1,
                options=options
            )
            pass
        # TODO: revisit this
        # elif(action == "search_inner_thoughts"):
        #     pass
        elif(action == "think"):
            # 1. write action_obj["thought"] to db
            save_and_emit_message(
                user_id=bot.id,
                role="assistant",
                content=action_obj["thought"],
                convo_id=1,
                options=options.merge({
                    "is_inner_thought": True
                })
            )

            # Get all previous inner thoughts from the convo (limit to 10)
            inner_thoughts = Message.query.filter_by(convo_id=1, is_inner_thought=True).order_by(Message.created_at.desc()).limit(10).all()
            # reverse the list so the oldest thoughts are first
            inner_thoughts.reverse()

            # 2. get a response from OpenAI
            from mygptapp.openai_api import OpenAIAPI
            api = OpenAIAPI()
            response = api.call_model(inner_thoughts.extend([{
                "role": "assistant",
                "content": "I am a bot having a conversation with a human. this thread is just my inner thoughts about the conversation. right now I'm about to think my next thought to myself. the next message will be the contents of my thought. i will then respond to that thought using ONLY valid json, nothing more, containing ONE of the following actions: " + rules.get_actions_list_as_text() + "\n current prompt: " + current_prompt
            },{
                "role": "assistant",
                "content": action_obj["thought"]
            }]))

            # 3. store the response to the db
            save_and_emit_message(
                user_id=bot.id,
                convo_id=1,
                role="assistant",
                content=response['choices'][0]['message']['content'],
                options=options.merge({
                    "is_inner_thought": True,
                })
            )
            pass
        elif(action == "respond"):
            pass
        elif(action == "final_response"):
            pass
        elif(action == "scrape_url"):
            from mygptapp.actions.scrape_url import ScrapeURL
            scraper = ScrapeURL(action_obj["url"])
            await scraper.scrape(scraper.url)
            response = scraper.process_scrape_results(current_prompt)
            save_and_emit_message(
                convo_id=1,
                user_id=bot.id,
                role="assistant",
                content=response['choices'][0]['message']['content'],
                options=options
            )
        elif(action == "clear"):
            # delete all messages in the conversation in one line
            Message.query.filter_by(convo_id=1).delete()
            db.session.commit()
            pass
        elif(action == "get_todos"):
            message = todos.get_todos_as_message()
            save_and_emit_message(
                convo_id=1,
                user_id=bot.id,
                role="assistant",
                content=message,
                options=options
            )
            # flag a response so the bot_holds_lock is released
            response = {"status": "success", "message": "got todos", "release_lock": True}
        elif(action == "add_todo"):
            todo = todos.add_todo(action_obj["text"])
            todos_as_message = todos.get_todos_as_message()
            emit_message(
                message=todos_as_message,
                options={"clientid": "broadcast"}
            )
            response = {"status": "success", "message": "added todo", "id": todo.id, "release_lock": True}
            pass
        elif(action == "remove_todo"):
            todos.remove_todo(action_obj["id"])
            todos_as_message = todos.get_todos_as_message()
            emit_message(
                message=todos_as_message,
                options={"clientid": "broadcast"}
            )
            response = {"status": "success", "message": "removed todo", "release_lock": True}
            pass
        elif(action == "update_todo"):
            todos.update_todo(action_obj["id"], action_obj["text"])
            todos_as_message = todos.get_todos_as_message()
            emit_message(
                message=todos_as_message,
                options={"clientid": "broadcast"}
            )
            response = {"status": "success", "message": "updated todo", "release_lock": True}
            pass
        elif(action == "toggle_todo"):
            todos.toggle_todo(action_obj["id"])
            todos_as_message = todos.get_todos_as_message()
            emit_message(
                message=todos_as_message,
                options={"clientid": "broadcast"}
            )
            response = {"status": "success", "message": "toggled todo", "release_lock": True}
            pass
        # elif(action == "get_reminders"):
        elif(action == "remember"):
            memory = memories.remember(action_obj["memory"])
            memory_as_message = memories.memory_as_message(memory)
            save_and_emit_message(
                convo_id=1,
                user_id=bot.id,
                role="assistant",
                content=memory_as_message,
                options=options
            )
        elif(action == "recall"):
            _memories = memories.recall(action_obj["memory"])
            print("recalled: ", _memories)
            memories_as_message = memories.memories_as_message(_memories)
            save_and_emit_message(
                convo_id=1,
                user_id=bot.id,
                role="assistant",
                content=memories_as_message,
                options=options
            )
        else:
            print("unknown action: ", action)
            pass

        return response