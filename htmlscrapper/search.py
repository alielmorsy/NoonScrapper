import asyncio
import logging
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Dict, Optional

import lxml.html
import tqdm
from lxml import html

import httpx

from htmlscrapper.utils import _get_item_counter, extract_products, write_to_disk

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

logger = logging.getLogger(__name__)


class NoonSearchScrapper:
    BASE_URL = "https://www.noon.com/egypt-ar/"

    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=30)
        # Semaphore is a non-safe thread counter that count how many tasks are running at once (similar to locking but with atomic counter)
        self.connection_limiter = asyncio.Semaphore(value=config["connectionLimiter"])
        self.final_url: Optional[httpx.URL] = None

    # Running it inside context to ensure the client is closed probably
    async def __aenter__(self):
        # Fetch cookies using the connection limiter
        async with self.connection_limiter:
            try:
                response = await self.client.get(self.BASE_URL, follow_redirects=True)
                response.raise_for_status()  # Raise for HTTP errors
                self.final_url = response.url
            except httpx.HTTPStatusError as e:
                await self.client.aclose()  # Ensure client is closed
                raise e
            except Exception as e:
                await self.client.aclose()
                raise RuntimeError(f"Failed to initialize scraper: {e}")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.aclose()

    async def search(self, query: str, output_path: str):
        # Fetching page one
        first_page_text = await self.request_page(query, None)
        page_count = _get_item_counter(first_page_text)
        logger.info(f"Found {page_count} page(s)")
        if page_count > 1:
            max_pages = self.config["maxPages"]
            max_pages = max(max_pages, 1)
            page_count = min(page_count, max_pages)
            async with self.connection_limiter:
                logger.info(
                    f"Requesting all products from {page_count} page with limit {self.config['connectionLimiter']}")
                # Starting from two because we already scrapped the first page.
                pages_coroutines = [self.request_page(query, page_number) for page_number in range(2, page_count)]
                results = await asyncio.gather(*pages_coroutines)
                results.insert(0, first_page_text)
        else:
            results = [first_page_text]
        if all(result is None for result in results):
            raise RuntimeError(f"No results found for query: {query}. (No request sent Okay status)")

        logger.info(f"Start parsing {page_count} page(s)")
        products = self.parse(results)

        # Product paths are relative, So we need to join them with the found absloute URL.
        for product in products:
            product["path"] = str(self.final_url.join(product["path"]))
        write_to_disk(output_path, products)

    async def request_page(self, query: str, page_number: Optional[int]):
        params = {"q": query}
        if page_number is not None:
            params["page"] = page_number
            logger.debug(f"Requesting page {page_number}")

        response = await self.client.get(self.final_url.join("search/"), params=params)
        if response.status_code != 200:
            logger.error(f"Failed to fetch results for page {page_number}")
            return None
        return response.text

    def parse(self, results):
        if len(results) == 1:
            # No need for any sort of threading in case it just one page
            return extract_products(results[0])
        products = []
        with ThreadPoolExecutor(max_workers=self.config["maxWorkers"]) as worker:
            futures = [worker.submit(extract_products, result) for result in results]
            for page_number, future in tqdm.tqdm(enumerate(as_completed(futures), 1), total=len(results)):
                try:
                    result = future.result()
                    products += result
                except Exception as e:
                    logger.exception(f"Failed to extract products from page {page_number}", e)
        return products
