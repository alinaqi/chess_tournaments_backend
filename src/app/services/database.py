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
        self.crawl_history = []
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
    
    async def get_tournaments(self, filters: Optional[Dict[str, Any]] = None, pagination: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Retrieve tournaments from in-memory storage with optional filtering and pagination.
        
        Args:
            filters: Dictionary of filter criteria
            pagination: Dictionary with pagination parameters (page, page_size)
            
        Returns:
            Dictionary containing data, total count, and pages information
        """
        try:
            # Start with all tournaments
            result = self.tournaments
            
            # Apply filters if provided
            if filters:
                filtered_result = []
                for tournament in result:
                    match = True
                    
                    # Handle text search separately
                    if 'search' in filters:
                        search_term = filters['search'].lower()
                        search_match = False
                        # Search in name, description, and city
                        if ('name' in tournament and tournament['name'] and 
                            search_term in tournament['name'].lower()):
                            search_match = True
                        elif ('description' in tournament and tournament['description'] and 
                              search_term in tournament['description'].lower()):
                            search_match = True
                        elif ('city' in tournament and tournament['city'] and 
                              search_term in tournament['city'].lower()):
                            search_match = True
                        
                        if not search_match:
                            match = False
                            continue
                    
                    # Apply other filters
                    for key, value in filters.items():
                        if key == 'search':
                            continue  # Skip search as we handled it separately
                        
                        if key not in tournament or tournament[key] != value:
                            match = False
                            break
                    
                    if match:
                        filtered_result.append(tournament)
                result = filtered_result
            
            # Get total count before pagination
            total_count = len(result)
            
            # Apply pagination if provided
            if pagination:
                page = pagination.get('page', 1)
                page_size = pagination.get('page_size', 10)
                
                # Calculate slice indices
                start = (page - 1) * page_size
                end = min(start + page_size, len(result))
                
                # Slice the result
                result = result[start:end]
                
                # Calculate total pages
                total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
            else:
                total_pages = 1
            
            logger.info(f"Retrieved {len(result)} tournaments")
            
            # Return paginated results and metadata
            return {
                "data": result,
                "total": total_count,
                "pages": total_pages
            }
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

    async def get_available_categories(self) -> List[str]:
        """
        Retrieve all unique tournament categories from the in-memory database.
        
        Returns:
            List of unique category values
        """
        try:
            # Extract unique category values
            categories = [t.category for t in self.tournaments if t.category]
            
            # Return sorted unique values
            return sorted(list(set(categories)))
        except Exception as e:
            logger.error(f"Error retrieving available categories: {str(e)}")
            raise

    async def record_crawl_history(self, tournaments_count: int, status: str = "success", error: str = None) -> Dict[str, Any]:
        """
        Record a crawl operation in the mock crawl history.
        
        Args:
            tournaments_count: Number of tournaments processed
            status: Status of the crawl operation (success/failed)
            error: Error message if the crawl failed
            
        Returns:
            Dictionary with inserted crawl history data
        """
        try:
            # Create crawl history record
            crawl_data = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "tournaments_count": tournaments_count,
                "status": status
            }
            
            if error:
                crawl_data["error"] = error
                
            # Add to in-memory crawl history
            self.crawl_history.append(crawl_data)
            
            logger.info(f"Mock crawl history recorded: {status}, processed {tournaments_count} tournaments")
            return crawl_data
        except Exception as e:
            logger.error(f"Error recording mock crawl history: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "tournaments_count": tournaments_count,
                "status": "failed_to_record",
                "error": str(e)
            }

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
        Initialize the Supabase client.
        """
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            
            # Explicitly use the service role key to bypass RLS policies
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE")
            if not supabase_key:
                supabase_key = os.getenv("SUPABASE_KEY")
                logger.warning("SUPABASE_SERVICE_ROLE not found, using SUPABASE_KEY instead. This may cause RLS policy issues.")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase credentials not found in environment variables")
            
            logger.info(f"Initializing Supabase client with URL: {supabase_url} (key length: {len(supabase_key) if supabase_key else 0})")
            self.client = create_client(supabase_url, supabase_key)
            
            # Get table prefix
            self.table_prefix = os.getenv("SUPABASE_TABLE_PREFIX", "ct_")
            
            # Define all table names
            self.tournaments_table = f"{self.table_prefix}tournaments"
            self.categories_table = f"{self.table_prefix}tournament_categories"
            self.types_table = f"{self.table_prefix}tournament_types"
            self.crawl_history_table = f"{self.table_prefix}crawl_history"
            
            # Use tournaments table for backward compatibility
            self.table_name = self.tournaments_table
            
            logger.info(f"Supabase client initialized successfully. Using tables with prefix: {self.table_prefix}")
            
            # Test connection
            self._test_connection()
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    def _test_connection(self):
        """
        Test the Supabase connection by fetching a single row limit
        """
        try:
            # Try a simple query to verify connection
            response = self.client.table(self.table_name).select("id").limit(1).execute()
            logger.info("Supabase connection test successful")
        except Exception as e:
            logger.error(f"Supabase connection test failed: {str(e)}")
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
            
            # Remove id if it's None (let Supabase generate one)
            if 'id' in tournament_dict and tournament_dict['id'] is None:
                del tournament_dict['id']
            
            # Convert datetime objects to ISO format strings for JSON compatibility
            if 'start_date' in tournament_dict and tournament_dict['start_date']:
                tournament_dict['start_date'] = tournament_dict['start_date'].isoformat()
            if 'end_date' in tournament_dict and tournament_dict['end_date']:
                tournament_dict['end_date'] = tournament_dict['end_date'].isoformat()
            if 'created_at' in tournament_dict:
                tournament_dict['created_at'] = tournament_dict['created_at'].isoformat()
            if 'updated_at' in tournament_dict:
                tournament_dict['updated_at'] = tournament_dict['updated_at'].isoformat()
            
            # Log the data being inserted
            logger.debug(f"Attempting to insert tournament into {self.tournaments_table}: {tournament.name}")
            logger.debug(f"Tournament data: {tournament_dict}")
            
            # Insert data into Supabase
            response = self.client.table(self.tournaments_table).insert(tournament_dict).execute()
            
            # Extract the inserted record
            if response.data and len(response.data) > 0:
                inserted_record = response.data[0]
                logger.info(f"Tournament inserted: {tournament.name}")
                return inserted_record
            else:
                logger.warning(f"No data returned after inserting tournament: {tournament.name}")
                # Log the response for debugging
                logger.debug(f"Supabase response: {response}")
                return tournament_dict
        except Exception as e:
            # Special handling for RLS errors
            if "violates row-level security policy" in str(e):
                logger.error(f"RLS policy violation inserting tournament {tournament.name}. This usually means the Supabase key doesn't have permission to insert data.")
                logger.error(f"Check if you're using the service role key or if RLS policies are configured correctly.")
                
                # Try to check RLS settings
                try:
                    # Try a simple select to check if we can read at least
                    self.client.table(self.tournaments_table).select("id").limit(1).execute()
                    logger.info("Can read from the table but not write - likely an RLS policy issue")
                except Exception as e2:
                    logger.error(f"Also can't read from the table: {str(e2)}")
            
            # Log detailed error information
            logger.error(f"Error inserting tournament {tournament.name}: {str(e)}")
            logger.debug(f"Tournament data: {tournament_dict}")
            raise
    
    async def get_tournaments(self, filters: Optional[Dict[str, Any]] = None, pagination: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Retrieve tournaments from Supabase with optional filtering and pagination.
        
        Args:
            filters: Dictionary of filter criteria
            pagination: Dictionary with pagination parameters (page, page_size)
            
        Returns:
            Dictionary containing data, total count, and pages information
        """
        try:
            # Start with a base query
            query = self.client.table(self.tournaments_table).select('*', count='exact')
            
            # Apply text search if provided
            if filters and 'search' in filters:
                search_term = filters.pop('search')
                # Search in name and description fields
                query = query.or_(f"name.ilike.%{search_term}%,description.ilike.%{search_term}%,city.ilike.%{search_term}%")
            
            # Apply remaining filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Get total count first
            count_response = query.execute()
            total_count = count_response.count
            
            # Apply pagination if provided
            if pagination:
                page = pagination.get('page', 1)
                page_size = pagination.get('page_size', 10)
                
                # Calculate range and limits
                start = (page - 1) * page_size
                end = page * page_size - 1
                
                # Add range to query
                query = query.range(start, end)
                
                # Calculate total pages
                total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
            else:
                total_pages = 1
            
            # Execute the query
            response = query.execute()
            
            data = []
            if response.data:
                logger.info(f"Retrieved {len(response.data)} tournaments")
                data = response.data
            else:
                logger.info("No tournaments found")
            
            # Return paginated results and metadata
            return {
                "data": data,
                "total": total_count,
                "pages": total_pages
            }
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
            Updated tournament data dictionary
        """
        try:
            # Update the updated_at field
            data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update tournament in Supabase
            response = self.client.table(self.tournaments_table).update(data).eq('id', tournament_id).execute()
            
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
            Deleted tournament data dictionary
        """
        try:
            # First get the tournament to return it
            get_response = self.client.table(self.tournaments_table).select("*").eq('id', tournament_id).execute()
            
            if not get_response.data or len(get_response.data) == 0:
                logger.warning(f"Tournament not found for deletion: {tournament_id}")
                return {}
            
            deleted_tournament = get_response.data[0]
            
            # Delete tournament from Supabase
            response = self.client.table(self.tournaments_table).delete().eq('id', tournament_id).execute()
            
            logger.info(f"Tournament deleted: {tournament_id}")
            return deleted_tournament
        except Exception as e:
            logger.error(f"Error deleting tournament {tournament_id}: {str(e)}")
            raise
    
    async def check_tournament_exists(self, name: str, month: str, year: int) -> bool:
        """
        Check if a tournament with the same name, month, and year already exists.
        
        Args:
            name: Tournament name
            month: Tournament month
            year: Tournament year
            
        Returns:
            True if a matching tournament exists, False otherwise
        """
        try:
            # Query for matching tournament
            response = self.client.table(self.tournaments_table) \
                .select('id') \
                .eq('name', name) \
                .eq('month', month) \
                .eq('year', year) \
                .execute()
            
            # Return True if there are any results
            return response.data and len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking if tournament exists: {str(e)}")
            raise
    
    async def get_available_categories(self) -> List[str]:
        """
        Retrieve all unique tournament categories from the database.
        
        Returns:
            List of unique category values
        """
        try:
            # Try to get from categories table first
            response = self.client.table(self.categories_table).select('name').execute()
            
            if response.data and len(response.data) > 0:
                # Extract category names from the dedicated table
                categories = [item['name'] for item in response.data if 'name' in item]
                return sorted(categories)
            
            # Fallback: Extract from tournaments table if categories table is empty
            response = self.client.table(self.tournaments_table).select('category').execute()
            
            # Extract unique category values
            categories = []
            if response.data:
                categories = [item['category'] for item in response.data 
                             if 'category' in item and item['category']]
            
            # Return sorted unique values
            return sorted(list(set(categories)))
        except Exception as e:
            logger.error(f"Error retrieving available categories: {str(e)}")
            raise
    
    async def get_available_tournament_types(self) -> List[str]:
        """
        Retrieve all unique tournament types from the database.
        
        Returns:
            List of unique tournament type values
        """
        try:
            # Try to get from types table first
            response = self.client.table(self.types_table).select('name').execute()
            
            if response.data and len(response.data) > 0:
                # Extract type names from the dedicated table
                types = [item['name'] for item in response.data if 'name' in item]
                return sorted(types)
                
            # Fallback: Extract from tournaments table if types table is empty
            response = self.client.table(self.tournaments_table).select('tournament_type').execute()
            
            # Extract unique tournament type values
            types = []
            if response.data:
                types = [item['tournament_type'] for item in response.data 
                        if 'tournament_type' in item and item['tournament_type']]
            
            # Return sorted unique values
            return sorted(list(set(types)))
        except Exception as e:
            logger.error(f"Error retrieving available tournament types: {str(e)}")
            raise

    async def record_crawl_history(self, tournaments_count: int, status: str = "success", error: str = None) -> Dict[str, Any]:
        """
        Record a crawl operation in the crawl history table.
        
        Args:
            tournaments_count: Number of tournaments processed
            status: Status of the crawl operation (success/failed)
            error: Error message if the crawl failed
            
        Returns:
            Dictionary with inserted crawl history data
        """
        try:
            # Create crawl history record with only the columns that exist
            crawl_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "tournaments_count": tournaments_count,
                "status": status
            }
            
            # Only add error if the column exists and there is an error
            if error:
                # Check if the error column exists in the table
                try:
                    # Use a simple select to check if the column exists
                    self.client.table(self.crawl_history_table).select("error").limit(1).execute()
                    # If no error, the column exists
                    crawl_data["error"] = error
                except Exception as e:
                    logger.warning(f"Error column not found in {self.crawl_history_table} table: {str(e)}")
                    # If the error column doesn't exist, add the error to a message field if available
                    try:
                        self.client.table(self.crawl_history_table).select("message").limit(1).execute()
                        crawl_data["message"] = f"Error: {error}"
                    except:
                        # Neither error nor message columns exist
                        logger.warning(f"Neither error nor message columns found in {self.crawl_history_table}")
                
            # Insert into crawl history table
            response = self.client.table(self.crawl_history_table).insert(crawl_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Crawl history recorded: {status}, processed {tournaments_count} tournaments")
                return response.data[0]
            else:
                logger.warning(f"No data returned after inserting crawl history")
                return crawl_data
        except Exception as e:
            logger.error(f"Error recording crawl history: {str(e)}")
            # Don't raise the exception - we don't want crawl history recording to break the main flow
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "tournaments_count": tournaments_count,
                "status": "failed_to_record"
            }

def get_database_client():
    """
    Factory function to get the appropriate database client.
    Returns a MockDatabaseClient if Supabase credentials are not set,
    otherwise returns a SupabaseClient.
    """
    try:
        # Check if mock database is explicitly requested
        use_mock_db = os.getenv("USE_MOCK_DB", "false").lower() == "true"
        if use_mock_db:
            logger.info("Using mock database client (USE_MOCK_DB=true)")
            return MockDatabaseClient()
        
        # Check for Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE")
        if not supabase_key:
            supabase_key = os.getenv("SUPABASE_KEY")
            logger.warning("SUPABASE_SERVICE_ROLE not found, using SUPABASE_KEY instead. This may cause RLS policy issues.")
        
        if supabase_url and supabase_key:
            logger.info("Using Supabase database client")
            return SupabaseClient()
        else:
            logger.info("Using mock database client (Supabase credentials not found)")
            return MockDatabaseClient()
    except Exception as e:
        logger.error(f"Error creating database client: {str(e)}. Falling back to mock client.")
        return MockDatabaseClient() 