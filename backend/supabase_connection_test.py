#!/usr/bin/env python3
"""
Supabase Connection and Table Verification
Verifies your Supabase connection and checks if the expected tables exist
"""

import os
import sys
import supabase
from dotenv import load_dotenv
import requests
import json

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase URL and API key are required.")
        print("Make sure they are defined in your .env file.")
        sys.exit(1)
    
    print(f"Supabase URL: {supabase_url}")
    print(f"Key available: {'Yes' if supabase_key else 'No'}")
    print(f"Service key available: {'Yes' if service_key else 'No'}")
    
    # Initialize Supabase client
    print("\nTesting Supabase connection...")
    try:
        client = supabase.create_client(supabase_url, supabase_key)
        print("✅ Connection successful")
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        sys.exit(1)
    
    # List all tables in the database using the REST API
    print("\nListing database tables...")
    tables_to_check = ["users", "questions", "answers"]
    
    # Try using service key if available
    api_key = service_key if service_key else supabase_key
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get list of all tables
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        
        # Try with direct SQL query if using service key
        if service_key:
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/execute_sql",
                headers=headers,
                json={"query": tables_query}
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    tables = [row['table_name'] for row in result]
                    print(f"Found {len(tables)} tables: {', '.join(tables)}")
                except:
                    print(f"Error parsing response: {response.text}")
            else:
                print(f"❌ Failed to list tables: HTTP {response.status_code}")
                print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error listing tables: {str(e)}")
    
    # Check each expected table
    print("\nChecking specific tables:")
    for table in tables_to_check:
        try:
            # Try to get a record count from the table
            response = client.table(table).select("count", count="exact").execute()
            
            if hasattr(response, 'count'):
                print(f"✅ Table '{table}' exists with {response.count} records")
            else:
                # If we got data but no count, the table exists but count failed
                print(f"✅ Table '{table}' exists")
        except Exception as e:
            print(f"❌ Table '{table}' error: {str(e)}")
    
    # Try to insert a test system user if it's missing
    print("\nChecking system user...")
    try:
        # Check if system user exists
        response = client.table("users").select("*").eq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        if response.data and len(response.data) > 0:
            print("✅ System user found")
        else:
            print("⚠️ System user not found, trying to create it...")
            
            # Create the system user
            system_user = {
                "id": "00000000-0000-0000-0000-000000000000",
                "username": "System",
                "created_at": "2023-01-01T00:00:00Z"
            }
            
            insert_response = client.table("users").insert(system_user).execute()
            
            if insert_response.data and len(insert_response.data) > 0:
                print("✅ System user created successfully")
            else:
                print(f"❌ Failed to create system user: {insert_response}")
    except Exception as e:
        print(f"❌ Error checking/creating system user: {str(e)}")
    
    print("\nVerification complete!")

if __name__ == "__main__":
    main()