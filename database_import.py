import os
import datetime
from supabase import create_client, Client
from remove_duplicates import questions_for_supabase

# Initialize Supabase client using environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_ANON_KEY.")

supabase: Client = create_client(supabase_url, supabase_key)

# Perform a batch insert into the 'questions' table
response = supabase.table("questions").insert(questions_for_supabase).execute()

print("Batch upload response:", response)