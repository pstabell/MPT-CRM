# DRIP CAMPAIGN SETUP - MANUAL STEPS REQUIRED

## Status: Item #001 - SendGrid API & MPT Domain Setup

✅ **COMPLETED:**
- Created .env file with SendGrid configuration
- Set up database connection to CRM Supabase
- Configured MPT domain (metropointtech.com) as sender domain
- Verified drip tables exist in database

⏳ **REQUIRES MANUAL INTERVENTION:**

### 1. Run SQL Migration in Supabase Dashboard
**Required:** Go to https://supabase.com/dashboard/project/qgtjpdviboxxlrivwcan
1. Navigate to SQL Editor
2. Run the complete migration from `drip_migration.sql`
3. This will:
   - Fix RLS policies for anon access
   - Insert 4 campaign templates (Networking, Lead, Prospect, Client)
   - Set up proper permissions

### 2. Get SendGrid API Key
**Required:** Set up SendGrid account and get API key
1. Go to https://sendgrid.com
2. Create account or log in with patrick@metropointtechnology.com
3. Generate API key with full mail send permissions
4. Update `.env` file: `SENDGRID_API_KEY=SG.actual-api-key-here`

### 3. Verify MPT Domain in SendGrid
**Required:** Add metropointtech.com as authenticated sender domain
1. In SendGrid dashboard → Sender Authentication
2. Add domain: metropointtech.com  
3. Follow DNS setup instructions
4. Verify domain ownership

## Next Steps After Manual Setup:
- Run `python populate_drip_templates.py` to verify templates loaded
- Test email sending with `python simple_drip_test.py`
- Enable drip campaigns in CRM UI

## Files Modified:
- ✅ `.env` - SendGrid config added
- ✅ `DRIP_SETUP_REQUIRED.md` - This setup guide

## Ready to Continue With:
- Item #002: UI integration for contact drip toggle
- Item #004: Audit existing drip code
- Item #008: Port drip engine to MPT-CRM