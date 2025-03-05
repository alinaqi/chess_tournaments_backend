import logging
import os
import schedule
import time
from datetime import datetime
from typing import List, Optional
import asyncio
from dotenv import load_dotenv

from ..models.tournament import Tournament
from .scraper import SchachinterScraper
from .analyzer import TournamentAnalyzer
from .database import SupabaseClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class TournamentCrawler:
    """
    Orchestrator for the tournament crawling process.
    """
    
    def __init__(self):
        """
        Initialize the crawler with its dependencies.
        """
        self.scraper = SchachinterScraper()
        self.analyzer = TournamentAnalyzer()
        self.db_client = SupabaseClient()
        
        # Get crawl interval from environment variables (default to 24 hours)
        try:
            self.crawl_interval = int(os.getenv("CRAWL_INTERVAL", "24"))
        except ValueError:
            logger.warning("Invalid CRAWL_INTERVAL value, defaulting to 24 hours")
            self.crawl_interval = 24
    
    async def process_tournaments(self, tournaments: List[Tournament]) -> List[Tournament]:
        """
        Process a list of tournaments: enhance with LLM and save to database.
        
        Args:
            tournaments: List of Tournament objects to process
            
        Returns:
            List of processed Tournament objects
        """
        # Enhance tournaments with LLM analysis
        enhanced_tournaments = await self.analyzer.analyze_tournaments(tournaments)
        
        # Save to database
        saved_tournaments = []
        for tournament in enhanced_tournaments:
            # Check if tournament already exists
            exists = await self.db_client.check_tournament_exists(
                tournament.name, tournament.month, tournament.year
            )
            
            if not exists:
                # Insert new tournament
                await self.db_client.insert_tournament(tournament)
                logger.info(f"Saved new tournament: {tournament.name}")
            else:
                logger.info(f"Tournament already exists: {tournament.name}")
            
            saved_tournaments.append(tournament)
        
        return saved_tournaments
    
    async def crawl(self) -> List[Tournament]:
        """
        Perform a single crawl operation: scrape, analyze, and save tournaments.
        
        Returns:
            List of processed Tournament objects
        """
        logger.info("Starting crawl operation")
        
        # Step 1: Scrape tournaments
        tournaments = await self.scraper.scrape()
        if not tournaments:
            logger.warning("No tournaments found during scraping")
            return []
        
        logger.info(f"Scraped {len(tournaments)} tournaments")
        
        # Step 2: Process tournaments
        processed_tournaments = await self.process_tournaments(tournaments)
        
        logger.info(f"Crawl operation completed, processed {len(processed_tournaments)} tournaments")
        return processed_tournaments
    
    def start_scheduled_crawling(self):
        """
        Start scheduled crawling at the specified interval.
        """
        logger.info(f"Starting scheduled crawling every {self.crawl_interval} hours")
        
        # Define the job to run
        def job():
            logger.info(f"Running scheduled crawl at {datetime.now()}")
            asyncio.run(self.crawl())
        
        # Schedule the job
        schedule.every(self.crawl_interval).hours.do(job)
        
        # Run immediately on startup
        logger.info("Running initial crawl on startup")
        asyncio.run(self.crawl())
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Sleep for 1 minute between checks
    
    def run_once(self):
        """
        Run the crawler once without scheduling.
        """
        logger.info("Running single crawl operation")
        asyncio.run(self.crawl()) 