#!/usr/bin/env python3
"""
Test script for database operations.

This script tests whether the crawler correctly saves data to the database.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.app.utils.logging_config import setup_logging
from src.app.services.database import SupabaseClient
from src.app.services.crawler import TournamentCrawler
from src.app.models.tournament import Tournament

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

async def test_db_operations():
    """Test basic database operations."""
    logger.info("Starting database test")
    
    # Create a database client
    db_client = SupabaseClient()
    logger.info("Database client initialized")
    
    # Create a test tournament
    test_tournament = Tournament(
        name="Test Tournament",
        month="January",
        year=2025,
        is_international=False,
        city="Berlin",
        country="Germany",
        tournament_type="Standard",
        category="Open"
    )
    logger.info(f"Created test tournament: {test_tournament.name}")
    
    # Check if the tournament exists
    exists = await db_client.check_tournament_exists(
        test_tournament.name, test_tournament.month, test_tournament.year
    )
    logger.info(f"Tournament exists check before insert: {exists}")
    
    # Insert the tournament
    if not exists:
        result = await db_client.insert_tournament(test_tournament)
        logger.info(f"Tournament inserted with ID: {result.get('id')}")
    
    # Get all tournaments
    tournaments = await db_client.get_tournaments()
    logger.info(f"Retrieved {len(tournaments)} tournaments")
    
    # Print them out
    for idx, tournament in enumerate(tournaments):
        logger.info(f"Tournament {idx+1}: {tournament.get('name')} ({tournament.get('month')} {tournament.get('year')})")
    
    # Check if our test tournament exists now
    exists_now = await db_client.check_tournament_exists(
        test_tournament.name, test_tournament.month, test_tournament.year
    )
    logger.info(f"Tournament exists check after insert: {exists_now}")
    
    logger.info("Database test completed")

async def test_crawler_operations():
    """Test crawler operations including database save."""
    logger.info("Starting crawler test")
    
    # Create a crawler
    crawler = TournamentCrawler()
    logger.info("Crawler initialized")
    
    # Run a test crawl operation
    tournaments = await crawler.crawl()
    logger.info(f"Crawler returned {len(tournaments)} tournaments")
    
    # Check if tournaments were added to the database
    db_client = SupabaseClient()
    db_tournaments = await db_client.get_tournaments()
    logger.info(f"Database now has {len(db_tournaments)} tournaments")
    
    logger.info("Crawler test completed")

async def main():
    """Main test function."""
    try:
        # Test database operations
        await test_db_operations()
        
        # Test crawler operations
        await test_crawler_operations()
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test stopped by user") 