#!/usr/bin/env python3
"""
REST API for the chess tournament crawler.

This module provides HTTP endpoints to access and manage tournament data.
"""

import logging
import sys
import os
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Depends
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.utils.logging_config import setup_logging
from app.services.database import SupabaseClient
from app.services.crawler import TournamentCrawler
from app.models.tournament import Tournament, TournamentResponse

# Load environment variables
load_dotenv()

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Chess Tournament API",
    description="API for accessing chess tournament data from Schachinter.net",
    version="0.1.0"
)

# Initialize database client
db_client = SupabaseClient()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is up and running"}

@app.get("/api/tournaments", response_model=TournamentResponse)
async def get_tournaments(
    month: Optional[str] = Query(None, description="Filter by month"),
    year: Optional[int] = Query(None, description="Filter by year"),
    is_international: Optional[bool] = Query(None, description="Filter by international status"),
    tournament_type: Optional[str] = Query(None, description="Filter by tournament type"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get a list of tournaments with optional filtering.
    
    Args:
        month: Filter by month (e.g., "January")
        year: Filter by year (e.g., 2025)
        is_international: Filter by international status
        tournament_type: Filter by tournament type (e.g., "Standard", "Rapid", "Blitz")
        category: Filter by category (e.g., "Open", "Women", "Youth", "Senior")
        
    Returns:
        List of tournaments matching the filter criteria
    """
    try:
        # Prepare filters
        filters = {}
        if month:
            filters["month"] = month
        if year:
            filters["year"] = year
        if is_international is not None:
            filters["is_international"] = is_international
        if tournament_type:
            filters["tournament_type"] = tournament_type
        if category:
            filters["category"] = category
        
        # Query database
        tournaments_data = await db_client.get_tournaments(filters)
        
        # Convert to Tournament objects
        tournaments = [Tournament(**tournament) for tournament in tournaments_data]
        
        return {
            "status": "success",
            "data": tournaments,
            "count": len(tournaments)
        }
    except Exception as e:
        logger.error(f"Error retrieving tournaments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawl")
async def trigger_crawl():
    """
    Manually trigger a crawl operation.
    
    Returns:
        Summary of the crawl operation
    """
    try:
        crawler = TournamentCrawler()
        tournaments = await crawler.crawl()
        
        return {
            "status": "success",
            "message": "Crawl operation completed successfully",
            "tournaments_processed": len(tournaments)
        }
    except Exception as e:
        logger.error(f"Error during manual crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/months")
async def get_available_months():
    """
    Get a list of available months in the database.
    
    Returns:
        List of unique months
    """
    try:
        tournaments_data = await db_client.get_tournaments()
        months = sorted(set(tournament["month"] for tournament in tournaments_data if "month" in tournament))
        
        return {
            "status": "success",
            "data": months
        }
    except Exception as e:
        logger.error(f"Error retrieving months: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/years")
async def get_available_years():
    """
    Get a list of available years in the database.
    
    Returns:
        List of unique years
    """
    try:
        tournaments_data = await db_client.get_tournaments()
        years = sorted(set(tournament["year"] for tournament in tournaments_data if "year" in tournament))
        
        return {
            "status": "success",
            "data": years
        }
    except Exception as e:
        logger.error(f"Error retrieving years: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
async def get_available_categories():
    """
    Get a list of available tournament categories.
    
    Returns:
        List of unique categories
    """
    try:
        tournaments_data = await db_client.get_tournaments()
        categories = sorted(set(tournament["category"] for tournament in tournaments_data 
                              if "category" in tournament and tournament["category"]))
        
        return {
            "status": "success",
            "data": categories
        }
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tournament-types")
async def get_available_tournament_types():
    """
    Get a list of available tournament types.
    
    Returns:
        List of unique tournament types
    """
    try:
        tournaments_data = await db_client.get_tournaments()
        types = sorted(set(tournament["tournament_type"] for tournament in tournaments_data 
                         if "tournament_type" in tournament and tournament["tournament_type"]))
        
        return {
            "status": "success",
            "data": types
        }
    except Exception as e:
        logger.error(f"Error retrieving tournament types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 