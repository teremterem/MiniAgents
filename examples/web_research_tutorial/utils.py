import asyncio
import os
import sys
from typing import Any
from concurrent.futures import ThreadPoolExecutor

import httpx
import miniagents

# pylint: disable=wrong-import-order
from dotenv import load_dotenv
from markdownify import markdownify as md
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.remote.client_config import ClientConfig

load_dotenv()

EXPECTED_MINIAGENTS_VERSION = (0, 0, 32)

BRIGHTDATA_SERP_API_CREDS = os.environ["BRIGHTDATA_SERP_API_CREDS"]
BRIGHTDATA_SCRAPING_BROWSER_CREDS = os.environ["BRIGHTDATA_SCRAPING_BROWSER_CREDS"]

BRIGHT_DATA_TIMEOUT = 20

# Allow only a limited number of concurrent web searches
searching_semaphore = asyncio.Semaphore(5)
# Allow only a limited number of concurrent web page scrapings
scraping_thread_pool = ThreadPoolExecutor(max_workers=4)


async def fetch_google_search(query: str) -> dict[str, Any]:
    async with searching_semaphore:
        async with httpx.AsyncClient(
            proxy=f"https://{BRIGHTDATA_SERP_API_CREDS}@brd.superproxy.io:33335",
            verify=False,
            timeout=BRIGHT_DATA_TIMEOUT,
        ) as client:
            response = await client.get(f"https://www.google.com/search?q={query}&brd_json=1")

    return response.json()


async def scrape_web_page(url: str) -> str:
    def _scrape_web_page_sync(url: str) -> str:
        client_config = ClientConfig(
            remote_server_addr="https://brd.superproxy.io:9515",
            username=BRIGHTDATA_SCRAPING_BROWSER_CREDS.split(":")[0],
            password=BRIGHTDATA_SCRAPING_BROWSER_CREDS.split(":")[1],
            timeout=BRIGHT_DATA_TIMEOUT,
        )
        sbr_connection = ChromiumRemoteConnection(
            client_config.remote_server_addr,
            "goog",
            "chrome",
            client_config=client_config,
        )
        with Remote(sbr_connection, options=ChromeOptions()) as driver:
            driver.get(url)
            return driver.page_source

    loop = asyncio.get_running_loop()
    # Selenium does not support asyncio, so we need to run it in a thread pool
    page_source = await loop.run_in_executor(scraping_thread_pool, _scrape_web_page_sync, url)
    return md(page_source)


def check_miniagents_version():
    try:
        miniagents_version: tuple[int, int, int] = tuple(map(int, miniagents.__version__.split(".")))
        valid_miniagents_version = miniagents_version >= EXPECTED_MINIAGENTS_VERSION
    except ValueError:
        # if any of the version components are not integers, we will consider it as an older version
        # (before 0.0.28 there were only numeric versions)
        valid_miniagents_version = True
    except AttributeError:
        # the absence of the __version__ attribute means that it is definitely an old version
        valid_miniagents_version = False

    if not valid_miniagents_version:
        print(
            "\n"
            f"You need MiniAgents v{'.'.join([str(v) for v in EXPECTED_MINIAGENTS_VERSION])} or later to run this "
            "example.\n"
            "\n"
            "Please update MiniAgents with `pip install -U miniagents`\n"
        )
        sys.exit(1)
