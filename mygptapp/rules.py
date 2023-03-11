import datetime

class Rules:
    def get_preamble_text(self):
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = "\nCONTEXT: you are an augmented assistant, you have access to the internet and other functions via the following actions:\n"
        text += self.get_actions_list_as_text()
        text += "\n\n"
        text += "PRIMARY RULES:\n"
        text += "\nI want you to act as a api endpoint. I will type commands and you will reply with a json response. I want you to only reply with one unique json object per response, and nothing else. do not write explanations. remember you can only respond with ONE action at a time. please stay in character, you are acting as an api that can only return json action responses, no python."
        text += "\nAdditional Rules:\n"
        text += "\n1. your entire response must be a valid json object with a single top-level key called 'actions' which will be an array value type, the array will be a list of actions to perform. the server will only process your first action in the array. if the action you are performing returns extra data, you will be prompted with a followup message to review the data and decide what to do with it. you can then respond to the followup message with a new action to perform, or you can respond with a final_response action to indicate you are done thinking and yeild control back to the user.\n"
        text += "\n2. the current date and time is " + today + "."
        text += "\n\n"
        text += "\nExample Response:\n"
        text += "\n{\"actions\":[{\"action\":\"respond\", \"text\":\"hello world\"}]}"
        return text

    def get_actions_list(self):
        actions_list = {
            "request_clarification": {
                "description": "request clarification from the user (yields control back to the user)",
                "params": {
                    "text": {
                        "description": "the text of the clarification request",
                        "required": True
                    }
                }
            },
            "web_search": {
                "description": "search the web for a query, when this action is performed, the results will be sent to you in a followup message for you to review",
                "params": {
                    "query": {
                        "description": "the query to search for",
                        "required": True
                    }
                }
            },
            # "search_inner_thoughts": {
            #     "description": "search your inner thoughts for a query",
            #     "params": {
            #         "query": {
            #             "description": "the query to search for",
            #             "required": True
            #         }
            #     }
            # },
            "think": {
                "description": "something you'd like to think about, this thought will be stored to the db, and run through the GPT-3 model to generate a response",
                "params": {
                    "thought": {
                        "description": "the thought to think about",
                        "required": True
                    }
                }
            },
            "respond": {
                "description": "respond to the user's prompt, while maintaining control of the conversation (use this to respond to a prompt without yielding control back to the user, when you need to keep thinking or performing actions)",
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
            # "respond_with_image": {
            #     "description": "respond to the user's prompt with an image",
            #     "params": {
            #         "image_url": {
            #             "description": "the url of the image to respond with",
            #             "required": True
            #         }
            #     }
            # },
            "scrape_url": {
                "description": "use this action to scrape any public web url for text you can use to respond to the user's prompt. the scraped text will be sent to you in a followup message for you to review",
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
            "commentary": {
                "description": "include any commentary about your actions or choices here so that the user can see it, while keeping your entire response valid json only",
                "params": {
                    "text": {
                        "description": "the text of your commentary",
                        "required": True
                    }
                }
            },
            "render_graph": {
                "description": "render a graphviz graph from a dotlang string",
                "params": {
                    "dotlang_string": {
                        "description": "the dotlang string to render. make sure the string is properly encoded for being inside a json object",
                        "required": True
                    }
                }
            },
            # DONT ENABLE THIS UNLESS YOU'RE OK WITH THE BOT BEING ABLE TO DELETE ALL MESSAGES IN A CONVO ON IT'S OWN
            # "clear": {
            #     "description": "erase all messages in the current conversation",
            #     "params": {}
            # }
        }
        return actions_list

    def get_actions_list_as_text(self):
        text = "\nResponse Actions:\n"
        i = 1
        for action_name, action in self.get_actions_list().items():
            text += "\n" + str(i) + ". {\"action\":\"" + str(action_name) + "\"";
            for param_name, param in action["params"].items():
                text += ", \"" + param_name + "\":\"\""
            text += "}"
            i += 1

        text += "\nhere is a description of each action type and their parameters:"
        i = 1
        for action_name, action in self.get_actions_list().items():
            text += "\n" + str(i) + ". " + action["description"]
            for param_name, param in action["params"].items():
                text += "\n\t" + param_name + ": " + param["description"]
            i += 1
        return text

