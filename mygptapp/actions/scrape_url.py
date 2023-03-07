# a class that can scrape a url and return the text (stripped of html tags)
# and the title of the page
import requests
from bs4 import BeautifulSoup
from mygptapp import rules, db
from mygptapp.models import Message
from mygptapp.openai_api import OpenAIAPI

ai_api = OpenAIAPI()

class ScrapeURL:
    def __init__(self, url):
        self.url = url
        self.title = None
        self.text = None
        self.scrape(url)

    def scrape(self,url):
        # scrape the url and set the title and text attributes
        # use the requests and BeautifulSoup libraries
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        # if title is found, set it
        if soup.title and "string" in soup.title:
            self.title = soup.title.string
        self.text = soup.get_text()

    def process_scrape_results(self, original_prompt):
        # convert the self object to a message
        scrape_results_as_message = "Scrape Results for Url: " + self.url
        if self.title is not None:
            scrape_results_as_message += "\n"
            scrape_results_as_message += "title: " + self.title
        if self.text is not None:
            scrape_results_as_message += "\n"
            # cap the body text at N characters
            scrape_results_as_message += "body text: " + self.text[:3000]
        scrape_results_as_message += "\n------------------"
        scrape_results_as_message += "\n"

        # save the scrape message to the db
        scrape_message = Message(convo_id=1, user_id=1, content=scrape_results_as_message, is_inner_thought=False, role="system")
        db.session.add(scrape_message)
        db.session.commit()

        # bake scrape_results into a "chat"
        messages = []
        messages.append({"role": "user", "content": original_prompt})
        messages.append({"role": "system", "content": scrape_results_as_message})
        messages.append({"role": "system", "content": "See if you can respond to the base prompt now using the scrape results."+rules.get_response_rules_text()})

        print("calling the model with a followup prompt: ", messages)
        followup = ai_api.call_model(messages)
        followup["scrape_result_message"] = {
            "choices":[
                {
                    "message": {
                        "role": "system",
                        "content": scrape_results_as_message
                    }
                }
            ]
        }
        return followup