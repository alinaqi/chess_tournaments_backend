import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid
from supabase import create_client, Client

from ..models.tournament import Tournament

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class MockDatabaseClient:
    """
    Mock database client for testing purposes.
    Uses in-memory storage to simulate a database.
    """
    _instance = None
    
    def __new__(cls):
        """
        Implements the Singleton pattern to ensure only one database connection.
        """
        if cls._instance is None:
            cls._instance = super(MockDatabaseClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """
        Initialize the mock database.
        """
        self.tournaments = []
        logger.info("Mock database client initialized successfully")
    
    async def insert_tournament(self, tournament: Tournament) -> Dict[str, Any]:
        """
        Insert a new tournament into the mock database.
        
        Args:
            tournament: Tournament model instance
            
        Returns:
            Dictionary with inserted tournament data
        """
        try:
            # Convert Tournament to dictionary
            tournament_dict = tournament.dict(exclude_none=True)
            
            # Add an ID if not present
            if 'id' not in tournament_dict or not tournament_dict['id']:
                tournament_dict['id'] = str(uuid.uuid4())
            
            # Convert datetime objects to ISO format strings
            if 'start_date' in tournament_dict and isinstance(tournament_dict['start_date'], datetime):
                tournament_dict['start_date'] = tournament_dict['start_date'].isoformat()
            if 'end_date' in tournament_dict and isinstance(tournament_dict['end_date'], datetime):
                tournament_dict['end_date'] = tournament_dict['end_date'].isoformat()
            if 'created_at' in tournament_dict and isinstance(tournament_dict['created_at'], datetime):
                tournament_dict['created_at'] = tournament_dict['created_at'].isoformat()
            if 'updated_at' in tournament_dict and isinstance(tournament_dict['updated_at'], datetime):
                tournament_dict['updated_at'] = tournament_dict['updated_at'].isoformat()
            
            # Store in our list
            self.tournaments.append(tournament_dict)
            
            logger.info(f"Tournament inserted into mock DB: {tournament.name}")
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
                return self.tournaments
            
            filtered_tournaments = []
            for tournament in self.tournaments:
                matches = True
                for key, value in filters.items():
                    if key not in tournament or tournament[key] != value:
                        matches = False
                        break
                
                if matches:
                    filtered_tournaments.append(tournament)
            
            logger.info(f"Retrieved {len(filtered_tournaments)} tournaments from mock DB")
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
            
            # Find the tournament to update
            for i, tournament in enumerate(self.tournaments):
                if tournament.get('id') == tournament_id:
                    # Update the fields
                    self.tournaments[i].update(data)
                    logger.info(f"Tournament updated in mock DB: {tournament_id}")
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
            # Find the tournament to delete
            for i, tournament in enumerate(self.tournaments):
                if tournament.get('id') == tournament_id:
                    # Remove the tournament
                    deleted = self.tournaments.pop(i)
                    logger.info(f"Tournament deleted from mock DB: {tournament_id}")
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
                    logger.debug(f"Tournament already exists in mock DB: {name} ({month} {year})")
                    return True
            
            logger.debug(f"Tournament does not exist in mock DB: {name} ({month} {year})")
            return False
        except Exception as e:
            logger.error(f"Error checking tournament existence: {str(e)}")
            raise

class SupabaseClient:
    """
    Service class for interacting with Supabase database.
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
        Initialize the Supabase client with credentials from environment variables.
        """
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            # Use the service role key for admin access to bypass RLS policies
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE", os.getenv("SUPABASE_KEY"))
            
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
            
            self.client = create_client(supabase_url, supabase_key)
            self.table_name = os.getenv("SUPABASE_TABLE", "ct_tournaments")
            
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    async def insert_tournament(self, tournament: Tournament) -> Dict[str, Any]:
        """
        Insert a new tournament into Supabase.
        
        Args:
            tournament: Tournament model instance
            
        Returns:
            Dictionary with inserted tournament data
        """
        try:
            # Convert Tournament to dictionary
            tournament_dict = tournament.dict(exclude_none=True)
            
            # Convert datetime objects to ISO format strings for JSON compatibility
            if 'start_date' in tournament_dict and tournament_dict['start_date']:
                tournament_dict['start_date'] = tournament_dict['start_date'].isoformat()
            if 'end_date' in tournament_dict and tournament_dict['end_date']:
                tournament_dict['end_date'] = tournament_dict['end_date'].isoformat()
            if 'created_at' in tournament_dict:
                tournament_dict['created_at'] = tournament_dict['created_at'].isoformat()
            if 'updated_at' in tournament_dict:
                tournament_dict['updated_at'] = tournament_dict['updated_at'].isoformat()
            
            # Insert data into Supabase
            response = self.client.table(self.table_name).insert(tournament_dict).execute()
            
            # Extract the inserted record
            if response.data and len(response.data) > 0:
                inserted_record = response.data[0]
                logger.info(f"Tournament inserted: {tournament.name}")
                return inserted_record
            else:
                logger.warning(f"No data returned after inserting tournament: {tournament.name}")
                return tournament_dict
        except Exception as e:
            logger.error(f"Error inserting tournament {tournament.name}: {str(e)}")
            raise
    
    async def get_tournaments(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve tournaments from Supabase with optional filtering.
        
        Args:
            filters: Optional dictionary of filter conditions
            
        Returns:
            List of tournament dictionaries
        """
        try:
            query = self.client.table(self.table_name).select("*")
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Execute the query
            response = query.execute()
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} tournaments")
                return response.data
            else:
                logger.info("No tournaments found")
                return []
        except Exception as e:
            logger.error(f"Error retrieving tournaments: {str(e)}")
            raise
    
    async def update_tournament(self, tournament_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a tournament in Supabase.
        
        Args:
            tournament_id: ID of the tournament to update
            data: Dictionary of fields to update
            
        Returns:
            Dictionary with updated tournament data
        """
        try:
            # Update the updated_at field
            data['updated_at'] = datetime.utcnow().isoformat()
            
            # Execute the update operation
            response = self.client.table(self.table_name).update(data).eq('id', tournament_id).execute()
            
            if response.data and len(response.data) > 0:
                updated_record = response.data[0]
                logger.info(f"Tournament updated: {tournament_id}")
                return updated_record
            else:
                logger.warning(f"No data returned after updating tournament: {tournament_id}")
                return {}
        except Exception as e:
            logger.error(f"Error updating tournament {tournament_id}: {str(e)}")
            raise
    
    async def delete_tournament(self, tournament_id: str) -> Dict[str, Any]:
        """
        Delete a tournament from Supabase.
        
        Args:
            tournament_id: ID of the tournament to delete
            
        Returns:
            Dictionary with deleted tournament data
        """
        try:
            # First get the tournament to return it
            get_response = self.client.table(self.table_name).select("*").eq('id', tournament_id).execute()
            
            if not get_response.data or len(get_response.data) == 0:
                logger.warning(f"Tournament not found for deletion: {tournament_id}")
                return {}
            
            deleted_tournament = get_response.data[0]
            
            # Execute the delete operation
            self.client.table(self.table_name).delete().eq('id', tournament_id).execute()
            
            logger.info(f"Tournament deleted: {tournament_id}")
            return deleted_tournament
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
            response = self.client.table(self.table_name).select("id") \
                .eq('name', name) \
                .eq('month', month) \
                .eq('year', year) \
                .execute()
            
            exists = response.data and len(response.data) > 0
            
            if exists:
                logger.debug(f"Tournament already exists: {name} ({month} {year})")
            else:
                logger.debug(f"Tournament does not exist: {name} ({month} {year})")
                
            return exists
        except Exception as e:
            logger.error(f"Error checking tournament existence: {str(e)}")
            raise

def get_database_client():
    """
    Factory function to get the appropriate database client.
    Returns a MockDatabaseClient if Supabase credentials are not set,
    otherwise returns a SupabaseClient.
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE", os.getenv("SUPABASE_KEY"))
        
        # Use mock client if credentials are not configured
        use_mock = not supabase_url or not supabase_key or os.getenv("USE_MOCK_DB", "false").lower() == "true"
        
        if use_mock:
            logger.info("Using mock database client")
            return MockDatabaseClient()
        else:
            logger.info("Using Supabase database client")
            return SupabaseClient()
    except Exception as e:
        logger.warning(f"Error creating database client: {str(e)}. Falling back to mock client.")
        return MockDatabaseClient() 