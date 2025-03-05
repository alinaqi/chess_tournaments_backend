#!/usr/bin/env python3
"""
Main entry point for the chess tournament crawler.

This script starts the crawler to periodically fetch and analyze chess tournament
information from Schachinter.net.
"""

import argparse
import logging
import sys
import os
import asyncio
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.utils.logging_config import setup_logging
from app.services.crawler import TournamentCrawler

# Load environment variables
load_dotenv()

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Chess Tournament Crawler for Schachinter.net'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run the crawler once and exit'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        help='Crawl interval in hours (overrides environment variable)'
    )
    
    return parser.parse_args()

def main():
    """Main function that starts the crawler."""
    args = parse_args()
    
    # Initialize the crawler
    crawler = TournamentCrawler()
    
    # Override interval if provided as argument
    if args.interval:
        crawler.crawl_interval = args.interval
        logger.info(f"Crawl interval set to {crawler.crawl_interval} hours from command line")
    
    try:
        # Run crawler once or start scheduled execution
        if args.once:
            logger.info("Running crawler once as requested")
            crawler.run_once()
        else:
            logger.info(f"Starting scheduled crawling every {crawler.crawl_interval} hours")
            crawler.start_scheduled_crawling()
    except KeyboardInterrupt:
        logger.info("Crawler stopped by user")
    except Exception as e:
        logger.error(f"Crawler failed with error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 