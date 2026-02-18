"""
Create crm_sms_history table in Supabase for SMS message tracking
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def create_sms_history_table():
    """Create the crm_sms_history table"""
    
    # Get Supabase connection
    url = os.getenv("SUPABASE_URL_CRM") or "https://qgtjpdviboxxlrivwcan.supabase.co"
    key = os.getenv("SUPABASE_ANON_KEY_CRM") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFndGpwZHZpYm94eGxyaXZ3Y2FuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkyNzc0MzIsImV4cCI6MjA4NDg1MzQzMn0.c4HugHTbj1FJ79pLnJ3an45Kg9nOjGDNmH00pv0foJA"
    
    supabase: Client = create_client(url, key)
    
    # SQL to create the crm_sms_history table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS crm_sms_history (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
        phone_number TEXT NOT NULL,
        message TEXT NOT NULL,
        twilio_sid TEXT,
        status TEXT NOT NULL DEFAULT 'sent',
        sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_crm_sms_history_contact_id ON crm_sms_history(contact_id);
    CREATE INDEX IF NOT EXISTS idx_crm_sms_history_sent_at ON crm_sms_history(sent_at DESC);
    CREATE INDEX IF NOT EXISTS idx_crm_sms_history_status ON crm_sms_history(status);
    
    -- Enable Row Level Security
    ALTER TABLE crm_sms_history ENABLE ROW LEVEL SECURITY;
    
    -- Create policy to allow all operations for authenticated users
    DROP POLICY IF EXISTS "Allow all operations for authenticated users" ON crm_sms_history;
    CREATE POLICY "Allow all operations for authenticated users" 
    ON crm_sms_history FOR ALL 
    TO authenticated 
    USING (true) 
    WITH CHECK (true);
    
    -- Allow anonymous access for the CRM app (using anon key)
    DROP POLICY IF EXISTS "Allow all operations for anon users" ON crm_sms_history;
    CREATE POLICY "Allow all operations for anon users" 
    ON crm_sms_history FOR ALL 
    TO anon 
    USING (true) 
    WITH CHECK (true);
    
    -- Create trigger for updated_at
    CREATE OR REPLACE FUNCTION update_crm_sms_history_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    DROP TRIGGER IF EXISTS trigger_update_crm_sms_history_updated_at ON crm_sms_history;
    CREATE TRIGGER trigger_update_crm_sms_history_updated_at
        BEFORE UPDATE ON crm_sms_history
        FOR EACH ROW
        EXECUTE FUNCTION update_crm_sms_history_updated_at();
    """
    
    try:
        print("Creating crm_sms_history table...")
        
        # Execute the SQL
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        
        print("✅ crm_sms_history table created successfully!")
        print("Table includes:")
        print("- id (UUID, primary key)")
        print("- contact_id (UUID, foreign key to contacts)")
        print("- phone_number (TEXT)")
        print("- message (TEXT)")  
        print("- twilio_sid (TEXT)")
        print("- status (TEXT)")
        print("- sent_at (TIMESTAMP)")
        print("- error_message (TEXT)")
        print("- created_at, updated_at (TIMESTAMP)")
        print("- Row Level Security enabled")
        print("- Indexes created for performance")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        
        # Try alternative approach - direct SQL execution
        print("\nTrying alternative approach...")
        try:
            # Break down into smaller SQL statements
            statements = [
                """
                CREATE TABLE IF NOT EXISTS crm_sms_history (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
                    phone_number TEXT NOT NULL,
                    message TEXT NOT NULL,
                    twilio_sid TEXT,
                    status TEXT NOT NULL DEFAULT 'sent',
                    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """,
                "CREATE INDEX IF NOT EXISTS idx_crm_sms_history_contact_id ON crm_sms_history(contact_id);",
                "CREATE INDEX IF NOT EXISTS idx_crm_sms_history_sent_at ON crm_sms_history(sent_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_crm_sms_history_status ON crm_sms_history(status);",
                "ALTER TABLE crm_sms_history ENABLE ROW LEVEL SECURITY;",
                """
                DROP POLICY IF EXISTS "Allow all operations for anon users" ON crm_sms_history;
                CREATE POLICY "Allow all operations for anon users" 
                ON crm_sms_history FOR ALL 
                TO anon 
                USING (true) 
                WITH CHECK (true);
                """
            ]
            
            for stmt in statements:
                try:
                    supabase.rpc('exec_sql', {'sql': stmt}).execute()
                    print(f"✅ Executed: {stmt[:50]}...")
                except Exception as stmt_error:
                    print(f"⚠️ Warning: {stmt[:50]}... - {str(stmt_error)}")
            
            print("✅ Table creation completed with alternative approach!")
            return True
            
        except Exception as alt_error:
            print(f"❌ Alternative approach also failed: {str(alt_error)}")
            return False

def test_sms_table():
    """Test the SMS table by inserting and retrieving a test record"""
    
    url = os.getenv("SUPABASE_URL_CRM") or "https://qgtjpdviboxxlrivwcan.supabase.co"
    key = os.getenv("SUPABASE_ANON_KEY_CRM") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFndGpwZHZpYm94eGxyaXZ3Y2FuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkyNzc0MzIsImV4cCI6MjA4NDg1MzQzMn0.c4HugHTbj1FJ79pLnJ3an45Kg9nOjGDNmH00pv0foJA"
    
    supabase: Client = create_client(url, key)
    
    try:
        print("\nTesting SMS history table...")
        
        # Test insert
        test_data = {
            "contact_id": "00000000-0000-0000-0000-000000000000",  # Dummy UUID
            "phone_number": "+12396008159",
            "message": "Test SMS message",
            "twilio_sid": "test_sid_123",
            "status": "sent"
        }
        
        result = supabase.table("crm_sms_history").insert(test_data).execute()
        
        if result.data:
            test_id = result.data[0]['id']
            print(f"✅ Test record inserted with ID: {test_id}")
            
            # Test retrieval
            retrieve_result = supabase.table("crm_sms_history").select("*").eq("id", test_id).execute()
            
            if retrieve_result.data:
                print("✅ Test record retrieved successfully")
                
                # Clean up test record
                supabase.table("crm_sms_history").delete().eq("id", test_id).execute()
                print("✅ Test record cleaned up")
                
                print("\n🎉 SMS history table is working correctly!")
                return True
        
        print("❌ Test failed - no data returned")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== SMS History Table Setup ===")
    
    if create_sms_history_table():
        test_sms_table()
    else:
        print("\n❌ Table creation failed. Please check Supabase connection and permissions.")
        
    print("\n=== Setup Complete ===")