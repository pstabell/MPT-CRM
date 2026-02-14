"""
db_service.py — Centralized Database Service Layer for MPT-CRM
==============================================================

THE SINGLE SOURCE OF TRUTH for ALL database operations.

Pages are UI-only islands. They import from here.
They NEVER import supabase or call .table() directly.

Architecture:
    ┌─────────────┐     ┌──────────────┐     ┌──────────┐
    │  Page (UI)  │ ──▸ │ db_service.py │ ──▸ │ Supabase │
    └─────────────┘     └──────────────┘     └──────────┘

How to add new DB operations:
    1. Add a function here with db_ prefix
    2. Add a docstring
    3. Import it in the page that needs it

Sections:
    1.  Connection
    2.  Contacts
    3.  Deals / Pipeline
    4.  Discovery / Intakes
    5.  Activities
    6.  Tasks
    7.  Time & Billing
    8.  Marketing / Campaigns
    9.  Business Cards / Storage
    10. Dashboard
    11. Settings / Export
    12. Service Tickets
    13. Drip Campaign / Scheduler
"""

import os
import json
import hashlib
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


# ============================================================
# 1. CONNECTION
# ============================================================

_supabase_client = None


def _create_supabase_client():
    """Internal: create a fresh Supabase client from environment variables."""
    if not SUPABASE_AVAILABLE:
        return None
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None


def get_db():
    """Get the Supabase database client (cached singleton).

    Creates the client once and reuses it for the lifetime of the process.
    Works in both Streamlit and Flask contexts.

    Returns:
        Supabase Client or None if unavailable.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    _supabase_client = _create_supabase_client()
    return _supabase_client


def reset_db_connection():
    """Reset the database connection, forcing a fresh client on next get_db() call.

    Use this when you need to reconnect (e.g., after credential changes).
    """
    global _supabase_client
    _supabase_client = None


def db_is_connected():
    """Check if the database is connected and available.

    Returns:
        bool: True if a Supabase client is available.
    """
    return get_db() is not None


def db_test_connection():
    """Test the database connection by running a lightweight query.

    Returns:
        tuple: (success: bool, message: str)
    """
    db = get_db()
    if not db:
        return False, "No database connection"
    try:
        db.table("deals").select("id").limit(1).execute()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)


# ============================================================
# 2. CONTACTS
# ============================================================

def db_get_contacts(include_archived=False):
    """Get all contacts from the database.

    Args:
        include_archived: If True, include archived contacts. Default False.

    Returns:
        list[dict]: List of contact records, or empty list on error.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("contacts").select("*").order("created_at", desc=True).execute()
        result = response.data if response.data else []
        if not include_archived and result:
            result = [c for c in result if not c.get('archived')]
        return result
    except Exception as e:
        print(f"[db_service] Error getting contacts: {e}")
        return []


def db_get_contact(contact_id):
    """Get a single contact by ID.

    Args:
        contact_id: The UUID of the contact.

    Returns:
        dict or None: The contact record, or None if not found.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("contacts").select("*").eq("id", contact_id).single().execute()
        return response.data
    except Exception as e:
        print(f"[db_service] Error getting contact {contact_id}: {e}")
        return None


def db_create_contact(contact_data):
    """Create a new contact record and auto-enroll in the appropriate drip campaign.

    Args:
        contact_data: dict with contact fields (first_name, last_name, etc.)

    Returns:
        dict or None: The created contact record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("contacts").insert(contact_data).execute()
        contact = response.data[0] if response.data else None
        
        # Auto-enroll in drip campaign based on contact type
        if contact:
            contact_type = (contact_data.get("type") or "").lower()
            if contact_type:
                try:
                    _auto_enroll_new_contact(contact["id"], contact_type)
                except Exception as e:
                    print(f"[db_service] Auto-enroll failed for new contact: {e}")
        
        return contact
    except Exception as e:
        print(f"[db_service] Error creating contact: {e}")
        return None


def _auto_enroll_new_contact(contact_id, contact_type):
    """Auto-enroll a newly created contact in the appropriate drip campaign."""
    campaign_map = {
        "networking": "networking-drip-6week",
        "lead": "lead-drip",
        "prospect": "prospect-drip",
        "client": "client-drip",
    }
    
    campaign_id = campaign_map.get(contact_type)
    if not campaign_id:
        return
    
    template = db_get_drip_campaign_template(campaign_id)
    if not template:
        print(f"[db_service] No campaign template for '{campaign_id}'")
        return
    
    email_sequence = template.get("email_sequence")
    if isinstance(email_sequence, str):
        try:
            email_sequence = json.loads(email_sequence)
        except Exception:
            email_sequence = []
    
    if not email_sequence:
        return
    
    schedule = _build_step_schedule(email_sequence)
    enrollment_data = {
        "contact_id": contact_id,
        "campaign_id": campaign_id,
        "campaign_name": template.get("name", campaign_id),
        "status": "active",
        "current_step": 0,
        "total_steps": len(email_sequence),
        "step_schedule": json.dumps(schedule),
        "source": "auto_enroll_on_create",
        "source_detail": f"New contact created with type '{contact_type}'",
        "emails_sent": 0,
        "next_email_scheduled": schedule[0]["scheduled_for"] if schedule else None
    }
    
    enrollment = db_create_enrollment(enrollment_data)
    if enrollment:
        db_log_activity(
            "campaign_enrolled",
            f"Auto-enrolled in {campaign_id} on contact creation.",
            contact_id
        )
        print(f"[db_service] Auto-enrolled contact {contact_id} in {campaign_id}")


