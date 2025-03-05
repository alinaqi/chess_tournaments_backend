#!/usr/bin/env python3
"""
Start the crawl4ai server.

This script initializes and starts the crawl4ai server for web crawling.
"""

import crawl4ai
import asyncio
import subprocess
import sys
import os
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def start_crawl4ai_server():
    """Start the crawl4ai server using the WebCrawler class."""
    try:
        # Create a WebCrawler instance
        logger.info("Initializing crawl4ai WebCrawler...")
        
        # Display available configurations and classes
        logger.info(f"Available crawl4ai classes: {dir(crawl4ai)}")

        # Initialize the crawler - we'll use the synchronous version
        crawler = crawl4ai.WebCrawler()
        
        # Start the server on the default port (11235)
        logger.info("Starting crawl4ai server on http://localhost:11235...")
        await crawler.start_server()
        
        # Keep the server running
        logger.info("Server started successfully. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting crawl4ai server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(start_crawl4ai_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user") 