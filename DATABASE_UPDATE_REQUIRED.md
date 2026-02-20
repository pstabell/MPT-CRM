# Database Schema Update Required

## Overview
The CRM Contact Detail Page has been overhauled with a new SharePoint Files section. To fully enable this feature, a new column needs to be added to the `contacts` table.

## Required Database Change

### SQL Command
```sql
ALTER TABLE contacts ADD COLUMN sharepoint_folder_url TEXT;
```

## Steps to Apply

### Option 1: Supabase Dashboard (Recommended)
1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Navigate to the **SQL Editor** 
3. Run the SQL command above
4. Verify the column was added by checking the **Table Editor** for the `contacts` table

### Option 2: Via psql (Advanced)
If you have direct database access:
```bash
psql -h your-supabase-host -U your-user -d your-database -c "ALTER TABLE contacts ADD COLUMN sharepoint_folder_url TEXT;"
```

## Impact

### Before Adding Column
- SharePoint Files section will show "No SharePoint folder URL set" for all contacts
- Users can still use the "Edit SharePoint Folder URL" feature
- Changes will be saved locally but not persisted to database
- No errors or crashes - the application handles the missing column gracefully

### After Adding Column
- Full SharePoint Files functionality enabled
- URLs can be saved and persisted across sessions
- "Open SharePoint Folder" links will work properly

## Updated Contact Table Schema

After the update, the `contacts` table will have these columns:
- id
- type
- first_name
- last_name
- company
- email
- phone
- source
- source_detail
- tags
- notes
- email_status
- created_at
- updated_at
- last_contacted
- archived
- card_image_url
- **sharepoint_folder_url** (NEW)

## Feature Details

The new SharePoint Files section includes:
1. **Always visible section** at the top of contact details
2. **Open Folder button** when URL is set
3. **Collapsible editor** to set/change the SharePoint URL
4. **Proper URL validation** and formatting

## Contact Detail Page Changes

The contact detail sections are now ordered as:
1. 📁 **SharePoint Files** (always visible at top)
2. ✏️ **Add a Note** (input area with button)  
3. 📜 **Notes History** (grows downward infinitely)

## Notes Format Update

Notes now use improved formatting:
- Each note starts with: `**[MM/DD/YYYY HH:MM AM/PM]**` (Eastern time)
- Clear separator lines (`---`) between entries
- Newest notes appear at TOP
- Notes grow downward with no sections below