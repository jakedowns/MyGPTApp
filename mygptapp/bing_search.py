import requests

class BingSearchAPI:
    def __init__(self, api_key, endpoint='https://api.bing.microsoft.com/v7.0/search'):
        self.api_key = api_key
        self.endpoint = endpoint

    def searchAndReturnTopNResults(self, query, n=3):
        # Set the query parameters
        params = {
            'q': query,
            'count': n,
            #'responseFilter': 'WebPages',
            #'textDecorations': True,
            #'textFormat': 'HTML',
            'mkt': 'en-US',
            'api-version': '7.0'
        }

        # Set the request headers
        headers = {
            'Ocp-Apim-Subscription-Key': self.api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        # Send the request and get the response
        response = requests.get(self.endpoint, params=params, headers=headers)
        data = response.json()

        # check for errors
        if response.status_code != 200:
            message = "error"

            # extract bing web search api error
            if "error" in data:
                if "message" in data["error"]:
                    message = data["error"]["message"]

            return {
                'error': {
                    'code': response.status_code,
                    'message': message
                }
            }

        # Extract the top n web results
        results = []
        for result in data['webPages']['value'][:n]:
            results.append({
                'name': result['name'],
                'url': result['url'],
                'snippet': result['snippet']
            })

        return results
