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
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.app.utils.logging_config import setup_logging
from src.app.services.database import SupabaseClient
from src.app.services.crawler import TournamentCrawler
from src.app.models.tournament import Tournament, TournamentResponse

# Load environment variables
load_dotenv()

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)  # Get the parent directory (the project root)

# Initialize FastAPI
app = FastAPI(
    title="Chess Tournament API",
    description="API for accessing chess tournament data from Schachinter.net",
    version="0.1.0"
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "app/static")), name="static")

# Set up templates
templates = Jinja2Templates(directory=os.path.join(current_dir, "app/templates"))

# Initialize database client
db_client = SupabaseClient()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main frontend page."""
    return templates.TemplateResponse("index.html", {"request": request})

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
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search text in tournament name and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Number of items per page")
):
    """
    Get a list of tournaments with optional filtering and pagination.
    
    Args:
        month: Filter by month (e.g., "January")
        year: Filter by year (e.g., 2025)
        is_international: Filter by international status
        tournament_type: Filter by tournament type (e.g., "Standard", "Rapid", "Blitz")
        category: Filter by category (e.g., "Open", "Women", "Youth", "Senior")
        search: Search text in tournament name and description
        page: Page number (starting from 1)
        page_size: Number of items per page
        
    Returns:
        List of tournaments matching the filter criteria with pagination metadata
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
        if search:
            filters["search"] = search
        
        # Add pagination parameters
        pagination = {
            "page": page,
            "page_size": page_size
        }
        
        # Query database
        tournaments_result = await db_client.get_tournaments(filters, pagination)
        
        # Return response
        return {
            "status": "success",
            "data": tournaments_result["data"],
            "meta": {
                "total": tournaments_result["total"],
                "page": page,
                "page_size": page_size,
                "pages": tournaments_result["pages"]
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving tournaments: {e}")
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
        months = sorted(set(tournament["month"] for tournament in tournaments_data["data"] if "month" in tournament))
        
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
        years = sorted(set(tournament["year"] for tournament in tournaments_data["data"] if "year" in tournament))
        
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
        categories = await db_client.get_available_categories()
        
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
        types = await db_client.get_available_tournament_types()
        
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