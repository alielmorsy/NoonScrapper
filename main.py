import asyncio
import logging
import json5
import argparse
import os
from htmlscrapper.search import NoonSearchScrapper
import time


# Load configuration from config.json using JSON5
def load_config(config_path="config.json"):
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            return json5.load(config_file)
    except FileNotFoundError:
        logging.error(f"Config file '{config_path}' not found. Using default configuration.")
        return {"connectionLimiter": 5, "maxWorkers": 12}
    except Exception as e:
        logging.error(f"Error decoding JSON5 in config file: {e}")
        raise


# Set up logging
def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Output to the console
            logging.FileHandler("app.log", encoding="utf-8")  # Output to a log file
        ]
    )
    # Suppress logs from external libraries
    logging.getLogger('httpx').setLevel(logging.CRITICAL)
    logging.getLogger('httpcore').setLevel(logging.CRITICAL)
    logging.getLogger('httpcore.http11').setLevel(logging.CRITICAL)


# Main function
async def main(query, output_path):
    start = time.time()

    # Load configuration
    config = load_config()
    connection_limiter = config["connectionLimiter"]
    max_workers = config["maxWorkers"]

    logging.info(f"Starting search with query: '{query}', output path: '{output_path}'")
    logging.debug(f"Configuration loaded: connectionLimiter={connection_limiter}, maxWorkers={max_workers}")

    # Perform search
    async with NoonSearchScrapper(config) as scrapper:
        await scrapper.search(query, output_path)

    end = time.time()
    taken = end - start
    logging.info(f"Search completed. Time taken: {taken:.2f}s")
    print(f"Time Taken: {taken:.2f}s")


if __name__ == '__main__':
    # Set up logging
    setup_logging()

    # Argument parsing
    parser = argparse.ArgumentParser(description="Search for products and save results to a CSV file.")
    parser.add_argument("query", type=str, help="Search query (can be Arabic)")
    parser.add_argument("--output", type=str, default="output.csv", help="Output CSV file path (default: output.csv)")
    args = parser.parse_args()

    # Run the main function
    asyncio.run(main(args.query, args.output))
