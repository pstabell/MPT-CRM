#!/usr/bin/env python3
"""
Apply Schema Update v16 for Projects Full Implementation
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
with open("database/schema_update_v16_projects_full_implementation.sql", "r") as f:
    migration_sql = f.read()

print("Applying Projects Module Full Implementation Schema...")
print("=" * 60)

# Execute SQL via psql-style approach (for manual execution)
print("""
To apply this schema update:
1. Copy the contents of database/schema_update_v16_projects_full_implementation.sql
2. Open Supabase SQL Editor at: https://supabase.com/dashboard/project/qgtjpdviboxxlrivwcan/sql
3. Paste the SQL and execute it

The schema includes:
- Enhanced projects table columns (project_type, hourly_rate, estimated_hours, actual_hours, mc_task_id)
- project_contacts table for team management
- project_files table for file attachments
- Performance indexes
- Database comments

""")

# Test database connectivity
try:
    projects = supabase.table("projects").select("id").limit(1).execute()
    print("SUCCESS: Database connection verified")
    print(f"Found {len(projects.data)} projects in database")
except Exception as e:
    print(f"ERROR: Database connection failed: {e}")
    
print("\nSchema application required for full functionality.")
print("After applying schema, restart Streamlit app to use new features.")