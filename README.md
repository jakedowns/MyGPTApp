# MyGPTApp

A wrapper around the new ChatGPT-3.5 Turbo model:
https://platform.openai.com/docs/guides/chat

looking to add more such as: {"action":"request_execute_python", "code":""}

Current Features Added:
```
0. {"action":"request_clarification", "text":""}
1. {"action":"web_search", "query":""}
2. {"action":"search_inner_thoughts", "query":""}
3. {"action":"think", "thought":""}
4. {"action":"respond", "text":""}
5. {"action":"final_response", "text":""}
6. {"action":"respond_with_image", "image_url":""}
7. {"action":"scrape_url", "url":""}
8. {"action":"message_maintainer", "text":""}

here is a description of each action type:
0. request clarification from the user
        text: the text of the clarification request
1. search the web for a query, when this action is performed, the assistant will have the ability to invoke follow-up actions before responding to the user
        query: the query to search for
2. search your inner thoughts for a query
        query: the query to search for
3. think about a thought, save it to your inner_thoughts for later reference
        thought: the thought to think about
4. respond to the user's prompt
        text: the text of your response
5. final response for the current base prompt. use this to indicate you're done thinking and yeild control back to the user
        text: the text of your response
6. respond to the user's prompt with an image
        image_url: the url of the image to respond with
7. scrape a url for text
        url: the url to scrape
8. send a message to the maintainer
        text: the text of your message to the maintainer
```
