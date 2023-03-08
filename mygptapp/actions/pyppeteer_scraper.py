import asyncio
from multiprocessing import Process, Queue
from pyppeteer import launch

class PyppeteerScraper:
    def __init__(self):
        self.browser = None
        self.page = None

    async def init(self):
        self.browser = await launch()
        self.page = await self.browser.newPage()

    def init_sync(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.init())

    async def scrape(self, url):
        await self.page.goto(url)
        html = await self.page.content()
        return html

    def scrape_sync(self, url):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        html = loop.run_until_complete(self.scrape(url))
        return html

    async def close(self):
        await self.browser.close()

    def scrape_to_queue(self, url, queue):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def scrape_async():
            await self.init()
            html = await self.scrape(url)
            queue.put(html)
            loop.stop()

        asyncio.ensure_future(scrape_async())
        loop.run_forever()
        self.browser.close()

    async def scrape_in_background(self, url):
        # Create a Queue object
        queue = Queue()

        # Create a PyppeteerScraper object and initialize it
        scraper = self
        #asyncio.run(scraper.init())

        # Start a new process to scrape the URL and write the HTML to the queue
        p = Process(target=scraper.scrape_to_queue, args=(url, queue))
        p.start()

        # Wait for the process to finish and get the HTML from the queue
        html = queue.get()
        p.join()

        # Do something with the HTML, such as print it
        return html