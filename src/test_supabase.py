#!/usr/bin/env python3
"""
Simple test script for Supabase connection.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connection."""
    print("Testing Supabase connection...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    # Use service role key for admin access
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE", os.getenv("SUPABASE_KEY"))
    
    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY/SUPABASE_SERVICE_ROLE must be set in environment variables")
        return
    
    print(f"Using URL: {supabase_url}")
    print(f"Using key: {supabase_key[:5]}...{supabase_key[-5:]}")
    
    try:
        # Explicitly print all the parameters being passed
        print("Creating client with parameters:")
        print(f"- URL: {supabase_url}")
        print(f"- Key: {supabase_key[:5]}...{supabase_key[-5:]}")
        print(f"- Using service role key: {os.getenv('SUPABASE_SERVICE_ROLE') == supabase_key}")
        
        # Create client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test a simple query to verify connection
        print("Testing query...")
        
        # Use the correct table name
        table_name = os.getenv("SUPABASE_TABLE", "ct_tournaments")
        print(f"Using table name: {table_name}")
        
        try:
            # Try a simple query first to check if table exists
            response = supabase.table(table_name).select("*").limit(1).execute()
            print(f"Query response: {response}")
            print(f"Table {table_name} exists.")
            print("Connection successful!")
        except Exception as e:
            print(f"Error querying table: {str(e)}")
            print(f"Table {table_name} might not exist. Please create it in the Supabase dashboard.")
        
        return supabase
    except Exception as e:
        print(f"ERROR: Failed to connect to Supabase: {str(e)}")
        return None

if __name__ == "__main__":
    test_supabase_connection() 