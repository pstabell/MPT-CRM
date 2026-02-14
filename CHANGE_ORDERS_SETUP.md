# Change Orders Setup Instructions

## Manual Database Setup Required

The Change Order Management System has been implemented but requires manual table creation in Supabase.

### Steps to Complete Setup:

1. **Open Supabase SQL Editor**
   - Go to: https://qgtjpdviboxxlrivwcan.supabase.co
   - Navigate to SQL Editor

2. **Execute Table Creation**
   - Copy the entire contents of `database/schema_update_v15_change_orders.sql`
   - Paste into SQL Editor and execute

3. **Verify Setup**
   - Run test script: `python create_change_orders_table.py`
   - Should confirm table exists and connection works

## Features Implemented

✅ **Database Schema**
- `change_orders` table with full workflow support
- Foreign key relationship to projects table
- Indexes for performance
- Auto-updating timestamps

✅ **Change Orders Page** (`pages/06_Change_Orders.py`)
- Complete CRUD operations
- Status filtering (draft/pending/approved/rejected/completed)
- Project filtering
- Approval workflow with buttons
- Financial calculations (hours × rate = total)
- Client approval tracking

✅ **Projects Integration**
- Change Orders section in project detail view
- Quick stats: total, pending, approved change orders
- Inline creation of new change orders
- Quick action buttons for status changes
- Link to full Change Orders page

✅ **Database Service Layer**
- All CRUD functions in `db_service.py`
- Automatic total amount calculation
- Project relationship queries
- Error handling and validation

## Change Order Workflow

1. **Draft** → Create and edit freely
2. **Pending** → Submit for approval (locked)
3. **Approved/Rejected** → Decision made
4. **Completed** → Work finished (approved only)

## Integration Points

- **Navigation**: Added to sidebar in all pages
- **Projects**: Embedded view in project details
- **Financial**: Automatic calculation of total amounts
- **Approval**: Client signature and approval tracking

## Next Steps After Table Creation

1. Test the Change Orders page
2. Create a sample change order
3. Test the approval workflow
4. Verify project integration works
5. Test filtering and search functionality

The system is fully functional once the database table is created.