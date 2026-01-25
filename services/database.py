"""
Supabase Database Service for MPT-CRM
Handles all database operations with Supabase
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import supabase, handle if not installed
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

class Database:
    """Supabase database wrapper for MPT-CRM"""

    def __init__(self):
        self.client: Optional[Client] = None
        self._connected = False

        if SUPABASE_AVAILABLE:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")

            if url and key:
                try:
                    self.client = create_client(url, key)
                    self._connected = True
                except Exception as e:
                    print(f"Failed to connect to Supabase: {e}")

    @property
    def is_connected(self) -> bool:
        return self._connected and self.client is not None

    # ============================================
    # CONTACTS
    # ============================================

    def get_contacts(self, type_filter: Optional[str] = None, tag_filter: Optional[str] = None) -> List[Dict]:
        """Get all contacts with optional filters"""
        if not self.is_connected:
            return []

        query = self.client.table("contacts").select("*").order("created_at", desc=True)

        if type_filter:
            query = query.eq("type", type_filter)

        if tag_filter:
            query = query.contains("tags", [tag_filter])

        response = query.execute()
        return response.data if response.data else []

    def get_contact(self, contact_id: str) -> Optional[Dict]:
        """Get a single contact by ID"""
        if not self.is_connected:
            return None

        response = self.client.table("contacts").select("*").eq("id", contact_id).single().execute()
        return response.data

    def create_contact(self, contact_data: Dict) -> Optional[Dict]:
        """Create a new contact"""
        if not self.is_connected:
            return None

        response = self.client.table("contacts").insert(contact_data).execute()
        return response.data[0] if response.data else None

    def update_contact(self, contact_id: str, contact_data: Dict) -> Optional[Dict]:
        """Update an existing contact"""
        if not self.is_connected:
            return None

        response = self.client.table("contacts").update(contact_data).eq("id", contact_id).execute()
        return response.data[0] if response.data else None

    def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact"""
        if not self.is_connected:
            return False

        self.client.table("contacts").delete().eq("id", contact_id).execute()
        return True

    # ============================================
    # DEALS
    # ============================================

    def get_deals(self, stage_filter: Optional[str] = None) -> List[Dict]:
        """Get all deals with optional stage filter"""
        if not self.is_connected:
            return []

        query = self.client.table("deals").select("*, contacts(first_name, last_name, company)").order("created_at", desc=True)

        if stage_filter:
            query = query.eq("stage", stage_filter)

        response = query.execute()
        return response.data if response.data else []

    def get_deal(self, deal_id: str) -> Optional[Dict]:
        """Get a single deal with related data"""
        if not self.is_connected:
            return None

        response = self.client.table("deals").select(
            "*, contacts(first_name, last_name, company, email), deal_tasks(*), deal_comments(*)"
        ).eq("id", deal_id).single().execute()
        return response.data

    def create_deal(self, deal_data: Dict) -> Optional[Dict]:
        """Create a new deal"""
        if not self.is_connected:
            return None

        response = self.client.table("deals").insert(deal_data).execute()
        return response.data[0] if response.data else None

    def update_deal(self, deal_id: str, deal_data: Dict) -> Optional[Dict]:
        """Update an existing deal"""
        if not self.is_connected:
            return None

        response = self.client.table("deals").update(deal_data).eq("id", deal_id).execute()
        return response.data[0] if response.data else None

    def update_deal_stage(self, deal_id: str, new_stage: str) -> Optional[Dict]:
        """Update deal stage (for drag-and-drop)"""
        update_data = {"stage": new_stage}
        if new_stage == "won":
            update_data["actual_close"] = datetime.now().isoformat()
        return self.update_deal(deal_id, update_data)

    # ============================================
    # DEAL TASKS
    # ============================================

    def add_deal_task(self, deal_id: str, title: str) -> Optional[Dict]:
        """Add a task to a deal"""
        if not self.is_connected:
            return None

        response = self.client.table("deal_tasks").insert({
            "deal_id": deal_id,
            "title": title
        }).execute()
        return response.data[0] if response.data else None

    def toggle_deal_task(self, task_id: str, is_complete: bool) -> Optional[Dict]:
        """Toggle deal task completion"""
        if not self.is_connected:
            return None

        response = self.client.table("deal_tasks").update({
            "is_complete": is_complete
        }).eq("id", task_id).execute()
        return response.data[0] if response.data else None

    # ============================================
    # DEAL COMMENTS
    # ============================================

    def add_deal_comment(self, deal_id: str, content: str, author: str = "Patrick") -> Optional[Dict]:
        """Add a comment to a deal"""
        if not self.is_connected:
            return None

        response = self.client.table("deal_comments").insert({
            "deal_id": deal_id,
            "content": content,
            "author": author
        }).execute()
        return response.data[0] if response.data else None

    # ============================================
    # PROJECTS
    # ============================================

    def get_projects(self, status_filter: Optional[str] = None) -> List[Dict]:
        """Get all projects"""
        if not self.is_connected:
            return []

        query = self.client.table("projects").select(
            "*, contacts(first_name, last_name, company)"
        ).order("created_at", desc=True)

        if status_filter:
            query = query.eq("status", status_filter)

        response = query.execute()
        return response.data if response.data else []

    def create_project(self, project_data: Dict) -> Optional[Dict]:
        """Create a new project"""
        if not self.is_connected:
            return None

        response = self.client.table("projects").insert(project_data).execute()
        return response.data[0] if response.data else None

    def update_project(self, project_id: str, project_data: Dict) -> Optional[Dict]:
        """Update a project"""
        if not self.is_connected:
            return None

        response = self.client.table("projects").update(project_data).eq("id", project_id).execute()
        return response.data[0] if response.data else None

    # ============================================
    # TASKS
    # ============================================

    def get_tasks(self, status_filter: Optional[str] = None, due_date: Optional[str] = None) -> List[Dict]:
        """Get all tasks"""
        if not self.is_connected:
            return []

        query = self.client.table("tasks").select(
            "*, contacts(first_name, last_name), deals(title), projects(name)"
        ).order("due_date", desc=False)

        if status_filter:
            query = query.eq("status", status_filter)

        if due_date:
            query = query.lte("due_date", due_date)

        response = query.execute()
        return response.data if response.data else []

    def create_task(self, task_data: Dict) -> Optional[Dict]:
        """Create a new task"""
        if not self.is_connected:
            return None

        response = self.client.table("tasks").insert(task_data).execute()
        return response.data[0] if response.data else None

    def update_task(self, task_id: str, task_data: Dict) -> Optional[Dict]:
        """Update a task"""
        if not self.is_connected:
            return None

        if task_data.get("status") == "completed":
            task_data["completed_at"] = datetime.now().isoformat()

        response = self.client.table("tasks").update(task_data).eq("id", task_id).execute()
        return response.data[0] if response.data else None

    # ============================================
    # TIME ENTRIES
    # ============================================

    def get_time_entries(self, project_id: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Get time entries with optional filters"""
        if not self.is_connected:
            return []

        query = self.client.table("time_entries").select(
            "*, projects(name, contacts(company))"
        ).order("date", desc=True)

        if project_id:
            query = query.eq("project_id", project_id)
        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)

        response = query.execute()
        return response.data if response.data else []

    def create_time_entry(self, entry_data: Dict) -> Optional[Dict]:
        """Create a time entry"""
        if not self.is_connected:
            return None

        response = self.client.table("time_entries").insert(entry_data).execute()
        return response.data[0] if response.data else None

    # ============================================
    # EMAIL TEMPLATES
    # ============================================

    def get_email_templates(self, category: Optional[str] = None) -> List[Dict]:
        """Get email templates"""
        if not self.is_connected:
            return []

        query = self.client.table("email_templates").select("*").order("name")

        if category:
            query = query.eq("category", category)

        response = query.execute()
        return response.data if response.data else []

    def save_email_template(self, template_data: Dict) -> Optional[Dict]:
        """Create or update email template"""
        if not self.is_connected:
            return None

        if template_data.get("id"):
            response = self.client.table("email_templates").update(template_data).eq("id", template_data["id"]).execute()
        else:
            response = self.client.table("email_templates").insert(template_data).execute()

        return response.data[0] if response.data else None

    # ============================================
    # ACTIVITIES
    # ============================================

    def log_activity(self, activity_type: str, description: str, contact_id: Optional[str] = None,
                     deal_id: Optional[str] = None, project_id: Optional[str] = None) -> Optional[Dict]:
        """Log an activity"""
        if not self.is_connected:
            return None

        response = self.client.table("activities").insert({
            "type": activity_type,
            "description": description,
            "contact_id": contact_id,
            "deal_id": deal_id,
            "project_id": project_id
        }).execute()
        return response.data[0] if response.data else None

    def get_activities(self, contact_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get recent activities"""
        if not self.is_connected:
            return []

        query = self.client.table("activities").select("*").order("created_at", desc=True).limit(limit)

        if contact_id:
            query = query.eq("contact_id", contact_id)

        response = query.execute()
        return response.data if response.data else []

    # ============================================
    # DASHBOARD STATS
    # ============================================

    def get_dashboard_stats(self) -> Dict:
        """Get aggregated stats for dashboard"""
        if not self.is_connected:
            return {
                "total_contacts": 0,
                "active_deals": 0,
                "pipeline_value": 0,
                "won_this_month": 0
            }

        # Get contact count
        contacts = self.client.table("contacts").select("id", count="exact").execute()

        # Get active deals
        active_deals = self.client.table("deals").select("id, value").not_.in_("stage", ["won", "lost"]).execute()

        # Get won deals this month
        from datetime import datetime
        first_of_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        won_deals = self.client.table("deals").select("value").eq("stage", "won").gte("actual_close", first_of_month).execute()

        pipeline_value = sum(d.get("value", 0) or 0 for d in (active_deals.data or []))
        won_value = sum(d.get("value", 0) or 0 for d in (won_deals.data or []))

        return {
            "total_contacts": contacts.count or 0,
            "active_deals": len(active_deals.data or []),
            "pipeline_value": pipeline_value,
            "won_this_month": won_value
        }


# Singleton instance
db = Database()
