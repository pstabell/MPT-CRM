#!/usr/bin/env python3
"""
Run database migration for card images and addresses
"""

import os
from supabase import create_client

# Load environment
from dotenv import load_dotenv
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
    exit(1)

supabase = create_client(url, key)

# Read the migration SQL
with open("database/schema_update_v13_card_images_addresses.sql", "r") as f:
    migration_sql = f.read()

print("Applying migration: schema_update_v13_card_images_addresses.sql")
print("=" * 60)

# Split SQL into individual statements and execute them
statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

for i, statement in enumerate(statements):
    if statement.strip() and not statement.strip().startswith('--'):
        try:
            print(f"Executing statement {i+1}/{len(statements)}")
            print(f"SQL: {statement[:100]}..." if len(statement) > 100 else f"SQL: {statement}")
            
            result = supabase.rpc('exec_sql', {'sql': statement}).execute()
            print("✓ Success")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            # Continue with other statements
            
print("\nMigration completed!")
print("Note: If you see errors above, please run the SQL manually in Supabase SQL Editor.")