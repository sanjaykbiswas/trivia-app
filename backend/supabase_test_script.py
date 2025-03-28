#!/usr/bin/env python3
"""
Test script to verify Supabase connection and user creation
Run this directly from your backend directory:
python supabase_test.py
"""

import asyncio
import os
from dotenv import load_dotenv
import supabase

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in your .env file")
    exit(1)

print(f"Using Supabase URL: {SUPABASE_URL}")
print(f"Using Supabase Key: {SUPABASE_KEY[:5]}...{SUPABASE_KEY[-5:]}")

# Create Supabase client
client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n--- Testing Supabase Connection ---")

# Test basic connection by querying a few users
try:
    response = client.table("users").select("*").limit(5).execute()
    print(f"Successfully connected to Supabase!")
    print(f"Retrieved {len(response.data)} users")
    
    if response.data:
        print("Sample user data:")
        for i, user in enumerate(response.data):
            print(f"  User {i+1}: ID={user.get('id')}, Username={user.get('username')}")
    else:
        print("No users found in the database")
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    exit(1)

# Test user creation
print("\n--- Testing User Creation ---")
test_username = f"test_user_{os.urandom(4).hex()}"

try:
    # Create user data
    user_data = {
        "username": test_username,
        "is_temporary": True,
        "auth_provider": "none"
    }
    
    print(f"Attempting to create user: {test_username}")
    
    # Insert into users table
    response = client.table("users").insert(user_data).execute()
    
    if response.data:
        print(f"Successfully created user!")
        print(f"New user ID: {response.data[0].get('id')}")
        print(f"User data: {response.data[0]}")
    else:
        print(f"User creation failed - no data returned")
        if hasattr(response, 'error'):
            print(f"Error: {response.error}")
except Exception as e:
    print(f"Error creating user: {e}")

print("\nTest complete!")