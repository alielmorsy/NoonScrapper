# Web Scraping & Data Processing Task For Noon

## Overview

NoonScrapper is a high-performance web scraping tool designed specifically for extracting search results from Noon.

It works by:

1. Performing an initial search query to retrieve the content of the first page and determine the total number of pages.
2. Using `asyncio` and `httpx.AsyncClient` with a connection limiter to efficiently scrape multiple pages concurrently,
   reducing the chances of being rate-limited.

This tool is ideal for gathering large datasets quickly while maintaining performance and reliability.

## Setup

### Prerequisites

- Python 3.11 or higher
- `pip` (Python Package manger)

### Installation Steps

- Create a virtual environment (venv) `python -m venv venv`
- Active the environment

 ```bash
source  venv/Scripts/activate
```

- Install requirements

```bash
pip install -r requirments.txt
```

## Usage

### Basic Command

```bash
python main.py query --output result.csv 
```

- Use quotes (") around queries with spaces or special characters.
- Replace "query" with your desired search term (e.g., "ابل" for Arabic).
- The --output flag specifies the output file name (default: `output.csv`).

### Example

```bash
python main.py "آيفون 14" --output iphone_14.csv
```

## Configuration

The script supports a JSON configuration file (config.json) to customize its behavior.

> Note: It's json5 to support comments.

### Example

```json5
{
  "connectionLimiter": 12,
  "maxWorkers": 12,
  //Very, very important, because noon blocked me while testing on a general search query,
  "maxPages": 20,
  //Timeout in seconds for httpx
  "requestTimeout": 30
}
```

### Keys:

- `connectionLimiter`: How many connections at the same time.
- `maxWorkers`: How many parsing workers running at the same time.
- `maxPages`: Some search queries has up to 200 page which will result to a rate limiting trigger.
- `requestTimeout`: Timeout per request. High number is used for higher number of connections running at the same time.

## Notes:

- This project doesn't use any kind of multiprocessing. Instead, It utilizes both async for the http requesting and
  ThreadPool for the HTML parsing.

- All pages are requested at the same time in `search` function but due to the `asyncio.Semaphore` mechanism which is
  similar to atomic counter with mutex in threading, We can get the highest performance possible.
- ThreadPool in our case is faster than Multiprocessing in our case for simple reason. My choice for the parsing library
  was `lxml`. This library written in Cython and after reading the source code it unlocks the `GIL` (Global Lock
  Interpreter) which idle for multipage parsing on the same thread.

## Future Improvements

- Use `uvloop` instead of `asyncio` default loop, `uvloop` was optimized better for async http requests.
- Allow continuing from the last page to tackle the rating issue.
- Use socks5 proxies to gather all info at once avoiding any rate limiting issues.

## My Notes

- Unfortunately I didn't have time to put data inside `SQLite` but its kinda easy just set up the driver and run a
  simple SQL insert on my products.
- I am not aware of any websites that uses `React` or `vue`,...etc. For dynamic page loading which kinda make sense,
  Most websites depend on `Next.js`, `Remix` which render the products list on the server components 
