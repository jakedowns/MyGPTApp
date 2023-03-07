# a class that can scrape a url and return the text (stripped of html tags)
# and the title of the page
import requests
from bs4 import BeautifulSoup
class UrlScraper:
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
        self.title = soup.title.string
        self.text = soup.get_text()