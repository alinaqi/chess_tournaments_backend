import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from ..models.tournament import Tournament

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SupabaseClient:
    """
    Mock Service class for simulating Supabase database interactions.
    This is a simplified version for testing that doesn't require a real database connection.
    """
    _instance = None
    
    def __new__(cls):
        """
        Implements the Singleton pattern to ensure only one database connection.
        """
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """
        Initialize the mock database.
        """
        try:
            # Create an in-memory store for tournaments
            self.tournaments = []
            logger.info("Mock database client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize mock database: {str(e)}")
            raise
    
    async def insert_tournament(self, tournament: Tournament) -> Dict[str, Any]:
        """
        Insert a new tournament into the mock database.
        
        Args:
            tournament: Tournament model instance
            
        Returns:
            Dictionary with inserted tournament data
        """
        try:
            tournament_dict = tournament.dict(exclude_none=True)
            
            # Add unique ID
            tournament_dict['id'] = str(uuid.uuid4())
            
            # Convert datetime objects to ISO format
            if 'start_date' in tournament_dict and tournament_dict['start_date']:
                tournament_dict['start_date'] = tournament_dict['start_date'].isoformat()
            if 'end_date' in tournament_dict and tournament_dict['end_date']:
                tournament_dict['end_date'] = tournament_dict['end_date'].isoformat()
            if 'created_at' in tournament_dict:
                tournament_dict['created_at'] = tournament_dict['created_at'].isoformat()
            if 'updated_at' in tournament_dict:
                tournament_dict['updated_at'] = tournament_dict['updated_at'].isoformat()
                
            self.tournaments.append(tournament_dict)
            logger.info(f"Tournament inserted: {tournament.name}")
            return tournament_dict
        except Exception as e:
            logger.error(f"Error inserting tournament {tournament.name}: {str(e)}")
            raise
    
    async def get_tournaments(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve tournaments from the mock database with optional filtering.
        
        Args:
            filters: Optional dictionary of filter conditions
            
        Returns:
            List of tournament dictionaries
        """
        try:
            if not filters:
                logger.info(f"Retrieved {len(self.tournaments)} tournaments")
                return self.tournaments
            
            # Apply filters
            filtered_tournaments = []
            for tournament in self.tournaments:
                match = True
                for key, value in filters.items():
                    if key not in tournament or tournament[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_tournaments.append(tournament)
            
            logger.info(f"Retrieved {len(filtered_tournaments)} tournaments with filters")
            return filtered_tournaments
        except Exception as e:
            logger.error(f"Error retrieving tournaments: {str(e)}")
            raise
    
    async def update_tournament(self, tournament_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a tournament in the mock database.
        
        Args:
            tournament_id: ID of the tournament to update
            data: Dictionary of fields to update
            
        Returns:
            Dictionary with updated tournament data
        """
        try:
            # Update the updated_at field
            data['updated_at'] = datetime.utcnow().isoformat()
            
            for i, tournament in enumerate(self.tournaments):
                if tournament.get('id') == tournament_id:
                    self.tournaments[i].update(data)
                    logger.info(f"Tournament updated: {tournament_id}")
                    return self.tournaments[i]
            
            logger.warning(f"Tournament not found for update: {tournament_id}")
            return {}
        except Exception as e:
            logger.error(f"Error updating tournament {tournament_id}: {str(e)}")
            raise
    
    async def delete_tournament(self, tournament_id: str) -> Dict[str, Any]:
        """
        Delete a tournament from the mock database.
        
        Args:
            tournament_id: ID of the tournament to delete
            
        Returns:
            Dictionary with deleted tournament data
        """
        try:
            for i, tournament in enumerate(self.tournaments):
                if tournament.get('id') == tournament_id:
                    deleted = self.tournaments.pop(i)
                    logger.info(f"Tournament deleted: {tournament_id}")
                    return deleted
            
            logger.warning(f"Tournament not found for deletion: {tournament_id}")
            return {}
        except Exception as e:
            logger.error(f"Error deleting tournament {tournament_id}: {str(e)}")
            raise
    
    async def check_tournament_exists(self, name: str, month: str, year: int) -> bool:
        """
        Check if a tournament with the given name, month, and year already exists.
        
        Args:
            name: Tournament name
            month: Tournament month
            year: Tournament year
            
        Returns:
            True if the tournament exists, False otherwise
        """
        try:
            for tournament in self.tournaments:
                if (tournament.get('name') == name and 
                    tournament.get('month') == month and 
                    tournament.get('year') == year):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking tournament existence: {str(e)}")
            raise 