import json
from mygptapp import db, rules
from mygptapp import bing_search_api
from mygptapp.models import Message, User
from mygptapp.actions.web_search import WebSearch
#from mygptapp.actions.scrape_url import ScrapeUrl

web_search = WebSearch()

class Actions:
    def perform_action(self, conversation, original_prompt, action, response_arr, attempt, max_attempts):
        #if action is a string for some reason, just return the response_arr unchanged
        if isinstance(action, str):
            return response_arr

        print("perform_action: ", action, attempt, max_attempts)

        if action is not None and "action" not in action:
            print("action is not None and action does not contain an action key")
            return response_arr

        if action is not None and "action" in action and action["action"] != "respond":
            action_response = self.handle_action(original_prompt, action, attempt, max_attempts)

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

        if action is not None and action["action"] == "respond":
            # release the lock
            conversation.bot_holds_lock = False
            db.session.commit()

        return response_arr

    def get_actions_from_response(self, response):
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

    def process_latest_actions_in_response_arr(self, conversation, current_prompt, response_arr, attempt, max_attempts):
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

        # todo: limit the number of actions
        # temp: just run the first action only
        if len(actions_array) > 0:
            for action in actions_array[:1]:
                response_arr = self.perform_action(conversation, current_prompt, action, response_arr, attempt, max_attempts)

        return response_arr

    def handle_action(self, current_prompt, action_obj, attempt, max_attempts):
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
        elif(action == "web_search" or action == "search_web"):
            search_results = bing_search_api.searchAndReturnTopNResults(action_obj["query"], 3)
            response = web_search.process_web_search_results(current_prompt, action_obj["query"], search_results)
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
            from mygptapp.openai_api import OpenAIAPI
            api = OpenAIAPI()
            response = api.call_model([{
                "role": "assistant",
                "content": action_obj["thought"] + rules.get_response_rules_text()
            }])

            # 3. store the response to the db
            thoughtMessage = Message(user_id=bot.id, role="assistant", content=response['choices'][0]['message']['content'], convo_id=1, is_inner_thought=True)
            db.session.add(thoughtMessage)
            db.session.commit()
            pass
        elif(action == "respond"):
            pass
        elif(action == "final_response"):
            pass
        elif(action == "scrape_url"):
            from mygptapp.actions.scrape_url import ScrapeURL
            scraper = ScrapeURL(action_obj["url"])
            response = scraper.process_scrape_results(current_prompt)
        elif(action == "clear"):
            # delete all messages in the conversation in one line
            Message.query.filter_by(convo_id=1).delete()
            db.session.commit()
            pass
        else:
            print("unknown action: ", action)
            pass

        return response