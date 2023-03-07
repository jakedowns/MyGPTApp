import datetime

class Rules:
    def get_actions_list(self):
        actions_list = {
            "request_clarification": {
                "description": "request clarification from the user",
                "params": {
                    "text": {
                        "description": "the text of the clarification request",
                        "required": True
                    }
                }
            },
            "web_search": {
                "description": "search the web for a query, when this action is performed, the assistant will have the ability to invoke follow-up actions before responding to the user",
                "params": {
                    "query": {
                        "description": "the query to search for",
                        "required": True
                    }
                }
            },
            "search_inner_thoughts": {
                "description": "search your inner thoughts for a query",
                "params": {
                    "query": {
                        "description": "the query to search for",
                        "required": True
                    }
                }
            },
            "think": {
                "description": "think about a thought, save it to your inner_thoughts for later reference",
                "params": {
                    "thought": {
                        "description": "the thought to think about",
                        "required": True
                    }
                }
            },
            "respond": {
                "description": "respond to the user's prompt",
                "params": {
                    "text": {
                        "description": "the text of your response",
                        "required": True
                    }
                }
            },
            "final_response": {
                "description": "final response for the current base prompt. use this to indicate you're done thinking and yeild control back to the user",
                "params": {
                    "text": {
                        "description": "the text of your response",
                        "required": True
                    }
                }
            },
            "respond_with_image": {
                "description": "respond to the user's prompt with an image",
                "params": {
                    "image_url": {
                        "description": "the url of the image to respond with",
                        "required": True
                    }
                }
            },
            "scrape_url": {
                "description": "scrape a url for text",
                "params": {
                    "url": {
                        "description": "the url to scrape",
                        "required": True
                    }
                }
            },
            # "request_execute_python": {
            #     "description": "request to execute python code (use this as a last resort)",
            #     "params": {
            #         "code": {
            #             "description": "the python code to execute",
            #             "required": True
            #         }
            #     }
            # },
            "message_maintainer": {
                "description": "send a message to the maintainer",
                "params": {
                    "text": {
                        "description": "the text of your message to the maintainer",
                        "required": True
                    }
                }
            },
            # "clear": {
            #     "description": "erase all messages in the current conversation",
            #     "params": {}
            # }
        }
        return actions_list

    def get_response_rules_text(self):
        text = "\nREMEMBER YOU MUST ALWAYS FORMAT YOUR RESPONSE IN THE FORMAT: {\"actions\": [action1, action2, ...]} YOUR ENTIRE RESPONSE MUST BE VALID JSON, do not include any extra commentary about your actions or choices. if you do have something to share, include it in the actions array as a think action or a message_maintainer action.\n"

        text += "the following actions are available:"

        i = 0
        for action_name, action in self.get_actions_list().items():
            text += "\n" + str(i) + ". {\"action\":\"" + str(action_name) + "\"";
            for param_name, param in action["params"].items():
                text += ", \"" + param_name + "\":\"\""
            text += "}"
            i += 1

        text += "\nhere is a description of each action type:"
        i = 0
        for action_name, action in self.get_actions_list().items():
            text += "\n" + str(i) + ". " + action["description"]
            for param_name, param in action["params"].items():
                text += "\n\t" + param_name + ": " + param["description"]
            i += 1

        text += "\n please use the think action to save your inner thoughts for later reference, like {action: think, thought:\"ok, i'm replying to the base prompt: \"example base prompt\", it's going to take me a few actions to get a satisfactory result. my plan is to do x, then y, then z. so far i haven't completed any of those steps. \"} // this will save your inner thought for later reference, so you can search your inner thoughts for it later using {action:search_inner_thoughts,query:\"what is my plan for replying? what is my progress so far, what steps have i completed and what steps do i have left to complete?\"}"
        text += "\n if you find yourself stuck or unsure how to reply to the base prompt, you can {action:think,thought:\"how could i best use my available actions to generate a reply to the base prompt?\"}"
        text += "\n when performing a multi-action reply routine, remember to \"think\" updates to your plan, like step 2 complete. moving on to step 3 now."

        return text

    def get_postscript(self):
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        postscript = "\n(postscript) the current date and time is " + today + ". you are an AUGMENTED assistant, meaning you have additional functions available to you beyond your base functions. you have the ability to access real-time information using actions. the preceding messages are a chat between you and a human. the most recent message from the user is the current 'base prompt' you are are now responding to. make sure that your focus is figuring out which array of actions to perform to best reply to the current 'base prompt' in a satisfactory way. you do not need to define ALL your actions up front, some actions like search_web give you an opportunity to invoke a followup action once you have search results to reference. " + self.get_response_rules_text()
        print(postscript)
        return postscript