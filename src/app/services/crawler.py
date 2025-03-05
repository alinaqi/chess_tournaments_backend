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
from .database import get_database_client

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
        self.db_client = get_database_client()
        
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
        logger.debug(f"Starting to process {len(tournaments)} tournaments")
        
        # Enhance tournaments with LLM analysis
        enhanced_tournaments = await self.analyzer.analyze_tournaments(tournaments)
        logger.debug(f"Enhanced {len(enhanced_tournaments)} tournaments with AI analysis")
        
        # Save to database
        saved_tournaments = []
        for tournament in enhanced_tournaments:
            logger.debug(f"Processing tournament: {tournament.name}")
            # Check if tournament already exists
            exists = await self.db_client.check_tournament_exists(
                tournament.name, tournament.month, tournament.year
            )
            
            if not exists:
                # Insert new tournament
                result = await self.db_client.insert_tournament(tournament)
                logger.info(f"Saved new tournament: {tournament.name}")
                logger.debug(f"Insertion result: {result is not None}")
            else:
                logger.info(f"Tournament already exists: {tournament.name}")
            
            saved_tournaments.append(tournament)
        
        logger.debug(f"Completed processing tournaments. Saved count: {len(saved_tournaments)}")
        return saved_tournaments
    
    async def crawl(self) -> List[Tournament]:
        """
        Perform a single crawl operation: scrape, analyze, and save tournaments.
        
        Returns:
            List of processed Tournament objects
        """
        logger.info("Starting crawl operation")
        
        # Debug environment variables
        logger.info(f"USE_MOCK_DB = {os.getenv('USE_MOCK_DB')}")
        logger.info(f"SUPABASE_URL = {os.getenv('SUPABASE_URL') is not None}")
        logger.info(f"SUPABASE_KEY = {os.getenv('SUPABASE_KEY') is not None}")
        logger.info(f"SUPABASE_SERVICE_ROLE = {os.getenv('SUPABASE_SERVICE_ROLE') is not None}")
        logger.info(f"SUPABASE_TABLE_PREFIX = {os.getenv('SUPABASE_TABLE_PREFIX')}")
        logger.info(f"Database client class: {self.db_client.__class__.__name__}")
        
        try:
            # Step 1: Scrape tournaments
            tournaments = await self.scraper.scrape()
            if not tournaments:
                logger.warning("No tournaments found during scraping")
                # Record empty crawl history
                await self.db_client.record_crawl_history(0, "success")
                return []
            
            logger.info(f"Scraped {len(tournaments)} tournaments")
            
            # Step 2: Process tournaments
            processed_tournaments = await self.process_tournaments(tournaments)
            
            # Record successful crawl history
            await self.db_client.record_crawl_history(len(processed_tournaments), "success")
            
            logger.info(f"Crawl operation completed, processed {len(processed_tournaments)} tournaments")
            return processed_tournaments
        except Exception as e:
            logger.error(f"Crawl operation failed: {str(e)}")
            # Record failed crawl history
            await self.db_client.record_crawl_history(0, "failed", str(e))
            raise
    
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