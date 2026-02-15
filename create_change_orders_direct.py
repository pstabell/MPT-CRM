from db_service import get_db

def create_change_orders_table():
    """Create the change_orders table"""
    db = get_db()
    
    try:
        # First, let's just verify we can connect
        print("Testing database connection...")
        response = db.table('contacts').select('id').limit(1).execute()
        print(f"Connected successfully. Found {len(response.data)} contacts.")
        
        # Since we can't execute DDL directly, let's test if the table exists
        try:
            response = db.table('change_orders').select('id').limit(1).execute()
            print("change_orders table already exists!")
            return True
        except Exception as e:
            if 'does not exist' in str(e) or 'not found' in str(e).lower():
                print("change_orders table does not exist - needs to be created in Supabase SQL Editor")
                print("\nPlease run this SQL in Supabase SQL Editor:")
                print("""
CREATE TABLE IF NOT EXISTS public.change_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'implemented')),
    requested_by TEXT,
    approved_by TEXT,
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    estimated_hours DECIMAL(10,2),
    hourly_rate DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    mission_control_card_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.change_orders ENABLE ROW LEVEL SECURITY;

-- Create RLS policy
CREATE POLICY "Enable all operations for authenticated users" ON public.change_orders
FOR ALL USING (auth.role() = 'authenticated');
                """)
                return False
            else:
                print(f"Unexpected error: {e}")
                return False
                
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    create_change_orders_table()