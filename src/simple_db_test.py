#!/usr/bin/env python3
"""
Simplified test script for Supabase operations.
"""

import os
import json
from dotenv import load_dotenv
from datetime import datetime
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_operations():
    """Test basic Supabase operations directly."""
    print("Testing Supabase operations...")
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE", os.getenv("SUPABASE_KEY"))
    table_name = os.getenv("SUPABASE_TABLE", "ct_tournaments")
    
    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE must be set in environment variables")
        return
    
    print(f"Using URL: {supabase_url}")
    print(f"Using key: {supabase_key[:5]}...{supabase_key[-5:]}")
    print(f"Using table: {table_name}")
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("Supabase client created")
        
        # Create a test tournament
        current_time = datetime.utcnow().isoformat()
        test_tournament = {
            "name": "Test Tournament Direct",
            "month": "January",
            "year": 2025,
            "is_international": False,
            "city": "Berlin",
            "country": "Germany",
            "tournament_type": "Standard",
            "category": "Open",
            "created_at": current_time,
            "updated_at": current_time
        }
        print(f"Created test data: {json.dumps(test_tournament)}")
        
        # Check if the tournament exists
        print("Checking if tournament exists...")
        try:
            response = supabase.table(table_name).select("*") \
                .eq('name', test_tournament["name"]) \
                .eq('month', test_tournament["month"]) \
                .eq('year', test_tournament["year"]) \
                .execute()
            
            exists = response.data and len(response.data) > 0
            print(f"Tournament exists check: {exists}")
            
            if exists:
                print("Tournament already exists, not inserting again")
            else:
                # Insert the tournament
                print("Inserting tournament...")
                insert_response = supabase.table(table_name).insert(test_tournament).execute()
                print(f"Insert response: {insert_response}")
                
                if insert_response.data:
                    print(f"Tournament inserted with ID: {insert_response.data[0].get('id')}")
                else:
                    print("No data returned from insert operation")
        except Exception as e:
            print(f"Error checking/inserting tournament: {str(e)}")
        
        # Get all tournaments
        print("Fetching all tournaments...")
        try:
            response = supabase.table(table_name).select("*").execute()
            tournaments = response.data
            print(f"Retrieved {len(tournaments)} tournaments")
            
            # Print them out
            for idx, tournament in enumerate(tournaments):
                print(f"Tournament {idx+1}: {tournament.get('name')} ({tournament.get('month')} {tournament.get('year')})")
        except Exception as e:
            print(f"Error fetching tournaments: {str(e)}")
        
        print("Test completed")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_supabase_operations() 