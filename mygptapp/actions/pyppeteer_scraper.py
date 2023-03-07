import asyncio
from pyppeteer import launch

class PyppeteerScraper:
    def __init__(self):
        self.browser = None
        self.page = None

    async def init(self):
        self.browser = await launch()
        self.page = await self.browser.newPage()

    async def scrape(self, url):
        await self.page.goto(url)
        html = await self.page.content()
        return html

    async def close(self):
        await self.browser.close()