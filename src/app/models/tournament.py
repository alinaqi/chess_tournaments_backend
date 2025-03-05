from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Tournament(BaseModel):
    """
    Pydantic model for chess tournament data.
    """
    id: Optional[str] = Field(None, description="Unique identifier for the tournament")
    name: str = Field(..., description="Name of the tournament")
    month: str = Field(..., description="Month when the tournament takes place")
    year: int = Field(..., description="Year when the tournament takes place")
    start_date: Optional[datetime] = Field(None, description="Start date of the tournament")
    end_date: Optional[datetime] = Field(None, description="End date of the tournament")
    is_international: bool = Field(False, description="Whether the tournament is international or national")
    city: Optional[str] = Field(None, description="City where the tournament takes place")
    country: Optional[str] = Field(None, description="Country where the tournament takes place")
    tournament_type: Optional[str] = Field(None, description="Type of tournament (Standard, Rapid, Blitz, etc.)")
    category: Optional[str] = Field(None, description="Category (Open, Women, Senior, Youth, etc.)")
    website_url: Optional[str] = Field(None, description="URL for the tournament's website")
    description: Optional[str] = Field(None, description="Description or additional information")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when this record was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when this record was last updated")

    class Config:
        """Configuration for the Tournament model."""
        json_schema_extra = {
            "example": {
                "name": "DSAM Chess Festival",
                "month": "April",
                "year": 2025,
                "is_international": True,
                "city": "Berlin",
                "country": "Germany",
                "tournament_type": "Standard",
                "category": "Open",
                "website_url": "https://example.com/tournament"
            }
        }


class PaginationMeta(BaseModel):
    """
    Pydantic model for pagination metadata.
    """
    total: int = Field(..., description="Total number of items available")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class TournamentResponse(BaseModel):
    """
    Pydantic model for API responses containing tournament data with pagination.
    """
    status: str = "success"
    data: List[Any]  # Using Any to accommodate both Tournament objects and raw dictionaries
    meta: Optional[PaginationMeta] = None 