def db_update_contact(contact_id, contact_data, skip_campaign_switch=False):
    """Update an existing contact.

    Args:
        contact_id: The UUID of the contact.
        contact_data: dict of fields to update.
        skip_campaign_switch: If True, do not auto-switch campaigns on type change.

    Returns:
        dict or None: The updated contact record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    previous_type = None
    if "type" in contact_data and not skip_campaign_switch:
        try:
            existing = db_get_contact(contact_id)
            previous_type = existing.get("type") if existing else None
        except Exception:
            previous_type = None
    try:
        response = db.table("contacts").update(contact_data).eq("id", contact_id).execute()
        updated = response.data[0] if response.data else None
        new_type = contact_data.get("type")
        if not skip_campaign_switch and updated and previous_type and new_type and new_type != previous_type:
            try:
                _handle_campaign_switch(contact_id, previous_type, new_type)
            except Exception as e:
                print(f"[db_service] Error switching campaigns for contact {contact_id}: {e}")
        return updated
    except Exception as e:
        print(f"[db_service] Error updating contact {contact_id}: {e}")
        return None


def db_delete_contact(contact_id):
    """Permanently delete a contact.

    Args:
        contact_id: The UUID of the contact.

    Returns:
        bool: True if deleted successfully.
    """
    db = get_db()
    if not db:
        return False
    try:
        db.table("contacts").delete().eq("id", contact_id).execute()
        return True
    except Exception as e:
        print(f"[db_service] Error deleting contact {contact_id}: {e}")
        return False


def db_archive_contact(contact_id):
    """Archive a contact (soft delete).

    Args:
        contact_id: The UUID of the contact.

    Returns:
        dict or None: The updated contact record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("contacts").update({
            "archived": True,
            "archived_at": datetime.now().isoformat()
        }).eq("id", contact_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error archiving contact {contact_id}: {e}")
        return None


def db_unarchive_contact(contact_id):
    """Restore an archived contact.

    Args:
        contact_id: The UUID of the contact.

    Returns:
        dict or None: The updated contact record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("contacts").update({
            "archived": False,
            "archived_at": None
        }).eq("id", contact_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error unarchiving contact {contact_id}: {e}")
        return None


def db_get_archived_contacts():
    """Get all archived contacts.

    Returns:
        list[dict]: List of archived contact records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("contacts").select("*").eq("archived", True).order("archived_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting archived contacts: {e}")
        return []


def db_update_contact_type(contact_id, contact_type):
    """Update a contact's type field (e.g., 'client', 'lead').

    Args:
        contact_id: The UUID of the contact.
        contact_type: The new type string.

    Returns:
        bool: True if updated successfully.
    """
    db = get_db()
    if not db:
        return False
    try:
        response = db.table("contacts").update({"type": contact_type}).eq("id", contact_id).execute()
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        print(f"[db_service] Error updating contact type: {e}")
        return False


def db_check_contact_exists(email):
    """Check if a contact with the given email already exists.

    Args:
        email: Email address to check.

    Returns:
        dict or None: The existing contact record, or None.
    """
    db = get_db()
    if not db or not email:
        return None
    try:
        response = db.table("contacts").select("id, first_name, last_name, email").eq("email", email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error checking contact exists: {e}")
        return None


def db_check_contacts_by_company(company_name):
    """Find contacts with similar company name (case-insensitive partial match).

    Args:
        company_name: Company name to search for.

    Returns:
        list[dict]: List of matching contacts.
    """
    db = get_db()
    if not db or not company_name:
        return []
    try:
        response = db.table("contacts").select(
            "id, first_name, last_name, email, company, phone"
        ).ilike("company", f"%{company_name}%").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error checking contacts by company: {e}")
        return []


def db_find_duplicate_contact(first_name, last_name, email, company):
    """Find an existing contact by email, name+company, or name only.

    Priority: email → name+company → name only.
    Used by mobile_scanner for dedup before creating contacts.

    Args:
        first_name: First name to search.
        last_name: Last name to search.
        email: Email to search (highest priority).
        company: Company to search (combined with name).

    Returns:
        dict or None: The first matching contact record, or None.
    """
    db = get_db()
    if not db:
        return None
    try:
        # Priority 1: Check by email (strongest match)
        if email:
            response = db.table("contacts").select("*").eq("email", email).execute()
            if response.data:
                return response.data[0]

        # Priority 2: Check by name + company
        if first_name and last_name and company:
            response = (
                db.table("contacts").select("*")
                .eq("first_name", first_name)
                .eq("last_name", last_name)
                .eq("company", company)
                .execute()
            )
            if response.data:
                return response.data[0]

        # Priority 3: Check by name only
        if first_name and last_name:
            response = (
                db.table("contacts").select("*")
                .eq("first_name", first_name)
                .eq("last_name", last_name)
                .execute()
            )
            if response.data:
                return response.data[0]

        return None
    except Exception as e:
        print(f"[db_service] Error finding duplicate contact: {e}")
        return None


def db_find_potential_duplicates(contact_id):
    """Find potential duplicate contacts for an existing contact.

    Matches on: name, company, email.

    Args:
        contact_id: The UUID of the source contact to find duplicates for.

    Returns:
        list[dict]: Potential duplicates with 'match_reasons' field added.
    """
    db = get_db()
    if not db:
        return []

    # Get the source contact
    try:
        response = db.table("contacts").select("*").eq("id", contact_id).single().execute()
        source = response.data
        if not source:
            return []
    except Exception:
        return []

    first_name = (source.get('first_name') or '').strip().lower()
    last_name = (source.get('last_name') or '').strip().lower()
    company = (source.get('company') or '').strip().lower()
    email = (source.get('email') or '').strip().lower()

    potential_duplicates = []
    seen_ids = {contact_id}

    try:
        all_contacts = db.table("contacts").select("*").neq("archived", True).execute()
        contacts = all_contacts.data if all_contacts.data else []

        for c in contacts:
            if c['id'] in seen_ids:
                continue

            c_first = (c.get('first_name') or '').strip().lower()
            c_last = (c.get('last_name') or '').strip().lower()
            c_company = (c.get('company') or '').strip().lower()
            c_email = (c.get('email') or '').strip().lower()

            match_reasons = []

            if first_name and last_name and c_first and c_last:
                if first_name == c_first and last_name == c_last:
                    match_reasons.append("Same name")

            if company and c_company and len(company) > 2:
                if company == c_company:
                    match_reasons.append("Same company")
                elif company in c_company or c_company in company:
                    match_reasons.append("Similar company")

            if email and c_email and '@' in email:
                if email == c_email:
                    match_reasons.append("Same email")

            if match_reasons:
                c['match_reasons'] = match_reasons
                potential_duplicates.append(c)
                seen_ids.add(c['id'])

        potential_duplicates.sort(key=lambda x: len(x.get('match_reasons', [])), reverse=True)
        return potential_duplicates
    except Exception as e:
        print(f"[db_service] Error finding duplicates: {e}")
        return []


def db_find_potential_duplicates_by_card(first_name, last_name, company, email):
    """Find potential duplicate contacts based on business card data.

    Matches on: name → company → email (priority ordered).

    Args:
        first_name: First name from the card.
        last_name: Last name from the card.
        company: Company from the card.
        email: Email from the card.

    Returns:
        list[dict]: Potential duplicates with 'match_reasons' and 'match_priority' fields.
    """
    db = get_db()
    if not db:
        return []

    first_name = (first_name or '').strip().lower()
    last_name = (last_name or '').strip().lower()
    company = (company or '').strip().lower()
    email = (email or '').strip().lower()

    potential_duplicates = []
    seen_ids = set()

    try:
        all_contacts = db.table("contacts").select(
            "id, first_name, last_name, email, company, phone, notes"
        ).neq("archived", True).execute()
        contacts = all_contacts.data if all_contacts.data else []

        for c in contacts:
            c_first = (c.get('first_name') or '').strip().lower()
            c_last = (c.get('last_name') or '').strip().lower()
            c_company = (c.get('company') or '').strip().lower()
            c_email = (c.get('email') or '').strip().lower()

            match_reasons = []
            match_priority = 0

            if first_name and last_name and c_first and c_last:
                if first_name == c_first and last_name == c_last:
                    match_reasons.append("Same name")
                    match_priority = 1

            if company and c_company and len(company) > 2:
                if company == c_company:
                    match_reasons.append("Same company")
                    if match_priority == 0:
                        match_priority = 2
                elif company in c_company or c_company in company:
                    match_reasons.append("Similar company")
                    if match_priority == 0:
                        match_priority = 3

            if email and c_email and '@' in email:
                if email == c_email:
                    match_reasons.append("Same email")
                    if match_priority == 0:
                        match_priority = 4

            if match_reasons:
                c['match_reasons'] = match_reasons
                c['match_priority'] = match_priority
                potential_duplicates.append(c)
                seen_ids.add(c['id'])

        potential_duplicates.sort(
            key=lambda x: (x.get('match_priority', 99), -len(x.get('match_reasons', [])))
        )
        return potential_duplicates
    except Exception as e:
        print(f"[db_service] Error finding card duplicates: {e}")
        return []


def db_merge_contacts(primary_id, secondary_id):
    """Merge secondary contact INTO primary contact.

    Transfers all related records (deals, intakes, activities, enrollments)
    from secondary to primary. Merges notes. Fills missing fields.
    Deletes the secondary contact after transfer.

    Args:
        primary_id: UUID of the contact to KEEP.
        secondary_id: UUID of the contact to absorb and DELETE.

    Returns:
        dict: {"success": bool, "message": str, "merged_counts": dict}
    """
    db = get_db()
    if not db:
        return {"success": False, "message": "Database not connected"}

    try:
        primary = db.table("contacts").select("*").eq("id", primary_id).single().execute().data
        secondary = db.table("contacts").select("*").eq("id", secondary_id).single().execute().data

        if not primary:
            return {"success": False, "message": "Primary contact not found"}
        if not secondary:
            return {"success": False, "message": "Secondary contact not found"}

        merged_counts = {
            "deals": 0,
            "intakes": 0,
            "activities": 0,
            "notes_merged": False
        }

        # 1. Transfer deals
        try:
            deals_response = db.table("deals").select("id").eq("contact_id", secondary_id).execute()
            if deals_response.data:
                for deal in deals_response.data:
                    db.table("deals").update({"contact_id": primary_id}).eq("id", deal['id']).execute()
                    merged_counts["deals"] += 1
        except Exception as e:
            print(f"[db_service] Error transferring deals: {e}")

        # 2. Transfer intakes
        try:
            intakes_response = db.table("client_intakes").select("id").eq("contact_id", secondary_id).execute()
            if intakes_response.data:
                for intake in intakes_response.data:
                    db.table("client_intakes").update({"contact_id": primary_id}).eq("id", intake['id']).execute()
                    merged_counts["intakes"] += 1
        except Exception as e:
            print(f"[db_service] Error transferring intakes: {e}")

        # 3. Transfer activities
        try:
            activities_response = db.table("activities").select("id").eq("contact_id", secondary_id).execute()
            if activities_response.data:
                for activity in activities_response.data:
                    db.table("activities").update({"contact_id": primary_id}).eq("id", activity['id']).execute()
                    merged_counts["activities"] += 1
        except Exception as e:
            print(f"[db_service] Error transferring activities: {e}")

        # 4. Transfer campaign enrollments
        try:
            enrollments_response = db.table("campaign_enrollments").select("id").eq("contact_id", secondary_id).execute()
            if enrollments_response.data:
                for enrollment in enrollments_response.data:
                    db.table("campaign_enrollments").update({"contact_id": primary_id}).eq("id", enrollment['id']).execute()
        except Exception:
            pass

        # 5. Merge notes
        primary_notes = primary.get('notes') or ''
        secondary_notes = secondary.get('notes') or ''

        if secondary_notes:
            merge_timestamp = datetime.now().strftime("%m/%d/%Y %I:%M %p")
            secondary_name = f"{secondary.get('first_name', '')} {secondary.get('last_name', '')}".strip()
            merge_header = f"**[{merge_timestamp}] Notes merged from: {secondary_name}**"

            if primary_notes:
                merged_notes = f"{merge_header}\n{secondary_notes}\n\n---\n\n{primary_notes}"
            else:
                merged_notes = f"{merge_header}\n{secondary_notes}"

            db.table("contacts").update({"notes": merged_notes}).eq("id", primary_id).execute()
            merged_counts["notes_merged"] = True

        # 6. Fill missing fields on primary from secondary
        fields_to_fill = ['phone', 'company', 'source', 'source_detail', 'card_image_url']
        update_data = {}
        for field in fields_to_fill:
            if not primary.get(field) and secondary.get(field):
                update_data[field] = secondary.get(field)

        # Merge tags
        primary_tags = primary.get('tags') or []
        secondary_tags = secondary.get('tags') or []
        if secondary_tags:
            combined_tags = list(set(primary_tags + secondary_tags))
            update_data['tags'] = combined_tags

        # Handle both having card images
        if primary.get('card_image_url') and secondary.get('card_image_url'):
            merge_timestamp = datetime.now().strftime("%m/%d/%Y %I:%M %p")
            secondary_name = f"{secondary.get('first_name', '')} {secondary.get('last_name', '')}".strip()
            image_note = f"\n\n**[{merge_timestamp}] Card image from merged contact {secondary_name}:**\n{secondary.get('card_image_url')}"
            current_notes = update_data.get('notes', primary.get('notes', '')) or ''
            update_data['notes'] = current_notes + image_note

        if update_data:
            db.table("contacts").update(update_data).eq("id", primary_id).execute()

        # 7. Log merge activity
        try:
            secondary_name = f"{secondary.get('first_name', '')} {secondary.get('last_name', '')}".strip()
            db.table("activities").insert({
                "type": "contact_merged",
                "description": (
                    f"Merged contact '{secondary_name}' into this contact. "
                    f"Transferred: {merged_counts['deals']} deals, "
                    f"{merged_counts['intakes']} discovery forms, "
                    f"{merged_counts['activities']} activities."
                ),
                "contact_id": primary_id
            }).execute()
        except Exception:
            pass

        # 8. Delete secondary contact
        db.table("contacts").delete().eq("id", secondary_id).execute()

        return {
            "success": True,
            "message": (
                f"Successfully merged contacts. Transferred: "
                f"{merged_counts['deals']} deals, "
                f"{merged_counts['intakes']} discovery forms, "
                f"{merged_counts['activities']} activities."
            ),
            "merged_counts": merged_counts
        }

    except Exception as e:
        return {"success": False, "message": f"Merge failed: {str(e)}"}


def db_get_contact_email_sends(contact_id, limit=5):
    """Get recent email sends for a contact.

    Args:
        contact_id: The UUID of the contact.
        limit: Max number of records to return.

    Returns:
        list[dict]: Email send records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("email_sends").select("*").eq(
            "contact_id", contact_id
        ).order("sent_at", desc=True).limit(limit).execute()
        return response.data or []
    except Exception:
        return []


def db_get_contact_activities(contact_id, limit=5):
    """Get recent activities for a contact.

    Args:
        contact_id: The UUID of the contact.
        limit: Max number of records to return.

    Returns:
        list[dict]: Activity records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("activities").select("*").eq(
            "contact_id", contact_id
        ).order("created_at", desc=True).limit(limit).execute()
        return response.data or []
    except Exception:
        return []


def db_get_contact_email(contact_id):
    """Get a contact's email and first name (lightweight query for projects).

    Args:
        contact_id: The UUID of the contact.

    Returns:
        dict or None: {'email': ..., 'first_name': ...} or None.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("contacts").select("email, first_name").eq(
            "id", contact_id
        ).single().execute()
        return response.data
    except Exception:
        return None


def db_get_unprocessed_cards():
    """Get contacts that were quick-captured and need processing.

    These are contacts with first_name starting with '[Unprocessed]'.

    Returns:
        list[dict]: Unprocessed card contact records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("contacts").select("*").ilike(
            "first_name", "[Unprocessed]%"
        ).order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting unprocessed cards: {e}")
        return []


# ============================================================
# 3. DEALS / PIPELINE
# ============================================================

def db_get_deals(include_contacts=False):
    """Get all deals from the database.

    Args:
        include_contacts: If True, join contacts table for name/company info.

    Returns:
        list[dict]: List of deal records, or empty list on error.
    """
    db = get_db()
    if not db:
        return []
    try:
        if include_contacts:
            response = db.table("deals").select(
                "*, contacts(id, first_name, last_name, company)"
            ).execute()
        else:
            response = db.table("deals").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting deals: {e}")
        return []


def db_create_deal(deal_data):
    """Create a new deal in the database.

    Args:
        deal_data: dict with deal fields (title, value, stage, etc.)

    Returns:
        dict or None: The created deal record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("deals").insert(deal_data).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[db_service] Error creating deal: {e}")
        return None


def db_update_deal(deal_id, deal_data):
    """Update an existing deal.

    Args:
        deal_id: The UUID of the deal.
        deal_data: dict of fields to update.

    Returns:
        dict or None: The updated deal record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("deals").update(deal_data).eq("id", deal_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[db_service] Error updating deal {deal_id}: {e}")
        return None


def db_update_deal_stage(deal_id, new_stage):
    """Update a deal's stage.

    Args:
        deal_id: The UUID of the deal.
        new_stage: The new stage string (e.g., 'qualified', 'won').

    Returns:
        bool: True if updated successfully.
    """
    db = get_db()
    if not db:
        return False
    try:
        response = db.table("deals").update({"stage": new_stage}).eq("id", deal_id).execute()
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        print(f"[db_service] Error updating deal stage: {e}")
        return False


def db_delete_deal(deal_id):
    """Delete a deal from the database.

    Args:
        deal_id: The UUID of the deal.

    Returns:
        bool: True if deleted successfully.
    """
    db = get_db()
    if not db:
        return False
    try:
        db.table("deals").delete().eq("id", deal_id).execute()
        return True
    except Exception as e:
        print(f"[db_service] Error deleting deal {deal_id}: {e}")
        return False


def db_get_deal_tasks(deal_id):
    """Get tasks associated with a deal.

    Args:
        deal_id: The UUID of the deal.

    Returns:
        list[dict]: List of deal task records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("deal_tasks").select("*").eq("deal_id", deal_id).execute()
        return response.data or []
    except Exception:
        return []


def db_add_deal_task(deal_id, title):
    """Add a task to a deal.

    Args:
        deal_id: The UUID of the deal.
        title: The task title.

    Returns:
        dict or None: The created task record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("deal_tasks").insert({
            "deal_id": deal_id,
            "title": title,
            "is_complete": False
        }).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None


def db_toggle_deal_task(task_id, is_complete):
    """Toggle a deal task's completion status.

    Args:
        task_id: The UUID of the task.
        is_complete: New completion status.

    Returns:
        bool: True if updated successfully.
    """
    db = get_db()
    if not db:
        return False
    try:
        db.table("deal_tasks").update({"is_complete": is_complete}).eq("id", task_id).execute()
        return True
    except Exception:
        return False


# ============================================================
# 4. DISCOVERY / INTAKES
# ============================================================

def db_get_intakes(contact_id=None):
    """Get client intake records with contact info joined.

    Args:
        contact_id: Optional. Filter by contact ID.

    Returns:
        list[dict]: List of intake records with nested contacts data.
    """
    db = get_db()
    if not db:
        return []
    try:
        query = db.table("client_intakes").select(
            "*, contacts(first_name, last_name, company)"
        ).order("intake_date", desc=True)
        if contact_id:
            query = query.eq("contact_id", contact_id)
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting intakes: {e}")
        return []


def db_get_intake(intake_id):
    """Get a single intake record with full contact info.

    Args:
        intake_id: The UUID of the intake.

    Returns:
        dict or None: The intake record with nested contacts(*), or None.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("client_intakes").select(
            "*, contacts(*)"
        ).eq("id", intake_id).single().execute()
        return response.data
    except Exception as e:
        print(f"[db_service] Error getting intake {intake_id}: {e}")
        return None


def db_create_intake(intake_data):
    """Create a new client intake record.

    Args:
        intake_data: dict with intake fields (contact_id, project_types, etc.)

    Returns:
        dict or None: The created intake record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("client_intakes").insert(intake_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error creating intake: {e}")
        return None


def db_update_intake(intake_id, intake_data):
    """Update an existing intake record.

    Args:
        intake_id: The UUID of the intake.
        intake_data: dict of fields to update.

    Returns:
        dict or None: The updated intake record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("client_intakes").update(intake_data).eq("id", intake_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error updating intake {intake_id}: {e}")
        return None


# ============================================================
# 5. ACTIVITIES
# ============================================================

def db_log_activity(activity_type, description, contact_id=None):
    """Log an activity event.

    Args:
        activity_type: Type string (e.g., 'call', 'email_sent', 'note').
        description: Human-readable description.
        contact_id: Optional UUID of the related contact.

    Returns:
        dict or None: The created activity record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        activity = {
            "type": activity_type,
            "description": description,
        }
        if contact_id:
            activity["contact_id"] = contact_id
        response = db.table("activities").insert(activity).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None


def db_get_activities(limit=5):
    """Get the most recent activities.

    Args:
        limit: Max number of activities to return.

    Returns:
        list[dict]: Recent activity records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("activities").select("*").order(
            "created_at", desc=True
        ).limit(limit).execute()
        return response.data or []
    except Exception:
        return []


# ============================================================
# 6. TASKS
# ============================================================

def db_get_tasks(due_date=None):
    """Get incomplete tasks, optionally filtered by due date.

    Args:
        due_date: Optional. Only return tasks due on or before this date string.

    Returns:
        list[dict]: Task records.
    """
    db = get_db()
    if not db:
        return []
    try:
        query = db.table("tasks").select("*").neq("status", "completed")
        if due_date:
            query = query.lte("due_date", due_date)
        response = query.order("due_date").execute()
        return response.data or []
    except Exception:
        return []


# ============================================================
# 7. TIME & BILLING
# ============================================================

def db_get_projects():
    """Get all projects from the database.

    Returns:
        list[dict]: Project records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("projects").select("*").execute()
        return response.data or []
    except Exception:
        return []


def db_get_time_entries():
    """Get all time entries with project info joined.

    Returns:
        list[dict]: Time entry records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("time_entries").select(
            "*, projects(id, name, client_id)"
        ).execute()
        return response.data or []
    except Exception:
        return []


def db_create_time_entry(entry_data):
    """Create a new time entry.

    Args:
        entry_data: dict with entry fields (project_id, hours, description, etc.)

    Returns:
        dict or None: The created time entry, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("time_entries").insert(entry_data).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None


def db_get_invoices():
    """Get all invoices from the database.

    Returns:
        list[dict]: Invoice records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("invoices").select("*").execute()
        return response.data or []
    except Exception:
        return []


def db_create_invoice(invoice_data):
    """Create a new invoice.

    Args:
        invoice_data: dict with invoice fields.

    Returns:
        dict or None: The created invoice, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("invoices").insert(invoice_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error creating invoice: {e}")
        return None


def db_update_invoice(invoice_id, data):
    """Update an existing invoice.

    Args:
        invoice_id: The UUID of the invoice.
        data: dict of fields to update.

    Returns:
        dict or None: The updated invoice, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("invoices").update(data).eq("id", invoice_id).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None


def db_create_project(project_data):
    """Create a new project record.

    Args:
        project_data: dict with project fields (name, client_name, project_type,
                      hourly_rate, estimated_hours, etc.)

    Returns:
        dict or None: The created project record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("projects").insert(project_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error creating project: {e}")
        return None


def db_update_project(project_id, project_data):
    """Update an existing project.

    Args:
        project_id: The UUID of the project.
        project_data: dict of fields to update.

    Returns:
        tuple: (success_bool, error_message_or_none)
    """
    db = get_db()
    if not db:
        return False, "No database connection"
    try:
        response = db.table("projects").update(project_data).eq("id", project_id).execute()
        # Success if no exception - Supabase may not return data on update
        return True, None
    except Exception as e:
        return False, str(e)


def db_delete_project(project_id):
    """Delete a project from the database.

    Args:
        project_id: The UUID of the project.

    Returns:
        bool: True if deleted successfully.
    """
    db = get_db()
    if not db:
        return False
    try:
        db.table("projects").delete().eq("id", project_id).execute()
        return True
    except Exception as e:
        print(f"[db_service] Error deleting project {project_id}: {e}")
        return False


def db_get_project(project_id):
    """Get a single project by ID.

    Args:
        project_id: The UUID of the project.

    Returns:
        dict or None: The project record, or None if not found.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("projects").select("*").eq("id", project_id).single().execute()
        return response.data
    except Exception as e:
        print(f"[db_service] Error getting project {project_id}: {e}")
        return None


def db_get_project_time_entries(project_id):
    """Get all time entries for a specific project.

    Args:
        project_id: The UUID of the project.

    Returns:
        list[dict]: Time entry records for the project.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("time_entries").select("*").eq(
            "project_id", project_id
        ).order("date", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"[db_service] Error getting time entries for project {project_id}: {e}")
        return []


def db_get_won_deals():
    """Get all deals with 'won' stage, available for linking to projects.

    Returns:
        list[dict]: List of won deal records with contact information.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("deals").select(
            "id, title, value, contact_id, contact_name, company_name, actual_close, contacts(id, first_name, last_name, company)"
        ).eq("stage", "won").order("actual_close", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting won deals: {e}")
        return []


def db_get_won_deals_by_contact(contact_id):
    """Get won deals for a specific contact/company.

    Args:
        contact_id: The UUID of the contact.

    Returns:
        list[dict]: List of won deals for this contact.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("deals").select(
            "id, title, value, contact_name, company_name, actual_close"
        ).eq("contact_id", contact_id).eq("stage", "won").order("actual_close", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting won deals for contact {contact_id}: {e}")
        return []


def db_check_deal_project_link(deal_id):
    """Check if a deal is already linked to a project.

    Args:
        deal_id: The UUID of the deal to check.

    Returns:
        dict or None: The linked project record if exists, None if available.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("projects").select(
            "id, name, status"
        ).eq("deal_id", deal_id).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error checking deal project link for {deal_id}: {e}")
        return None


def db_get_projects_by_contact(contact_id):
    """Get all projects for a specific contact/client.

    Args:
        contact_id: The UUID of the contact.

    Returns:
        list[dict]: List of projects for this contact with deal info.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("projects").select(
            "*, deals(id, title, value, stage)"
        ).eq("client_id", contact_id).order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting projects for contact {contact_id}: {e}")
        return []


def db_get_project_contacts(project_id):
    """Get all contacts associated with a project and their roles.

    Args:
        project_id: The UUID of the project.

    Returns:
        list[dict]: List of project contact records with contact info.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("project_contacts").select(
            "*, contacts(id, first_name, last_name, email, company)"
        ).eq("project_id", project_id).order("role").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting project contacts for {project_id}: {e}")
        return []


def db_add_project_contact(project_id, contact_id, role, is_primary=False, notes=None):
    """Add a contact to a project with a specific role.

    Args:
        project_id: The UUID of the project.
        contact_id: The UUID of the contact.
        role: The role string (e.g., 'Project Manager', 'Developer').
        is_primary: Whether this is the primary contact for this role.
        notes: Optional notes about the role.

    Returns:
        dict or None: The created project contact record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("project_contacts").insert({
            "project_id": project_id,
            "contact_id": contact_id,
            "role": role,
            "is_primary": is_primary,
            "notes": notes
        }).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error adding project contact: {e}")
        return None


def db_remove_project_contact(project_contact_id):
    """Remove a contact from a project.

    Args:
        project_contact_id: The UUID of the project contact record.

    Returns:
        bool: True if removed successfully.
    """
    db = get_db()
    if not db:
        return False
    try:
        db.table("project_contacts").delete().eq("id", project_contact_id).execute()
        return True
    except Exception as e:
        print(f"[db_service] Error removing project contact: {e}")
        return False


def db_get_project_files(project_id):
    """Get all files associated with a project.

    Args:
        project_id: The UUID of the project.

    Returns:
        list[dict]: List of project file records.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("project_files").select("*").eq(
            "project_id", project_id
        ).order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting project files for {project_id}: {e}")
        return []


def db_add_project_file(file_data):
    """Add a file record to a project.

    Args:
        file_data: dict with file fields (project_id, filename, storage_url, etc.)

    Returns:
        dict or None: The created file record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("project_files").insert(file_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error adding project file: {e}")
        return None


def db_delete_project_file(file_id):
    """Delete a project file record.

    Args:
        file_id: The UUID of the file record.

    Returns:
        bool: True if deleted successfully.
    """
    db = get_db()
    if not db:
        return False
    try:
        db.table("project_files").delete().eq("id", file_id).execute()
        return True
    except Exception as e:
        print(f"[db_service] Error deleting project file: {e}")
        return False


def db_update_project_hours(project_id, actual_hours):
    """Update the actual hours logged for a project.

    Args:
        project_id: The UUID of the project.
        actual_hours: The new actual hours value.

    Returns:
        bool: True if updated successfully.
    """
    db = get_db()
    if not db:
        return False
    try:
        response = db.table("projects").update({
            "actual_hours": actual_hours
        }).eq("id", project_id).execute()
        return bool(response.data)
    except Exception as e:
        print(f"[db_service] Error updating project hours: {e}")
        return False


def db_get_companies_with_won_deals():
    """Get all companies/contacts that have at least one won deal.

    Returns:
        list[dict]: List of contact records that have won deals.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("contacts").select(
            "id, first_name, last_name, company, email"
        ).in_(
            "id", 
            db.table("deals").select("contact_id").eq("stage", "won").execute().data
        ).order("company", desc=False).order("last_name", desc=False).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting companies with won deals: {e}")
        return []


# ============================================================
# 8. MARKETING / CAMPAIGNS
# ============================================================

def db_create_enrollment(enrollment_data):
    """Create a campaign enrollment record.

    Args:
        enrollment_data: dict with enrollment fields (contact_id, campaign_id, etc.)

    Returns:
        dict or None: The created enrollment record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("campaign_enrollments").insert(enrollment_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error creating enrollment: {e}")
        return None


# ============================================================
# 9. BUSINESS CARDS / STORAGE
# ============================================================

def upload_card_image_to_supabase(image_bytes, contact_id, file_ext="png", suffix=""):
    """Upload a business card image to Supabase Storage.

    Args:
        image_bytes: Raw image bytes to upload.
        contact_id: The UUID of the contact (used in filename).
        file_ext: File extension (default 'png').
        suffix: Optional suffix to differentiate front vs back ("" or "_back").

    Returns:
        str or None: The public URL of the uploaded image, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        import uuid as _uuid
        # Include suffix in filename to differentiate front vs back images
        filename = f"business-cards/{contact_id}{suffix}_{_uuid.uuid4().hex[:8]}.{file_ext}"

        response = db.storage.from_("card-images").upload(
            filename,
            image_bytes,
            {"content-type": f"image/{file_ext}", "upsert": "true"}
        )

        if response:
            public_url = db.storage.from_("card-images").get_public_url(filename)
            return public_url
        return None
    except Exception as e:
        print(f"[db_service] Error uploading card image: {e}")
        return None


def db_list_card_images(contact_id):
    """List business card images for a contact in Supabase Storage.

    Args:
        contact_id: The UUID of the contact.

    Returns:
        list[dict]: File metadata from storage, or empty list.
    """
    db = get_db()
    if not db:
        return []
    try:
        files_response = db.storage.from_("card-images").list("business-cards")
        return [f for f in files_response if f['name'].startswith(f"{contact_id}_")]
    except Exception:
        return []


def db_get_card_image_url(filename):
    """Get the public URL for a card image file.

    Args:
        filename: The filename within the business-cards folder.

    Returns:
        str or None: The public URL.
    """
    db = get_db()
    if not db:
        return None
    try:
        return db.storage.from_("card-images").get_public_url(f"business-cards/{filename}")
    except Exception:
        return None


# ============================================================
# 10. DASHBOARD
# ============================================================

def db_get_dashboard_stats():
    """Get dashboard statistics: contacts, deals, pipeline value, won this month.

    Returns:
        dict with keys: total_contacts, active_deals, pipeline_value, won_this_month.
    """
    db = get_db()
    default = {
        "total_contacts": 0,
        "active_deals": 0,
        "pipeline_value": 0,
        "won_this_month": 0
    }
    if not db:
        return default

    try:
        # Count non-archived contacts
        contacts_resp = db.table("contacts").select("id", count="exact").neq("archived", True).execute()
        total_contacts = contacts_resp.count if contacts_resp.count else 0

        # Get all deals for stage/value analysis
        deals_resp = db.table("deals").select("id, value, stage").execute()
        deals = deals_resp.data or []

        active_deals = [d for d in deals if d.get('stage') not in ['won', 'lost']]
        active_deal_count = len(active_deals)
        pipeline_value = sum(d.get('value', 0) or 0 for d in active_deals)

        won_deals = [d for d in deals if d.get('stage') == 'won']
        won_this_month = sum(d.get('value', 0) or 0 for d in won_deals)

        return {
            "total_contacts": total_contacts,
            "active_deals": active_deal_count,
            "pipeline_value": pipeline_value,
            "won_this_month": won_this_month
        }
    except Exception:
        return default


# ============================================================
# 11. SETTINGS / EXPORT
# ============================================================

def db_hash_password(raw_password):
    """Hash a password using SHA-256.

    Args:
        raw_password: Plain-text password string.

    Returns:
        str or None: Hex-encoded hash, or None if input is empty.
    """
    if not raw_password:
        return None
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def db_set_password_reset(code, expires_at):
    """Store password reset code and expiry in settings.

    Args:
        code: 6-digit reset code string.
        expires_at: datetime or ISO string for expiry time.

    Returns:
        bool: True if both settings were saved.
    """
    if not code or not expires_at:
        return False
    if isinstance(expires_at, datetime):
        expires_value = expires_at.isoformat()
    else:
        expires_value = str(expires_at)
    saved_code = db_set_setting("password_reset_code", code)
    saved_expires = db_set_setting("password_reset_expires", expires_value)
    return bool(saved_code and saved_expires)


def db_get_password_reset():
    """Get the current password reset code and expiry.

    Returns:
        dict: {"code": str|None, "expires_at": str|None}
    """
    return {
        "code": db_get_setting("password_reset_code"),
        "expires_at": db_get_setting("password_reset_expires"),
    }


def db_clear_password_reset():
    """Clear stored password reset code and expiry.

    Returns:
        bool: True if both settings were cleared.
    """
    cleared_code = db_set_setting("password_reset_code", None)
    cleared_expires = db_set_setting("password_reset_expires", None)
    return bool(cleared_code and cleared_expires)


def db_send_password_reset_email(to_email, reset_code, expires_minutes=15):
    """Send a password reset code email to the admin."""
    if not to_email or not reset_code:
        return {"success": False, "error": "Missing email or reset code"}

    subject = "MPT-CRM Password Reset Code"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; color: #1f2937;">
        <h2 style="margin: 0 0 12px;">Password Reset Request</h2>
        <p style="margin: 0 0 16px;">
            Use the code below to reset your MPT-CRM password. This code expires in {expires_minutes} minutes.
        </p>
        <div style="text-align: center; margin: 24px 0;">
            <div style="
                display: inline-block;
                padding: 16px 24px;
                font-size: 28px;
                letter-spacing: 6px;
                font-weight: 700;
                background: #f3f4f6;
                border-radius: 10px;
                color: #111827;">
                {reset_code}
            </div>
        </div>
        <p style="margin: 0;">
            If you did not request a password reset, you can ignore this email.
        </p>
    </div>
    """

    return send_email_via_sendgrid(
        to_email=to_email,
        to_name="Admin",
        subject=subject,
        html_body=html_body
    )


def db_get_setting(key):
    """Get a settings value by key.

    Args:
        key: Setting key string.

    Returns:
        str or None: The setting value, or None if missing/unavailable.
    """
    db = get_db()
    if not db or not key:
        return None
    try:
        response = db.table("settings").select("value").eq("key", key).limit(1).execute()
        if response.data:
            return response.data[0].get("value")
        return None
    except Exception as e:
        print(f"[db_service] Error getting setting {key}: {e}")
        return None


def db_set_setting(key, value):
    """Upsert a settings value by key.

    Args:
        key: Setting key string.
        value: Value to store (string or None).

    Returns:
        dict or None: Upserted setting record, or None on failure.
    """
    db = get_db()
    if not db or not key:
        return None
    try:
        payload = {
            "key": key,
            "value": value,
            "updated_at": datetime.now().isoformat(),
        }
        response = db.table("settings").upsert(payload, on_conflict="key").execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error setting {key}: {e}")
        return None


def db_export_all_tables():
    """Export all CRM data from all tables.

    Returns:
        dict: Table names as keys, list of records as values.
    """
    db = get_db()
    if not db:
        return {}

    export = {}
    tables = [
        "contacts", "deals", "projects", "tasks", "time_entries",
        "invoices", "email_templates", "email_campaigns", "email_sends",
        "activities"
    ]
    for table in tables:
        try:
            resp = db.table(table).select("*").execute()
            export[table] = resp.data if resp.data else []
        except Exception:
            export[table] = []
    return export


# ============================================================
# 12. SERVICE TICKETS
# ============================================================

def db_get_service_tickets(ticket_type=None):
    """Get service tickets, optionally filtered by type.

    Args:
        ticket_type: Optional. Filter by 'change_order', 'maintenance', or 'service'.

    Returns:
        list[dict]: Service ticket records.
    """
    db = get_db()
    if not db:
        return []
    try:
        query = db.table("service_tickets").select("*").order("created_at", desc=True)
        if ticket_type:
            query = query.eq("ticket_type", ticket_type)
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting service tickets: {e}")
        return []


def db_get_service_ticket(ticket_id):
    """Get a single service ticket by ID.

    Args:
        ticket_id: The UUID of the service ticket.

    Returns:
        dict or None: The service ticket record, or None if not found.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("service_tickets").select("*").eq("id", ticket_id).single().execute()
        return response.data
    except Exception as e:
        print(f"[db_service] Error getting service ticket {ticket_id}: {e}")
        return None


def db_create_service_ticket(ticket_data):
    """Create a new service ticket.

    Args:
        ticket_data: dict with ticket fields (title, ticket_type, project_id, etc.)

    Returns:
        dict or None: The created ticket record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        # Create the service ticket first
        response = db.table("service_tickets").insert(ticket_data).execute()
        created_ticket = response.data[0] if response.data else None
        
        if created_ticket:
            # Try to create Mission Control card
            try:
                from mission_control_service import create_mission_control_card
                
                # Determine ticket type for Mission Control
                ticket_type = created_ticket.get("ticket_type", "service")
                
                # Create Mission Control card
                mc_card_id = create_mission_control_card(created_ticket, ticket_type)
                
                # Update ticket with Mission Control card ID if successful
                if mc_card_id:
                    update_data = {"mission_control_card_id": mc_card_id}
                    db.table("service_tickets").update(update_data).eq("id", created_ticket["id"]).execute()
                    created_ticket["mission_control_card_id"] = mc_card_id
                    print(f"[db_service] Created Mission Control card {mc_card_id} for ticket {created_ticket['id']}")
                else:
                    print(f"[db_service] Failed to create Mission Control card for ticket {created_ticket['id']}")
                    
            except Exception as e:
                print(f"[db_service] Error creating Mission Control card: {e}")
                # Don't fail the ticket creation if MC integration fails
        
        return created_ticket
    except Exception as e:
        print(f"[db_service] Error creating service ticket: {e}")
        return None


def db_update_service_ticket(ticket_id, ticket_data):
    """Update an existing service ticket.

    Args:
        ticket_id: The UUID of the service ticket.
        ticket_data: dict of fields to update.

    Returns:
        dict or None: The updated ticket record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("service_tickets").update(ticket_data).eq("id", ticket_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error updating service ticket {ticket_id}: {e}")
        return None


# ============================================================
# 13. DRIP CAMPAIGN / SCHEDULER
# ============================================================

def db_get_active_enrollments():
    """Get all active campaign enrollments that may need emails sent.

    Returns:
        list[dict]: Active enrollment records with contact info joined.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("campaign_enrollments").select(
            "*, contacts(id, first_name, last_name, email, company, phone, type, email_status, source_detail)"
        ).eq("status", "active").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting active enrollments: {e}")
        return []


def db_get_enrollment(enrollment_id):
    """Get a single enrollment by ID.

    Args:
        enrollment_id: The UUID of the enrollment.

    Returns:
        dict or None: The enrollment record, or None if not found.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("campaign_enrollments").select(
            "*, contacts(id, first_name, last_name, email, company, phone, type, email_status, source_detail)"
        ).eq("id", enrollment_id).single().execute()
        return response.data
    except Exception as e:
        print(f"[db_service] Error getting enrollment {enrollment_id}: {e}")
        return None


def db_get_enrollments_for_contact(contact_id):
    """Get all enrollments for a specific contact.

    Args:
        contact_id: The UUID of the contact.

    Returns:
        list[dict]: Enrollment records for that contact.
    """
    db = get_db()
    if not db:
        return []
    try:
        response = db.table("campaign_enrollments").select("*").eq(
            "contact_id", contact_id
        ).order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"[db_service] Error getting enrollments for contact {contact_id}: {e}")
        return []


def db_update_enrollment(enrollment_id, data):
    """Update a campaign enrollment record.

    Args:
        enrollment_id: The UUID of the enrollment.
        data: dict of fields to update.

    Returns:
        dict or None: The updated enrollment, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("campaign_enrollments").update(data).eq(
            "id", enrollment_id
        ).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error updating enrollment {enrollment_id}: {e}")
        return None


def db_pause_enrollments_for_contact(contact_id, campaign_id=None):
    """Pause all active enrollments for a contact (or specific campaign).

    Used when switching campaigns due to contact type change.

    Args:
        contact_id: The UUID of the contact.
        campaign_id: Optional. Only pause enrollments for this campaign.

    Returns:
        int: Number of enrollments paused.
    """
    db = get_db()
    if not db:
        return 0
    try:
        query = db.table("campaign_enrollments").update({
            "status": "paused"
        }).eq("contact_id", contact_id).eq("status", "active")

        if campaign_id:
            query = query.eq("campaign_id", campaign_id)

        response = query.execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        print(f"[db_service] Error pausing enrollments for contact {contact_id}: {e}")
        return 0


def db_complete_enrollment(enrollment_id):
    """Mark an enrollment as completed.

    Args:
        enrollment_id: The UUID of the enrollment.

    Returns:
        dict or None: The updated enrollment, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("campaign_enrollments").update({
            "status": "completed"
        }).eq("id", enrollment_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error completing enrollment {enrollment_id}: {e}")
        return None


def db_record_email_send(contact_id, subject, sendgrid_message_id=None, enrollment_id=None):
    """Record an email send in the email_sends table.

    Args:
        contact_id: The UUID of the contact.
        subject: The email subject line.
        sendgrid_message_id: Optional SendGrid message ID for tracking.
        enrollment_id: Optional enrollment ID if from a drip campaign.

    Returns:
        dict or None: The created email_send record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        send_data = {
            "contact_id": contact_id,
            "subject": subject,
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
        }
        if sendgrid_message_id:
            send_data["sendgrid_message_id"] = sendgrid_message_id
        response = db.table("email_sends").insert(send_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error recording email send: {e}")
        return None


def send_email_via_sendgrid(to_email, to_name, subject, html_body, contact_id=None, enrollment_id=None):
    """Send an email via SendGrid and record it in email_sends.

    Returns {"success": True, "message_id": "..."} or {"success": False, "error": "..."}
    """
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, TrackingSettings, ClickTracking, OpenTracking
    except ImportError:
        return {"success": False, "error": "sendgrid package not installed"}

    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "patrick@metropointtechnology.com")
    from_name = os.getenv("SENDGRID_FROM_NAME", "Patrick Stabell")

    if not api_key:
        return {"success": False, "error": "SENDGRID_API_KEY not configured"}

    try:
        message = Mail(
            from_email=(from_email, from_name),
            to_emails=(to_email, to_name),
            subject=subject,
            html_content=html_body.replace("\n", "<br>")
        )

        tracking_settings = TrackingSettings()
        tracking_settings.click_tracking = ClickTracking(True, True)
        tracking_settings.open_tracking = OpenTracking(True)
        message.tracking_settings = tracking_settings

        sg = SendGridAPIClient(api_key)
        response = sg.send(message)

        if contact_id:
            db_record_email_send(
                contact_id=contact_id,
                subject=subject,
                sendgrid_message_id=response.headers.get("X-Message-Id", "")
            )

        return {
            "success": True,
            "message_id": response.headers.get("X-Message-Id", ""),
            "status_code": response.status_code
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def db_get_drip_campaign_template(campaign_id):
    """Get a drip campaign template by campaign_id.

    Args:
        campaign_id: The campaign identifier string (e.g. 'networking-drip-6week').

    Returns:
        dict or None: The campaign template record, or None if not found.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("drip_campaign_templates").select("*").eq(
            "campaign_id", campaign_id
        ).single().execute()
        return response.data
    except Exception as e:
        print(f"[db_service] Error getting drip campaign template {campaign_id}: {e}")
        return None


def _replace_merge_fields(template, contact, event_name=""):
    """Replace merge fields in a template string using contact data."""
    import re

    replacements = {
        "{{first_name}}": contact.get("first_name", ""),
        "{{last_name}}": contact.get("last_name", ""),
        "{{company}}": contact.get("company", ""),
        "{{company_name}}": contact.get("company", ""),
        "{{email}}": contact.get("email", ""),
        "{{phone}}": contact.get("phone", ""),
        "{{title}}": contact.get("title", ""),
        "{{event_name}}": event_name or contact.get("source_detail", ""),
        "{{your_name}}": os.getenv("SENDGRID_FROM_NAME", "Patrick Stabell"),
        "{{your_phone}}": os.getenv("SENDGRID_FROM_PHONE", "(239) 600-8159"),
        "{{your_email}}": os.getenv("SENDGRID_FROM_EMAIL", "patrick@metropointtechnology.com"),
        "{{your_website}}": os.getenv("SENDGRID_FROM_WEBSITE", "www.MetroPointTechnology.com"),
        "{{unsubscribe_link}}": "[Unsubscribe](mailto:patrick@metropointtechnology.com?subject=Unsubscribe)",
    }

    result = template or ""
    for field, value in replacements.items():
        result = result.replace(field, value or "")

    conditional_pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'

    def replace_conditional(match):
        field_name = match.group(1)
        content = match.group(2)
        value = replacements.get(f"{{{{{field_name}}}}}", "")
        return content if value else ""

    return re.sub(conditional_pattern, replace_conditional, result, flags=re.DOTALL)


def _build_step_schedule(email_sequence, start_date=None):
    """Build a step schedule from a campaign email sequence."""
    if start_date is None:
        start_date = datetime.now()
    schedule = []
    for idx, step in enumerate(email_sequence or []):
        day = step.get("day", 0)
        scheduled_date = start_date + timedelta(days=day)
        schedule.append({
            "step": idx,
            "day": day,
            "purpose": step.get("purpose", f"step_{idx}"),
            "scheduled_for": scheduled_date.isoformat(),
            "sent_at": None
        })
    return schedule


def _get_next_step_index(step_schedule, current_step, emails_sent):
    """Find the next unsent step index."""
    if step_schedule:
        for idx, step in enumerate(step_schedule):
            if not step.get("sent_at"):
                return idx
        return len(step_schedule)
    return max(current_step or 0, emails_sent or 0)


def _handle_campaign_switch(contact_id, old_type, new_type):
    """Complete existing enrollments and create a new one for the mapped campaign."""
    result = {"completed": 0, "enrolled": False, "message": ""}

    campaign_map = {
        "networking": "networking-drip-6week",
        "lead": "lead-drip",
        "prospect": "prospect-drip",
        "client": "client-drip",
    }

    new_campaign_id = campaign_map.get(new_type)
    if not new_campaign_id:
        result["message"] = f"No campaign mapped for type '{new_type}'."
        return result

    db = get_db()
    if not db:
        result["message"] = "Database not connected."
        return result

    try:
        active_resp = db.table("campaign_enrollments").select("*").eq(
            "contact_id", contact_id
        ).eq("status", "active").execute()
        active_enrollments = active_resp.data or []
    except Exception as e:
        result["message"] = f"Failed to fetch active enrollments: {e}"
        return result

    if any(e.get("campaign_id") == new_campaign_id for e in active_enrollments):
        result["message"] = "Already enrolled in mapped campaign."
        return result

    for enrollment in active_enrollments:
        updated = db_update_enrollment(enrollment["id"], {"status": "completed"})
        if updated:
            result["completed"] += 1

    template = db_get_drip_campaign_template(new_campaign_id)
    email_sequence = template.get("email_sequence") if template else None
    if isinstance(email_sequence, str):
        try:
            email_sequence = json.loads(email_sequence)
        except Exception:
            email_sequence = []

    if not email_sequence:
        result["message"] = f"Campaign template not found for '{new_campaign_id}'."
        return result

    schedule = _build_step_schedule(email_sequence)
    enrollment_data = {
        "contact_id": contact_id,
        "campaign_id": new_campaign_id,
        "campaign_name": template.get("name") if template else new_campaign_id,
        "status": "active",
        "current_step": 0,
        "total_steps": len(email_sequence),
        "step_schedule": json.dumps(schedule),
        "source": "auto_campaign_switch",
        "source_detail": f"Type changed from {old_type} to {new_type}",
        "emails_sent": 0,
        "next_email_scheduled": schedule[0]["scheduled_for"] if schedule else None
    }

    enrollment = db_create_enrollment(enrollment_data)
    if enrollment:
        result["enrolled"] = True
        result["message"] = f"Switched campaign to '{new_campaign_id}'."
        db_log_activity(
            "campaign_switched",
            f"Contact type changed from '{old_type}' to '{new_type}', enrolled in {new_campaign_id}.",
            contact_id
        )
    else:
        result["message"] = f"Failed to enroll in '{new_campaign_id}'."

    return result


def db_process_due_campaign_enrollments():
    """Send due drip emails based on next_email_scheduled."""
    db = get_db()
    if not db:
        return 0

    now = datetime.now()
    try:
        response = db.table("campaign_enrollments").select(
            "*, contacts(id, first_name, last_name, email, company, phone, type, email_status, source_detail)"
        ).eq("status", "active").lte("next_email_scheduled", now.isoformat()).execute()
        enrollments = response.data or []
    except Exception as e:
        print(f"[db_service] Error fetching due enrollments: {e}")
        return 0

    sent_count = 0

    for enrollment in enrollments:
        try:
            contact = enrollment.get("contacts") or {}
            email_addr = contact.get("email", "")
            email_status = contact.get("email_status", "active")
            if not email_addr or email_status in ("unsubscribed", "bounced"):
                continue

            campaign_id = enrollment.get("campaign_id", "")
            template = db_get_drip_campaign_template(campaign_id)
            email_sequence = template.get("email_sequence") if template else None
            if isinstance(email_sequence, str):
                try:
                    email_sequence = json.loads(email_sequence)
                except Exception:
                    email_sequence = []

            if not email_sequence:
                print(f"[db_service] Missing campaign template for {campaign_id}")
                continue

            step_schedule = enrollment.get("step_schedule") or []
            if isinstance(step_schedule, str):
                try:
                    step_schedule = json.loads(step_schedule)
                except Exception:
                    step_schedule = []

            if not step_schedule:
                enrolled_at = enrollment.get("enrolled_at")
                start_date = None
                if enrolled_at:
                    try:
                        start_date = datetime.fromisoformat(str(enrolled_at).replace("Z", "+00:00"))
                        if start_date.tzinfo:
                            start_date = start_date.replace(tzinfo=None)
                    except Exception:
                        start_date = None
                step_schedule = _build_step_schedule(email_sequence, start_date=start_date)

            next_step_idx = _get_next_step_index(
                step_schedule,
                enrollment.get("current_step"),
                enrollment.get("emails_sent")
            )

            if next_step_idx >= len(email_sequence):
                db_update_enrollment(enrollment["id"], {
                    "status": "completed",
                    "next_email_scheduled": None,
                    "step_schedule": json.dumps(step_schedule)
                })
                db_log_activity(
                    "campaign_completed",
                    f"Completed drip campaign: {enrollment.get('campaign_name', campaign_id)}",
                    contact.get("id")
                )
                continue

            email_template = email_sequence[next_step_idx]
            event_name = enrollment.get("source_detail", "")
            subject = _replace_merge_fields(email_template.get("subject", ""), contact, event_name)
            body = _replace_merge_fields(email_template.get("body", ""), contact, event_name)
            to_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()

            result = send_email_via_sendgrid(
                to_email=email_addr,
                to_name=to_name,
                subject=subject,
                html_body=body,
                contact_id=contact.get("id"),
                enrollment_id=enrollment.get("id")
            )

            if result.get("success"):
                sent_count += 1
                sent_at = datetime.now().isoformat()
                if next_step_idx < len(step_schedule):
                    step_schedule[next_step_idx]["sent_at"] = sent_at

                next_scheduled = None
                for step in step_schedule:
                    if not step.get("sent_at"):
                        next_scheduled = step.get("scheduled_for")
                        break

                update_data = {
                    "current_step": next_step_idx + 1,
                    "emails_sent": (enrollment.get("emails_sent") or 0) + 1,
                    "last_email_sent_at": sent_at,
                    "next_email_scheduled": next_scheduled,
                    "step_schedule": json.dumps(step_schedule)
                }
                if not next_scheduled:
                    update_data["status"] = "completed"

                db_update_enrollment(enrollment["id"], update_data)
                db_log_activity(
                    "email_sent",
                    f"Drip email step {next_step_idx + 1}: {subject}",
                    contact.get("id")
                )
            else:
                print(f"[db_service] Send failed for {email_addr}: {result.get('error')}")
        except Exception as e:
            print(f"[db_service] Error processing enrollment {enrollment.get('id')}: {e}")
            continue

    return sent_count


def db_update_contact_and_switch_campaign(contact_id, new_type, old_type=None):
    """Update a contact's type and handle campaign switching.

    When a contact's type changes (e.g., networking -> lead -> prospect -> client),
    complete current campaign enrollments and enroll in the appropriate new campaign.

    Campaign mapping:
        networking -> networking-drip-6week
        lead       -> lead-drip
        prospect   -> prospect-drip
        client     -> client-drip

    Args:
        contact_id: The UUID of the contact.
        new_type: The new contact type string.
        old_type: The previous contact type (if known).

    Returns:
        dict: {"success": bool, "message": str, "completed": int, "enrolled": bool}
    """
    result = {"success": False, "message": "", "completed": 0, "enrolled": False}

    if old_type is None:
        existing = db_get_contact(contact_id)
        old_type = existing.get("type") if existing else None

    updated = db_update_contact(contact_id, {"type": new_type}, skip_campaign_switch=True)
    if not updated:
        result["message"] = "Failed to update contact type"
        return result

    result["success"] = True

    if old_type and old_type != new_type:
        switch_result = _handle_campaign_switch(contact_id, old_type, new_type)
        result["completed"] = switch_result.get("completed", 0)
        result["enrolled"] = switch_result.get("enrolled", False)
        result["message"] = switch_result.get("message", "")
    else:
        result["message"] = f"Contact type set to '{new_type}'."

    return result

# ============================================
# COMPANY DATABASE FUNCTIONS
# ============================================

def db_get_companies():
    """Get all companies from database"""
    try:
        db = get_db()
        if db is None:
            return []
        result = db.table('companies').select('*').order('name').execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting companies: {e}")
        return []


def db_get_company(company_id):
    """Get a single company by ID"""
    try:
        db = get_db()
        if db is None:
            return None
        result = db.table('companies').select('*').eq('id', company_id).single().execute()
        return result.data
    except Exception as e:
        print(f"Error getting company: {e}")
        return None


def db_create_company(company_data):
    """Create a new company"""
    try:
        db = get_db()
        if db is None:
            return None
        result = db.table('companies').insert(company_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error creating company: {e}")
        return None


def db_update_company(company_id, company_data):
    """Update a company"""
    try:
        db = get_db()
        if db is None:
            return False
        db.table('companies').update(company_data).eq('id', company_id).execute()
        return True
    except Exception as e:
        print(f"Error updating company: {e}")
        return False


def db_delete_company(company_id):
    """Delete a company"""
    try:
        db = get_db()
        if db is None:
            return False
        db.table('companies').delete().eq('id', company_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting company: {e}")
        return False


def db_get_company_contacts(company_id):
    """Get all contacts for a company"""
    try:
        db = get_db()
        if db is None:
            return []
        result = db.table('contacts').select('*').eq('company_id', company_id).order('last_name').execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting company contacts: {e}")
        return []


# ============================================
# PROJECT STATUS MANAGEMENT FUNCTIONS
# ============================================

def db_change_project_status(project_id, new_status, reason, changed_by="Metro Bot"):
    """Change a project's status with reason tracking and history logging.
    
    Args:
        project_id: The UUID of the project
        new_status: New status value ('on-hold', 'voided', 'active', etc.)
        reason: Reason for the status change (required for on-hold/voided)
        changed_by: Who initiated the change
    
    Returns:
        tuple: (success_bool, error_message_or_none)
    """
    db = get_db()
    if not db:
        return False, "No database connection"
    
    # Validate required reason for certain status changes
    if new_status in ('on-hold', 'voided') and not reason:
        return False, "Reason is required for on-hold and voided status"
    
    try:
        # Get current project data
        current = db.table("projects").select("*").eq("id", project_id).single().execute()
        if not current.data:
            return False, "Project not found"
        
        old_status = current.data.get('status')
        
        # Update project with new status and metadata
        update_data = {
            "status": new_status,
            "status_reason": reason,
            "status_changed_by": changed_by,
            "status_changed_at": datetime.now().isoformat()
        }
        
        # Set actual_end_date if completing or voiding
        if new_status in ('completed', 'voided'):
            update_data["actual_end_date"] = datetime.now().date().isoformat()
        
        response = db.table("projects").update(update_data).eq("id", project_id).execute()
        
        # Log to project history (if table exists, otherwise skip gracefully)
        try:
            db.table("project_history").insert({
                "project_id": project_id,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
                "changed_by": changed_by
            }).execute()
        except Exception:
            # Project history table might not exist yet, that's ok
            pass
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def db_get_project_history(project_id):
    """Get status change history for a project.
    
    Args:
        project_id: The UUID of the project
        
    Returns:
        list[dict]: List of history records, newest first
    """
    db = get_db()
    if not db:
        return []
    
    try:
        response = db.table("project_history").select("*").eq(
            "project_id", project_id
        ).order("changed_at", desc=True).execute()
        return response.data or []
    except Exception:
        # Table might not exist yet
        return []


def db_can_log_time_to_project(project_id):
    """Check if time entries can be logged to this project.
    
    Stopped (on-hold) and voided projects should not accept new time entries.
    
    Args:
        project_id: The UUID of the project
        
    Returns:
        bool: True if time can be logged, False otherwise
    """
    db = get_db()
    if not db:
        return False
    
    try:
        response = db.table("projects").select("status").eq("id", project_id).single().execute()
        if not response.data:
            return False
        
        status = response.data.get('status')
        # Allow time logging for active, planning, completed, and maintenance projects
        # Disallow for on-hold and voided
        return status not in ('on-hold', 'voided')
        
    except Exception:
        return False


def db_notify_mission_control_project_status(project_id, project_name, new_status, reason):
    """Notify Mission Control about project status change for related cards.
    
    This function integrates with the Mission Control API to move related cards
    to backlog or archive when projects are stopped/voided.
    
    Args:
        project_id: The UUID of the project
        project_name: Name of the project
        new_status: The new status ('on-hold', 'voided', etc.)
        reason: Reason for the change
        
    Returns:
        bool: True if notification was successful, False otherwise
    """
    try:
        import requests
        
        # Mission Control API endpoint
        mc_api_url = "https://mpt-mission-control.vercel.app/api"
        
        # Search for cards related to this project
        search_response = requests.get(
            f"{mc_api_url}/tasks",
            params={"search": project_name},
            timeout=10
        )
        
        if search_response.status_code != 200:
            print(f"[db_service] Mission Control API not available: {search_response.status_code}")
            return False
        
        related_cards = search_response.json()
        
        # Determine target status based on project status
        if new_status == 'on-hold':
            target_card_status = 'backlog'
            action_msg = 'moved to backlog'
        elif new_status == 'voided':
            target_card_status = 'archive'
            action_msg = 'archived'
        else:
            # No action needed for other status changes
            return True
        
        # Update related cards
        updated_count = 0
        for card in related_cards:
            if card.get('status') in ('in-progress', 'queue'):
                try:
                    update_response = requests.put(
                        f"{mc_api_url}/tasks/{card['id']}",
                        json={
                            "status": target_card_status,
                            "notes": f"Auto-{action_msg}: Project {project_name} {new_status} - {reason}"
                        },
                        timeout=10
                    )
                    if update_response.status_code == 200:
                        updated_count += 1
                except Exception as e:
                    print(f"[db_service] Failed to update card {card.get('id')}: {e}")
        
        print(f"[db_service] Mission Control: {updated_count} cards {action_msg} for project {project_name}")
        return True
        
    except Exception as e:
        print(f"[db_service] Mission Control notification failed: {e}")
        return False


# ============================================================
# 15. CHANGE ORDERS
# ============================================================

def db_get_change_orders(project_id=None, status=None):
    """Get change orders with optional filtering"""
    try:
        db = get_db()
        if not db:
            return []
        
        query = db.table('change_orders').select("""
            id, project_id, title, description, status,
            requested_by, approved_by, requested_at, approved_at,
            estimated_hours, actual_hours, hourly_rate, total_amount,
            impact_description, requires_client_approval, client_signature,
            created_at, updated_at,
            projects(name, client_id, contacts(first_name, last_name, company))
        """).order('created_at', desc=True)
        
        if project_id:
            query = query.eq('project_id', project_id)
        if status:
            query = query.eq('status', status)
            
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error fetching change orders: {e}")
        return []


def db_create_change_order(data):
    """Create a new change order"""
    try:
        db = get_db()
        if not db:
            return None
        
        # Calculate total_amount if hourly_rate and estimated_hours are provided
        if data.get('estimated_hours') and data.get('hourly_rate'):
            data['total_amount'] = float(data['estimated_hours']) * float(data['hourly_rate'])
        
        result = db.table('change_orders').insert(data).execute()
        created_change_order = result.data[0] if result.data else None
        
        if created_change_order:
            # Try to create Mission Control card
            try:
                from mission_control_service import create_mission_control_card
                
                # Create Mission Control card for change order
                mc_card_id = create_mission_control_card(created_change_order, "change_order")
                
                # Update change order with Mission Control card ID if successful
                if mc_card_id:
                    update_data = {"mission_control_card_id": mc_card_id}
                    db.table("change_orders").update(update_data).eq("id", created_change_order["id"]).execute()
                    created_change_order["mission_control_card_id"] = mc_card_id
                    print(f"[db_service] Created Mission Control card {mc_card_id} for change order {created_change_order['id']}")
                else:
                    print(f"[db_service] Failed to create Mission Control card for change order {created_change_order['id']}")
                    
            except Exception as e:
                print(f"[db_service] Error creating Mission Control card for change order: {e}")
                # Don't fail the change order creation if MC integration fails
        
        return created_change_order
        
    except Exception as e:
        print(f"Error creating change order: {e}")
        return None


def db_update_change_order(change_order_id, data):
    """Update a change order"""
    try:
        db = get_db()
        if not db:
            return None
        
        data['updated_at'] = datetime.now().isoformat()
        
        # Recalculate total_amount if hourly_rate and estimated_hours are provided
        if data.get('estimated_hours') and data.get('hourly_rate'):
            data['total_amount'] = float(data['estimated_hours']) * float(data['hourly_rate'])
        
        result = db.table('change_orders').update(data).eq('id', change_order_id).execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"Error updating change order: {e}")
        return None


def db_get_change_order(change_order_id):
    """Get a single change order by ID"""
    try:
        db = get_db()
        if not db:
            return None
        
        result = db.table('change_orders').select("""
            id, project_id, title, description, status,
            requested_by, approved_by, requested_at, approved_at,
            estimated_hours, actual_hours, hourly_rate, total_amount,
            impact_description, requires_client_approval, client_signature,
            created_at, updated_at,
            projects(name, client_id, contacts(first_name, last_name, company))
        """).eq('id', change_order_id).execute()
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"Error fetching change order: {e}")
        return None


def db_delete_change_order(change_order_id):
    """Delete a change order"""
    try:
        db = get_db()
        if not db:
            return False
        
        db.table('change_orders').delete().eq('id', change_order_id).execute()
        return True
        
    except Exception as e:
        print(f"Error deleting change order: {e}")
        return False


def db_get_project_change_orders(project_id):
    """Get all change orders for a specific project"""
    return db_get_change_orders(project_id=project_id)
