# -*- coding: utf-8 -*-
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
"""

import os
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
    """Create a new contact record.

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
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"[db_service] Error creating contact: {e}")
        return None


def db_update_contact(contact_id, contact_data):
    """Update an existing contact.

    Args:
        contact_id: The UUID of the contact.
        contact_data: dict of fields to update.

    Returns:
        dict or None: The updated contact record, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        response = db.table("contacts").update(contact_data).eq("id", contact_id).execute()
        return response.data[0] if response.data else None
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

def upload_card_image_to_supabase(image_bytes, contact_id, file_ext="png"):
    """Upload a business card image to Supabase Storage.

    Args:
        image_bytes: Raw image bytes to upload.
        contact_id: The UUID of the contact (used in filename).
        file_ext: File extension (default 'png').

    Returns:
        str or None: The public URL of the uploaded image, or None on failure.
    """
    db = get_db()
    if not db:
        return None
    try:
        import uuid as _uuid
        filename = f"business-cards/{contact_id}_{_uuid.uuid4().hex[:8]}.{file_ext}"

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
