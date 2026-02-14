"""
Mission Control API Service for CRM
====================================

Integrates CRM with Mission Control for time tracking and task management.

Architecture Rules:
- Time tracking data comes from Mission Control (source of truth)  
- CRM queries MC for live time data
- Financial data (invoiced amounts) comes from Accounting (source of truth)
- CRM shows both raw time from MC and invoiced time from Accounting

API Endpoints:
- GET /api/tasks - List all tasks
- GET /api/tasks/{task_id} - Get specific task
- GET /api/tasks/{task_id}/time - Get time entries for task
- POST /api/tasks/{task_id}/time/manual - Log manual time entry
"""

import requests
import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os


class MissionControlService:
    """Service for querying Mission Control API"""
    
    def __init__(self):
        # Mission Control API base URL
        self.base_url = os.environ.get(
            "MISSION_CONTROL_API_URL",
            "https://mpt-mission-control.vercel.app/api"
        )
        self.timeout = 10
    
    def _make_request(self, endpoint: str, method: str = "GET", data: dict = None) -> Optional[dict]:
        """Make HTTP request to Mission Control API with error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=self.timeout)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            st.warning("Mission Control API timeout")
            return None
        except requests.exceptions.ConnectionError:
            st.warning("Cannot connect to Mission Control")
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None  # Not found is OK
            st.error(f"Mission Control API error: {e}")
            return None
        except Exception as e:
            st.error(f"Unexpected error calling Mission Control: {e}")
            return None
    
    def get_project_tasks(self, project_id: str = None, mc_task_id: str = None) -> List[Dict[str, Any]]:
        """
        Get tasks from Mission Control for a CRM project.
        
        Args:
            project_id: CRM project ID to filter by (if tasks have crm_project_id field)
            mc_task_id: Specific Mission Control task ID to get
            
        Returns:
            List of task records with time tracking data
        """
        if mc_task_id:
            # Get specific task
            task = self._make_request(f"tasks/{mc_task_id}")
            return [task] if task else []
        
        # Get all tasks, filter client-side if needed
        tasks = self._make_request("tasks") or []
        
        if project_id:
            # Filter tasks that belong to this CRM project
            # Assumes tasks have a crm_project_id or tags field we can match
            filtered_tasks = []
            for task in tasks:
                if (task.get("crm_project_id") == project_id or
                    project_id in task.get("tags", []) or
                    project_id in task.get("title", "").lower()):
                    filtered_tasks.append(task)
            return filtered_tasks
        
        return tasks
    
    def get_time_entries(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get time entries for a specific Mission Control task.
        
        Args:
            task_id: Mission Control task ID
            
        Returns:
            List of time entry records
        """
        return self._make_request(f"tasks/{task_id}/time") or []
    
    def log_manual_time(self, task_id: str, duration_minutes: int, agent_name: str = "Metro Bot", note: str = "") -> Optional[dict]:
        """
        Log manual time entry to Mission Control.
        
        Args:
            task_id: Mission Control task ID
            duration_minutes: Duration in minutes (e.g., 1800000 = 30 min)
            agent_name: Name of agent who did the work
            note: Description of work done
            
        Returns:
            Time entry record if successful, None otherwise
        """
        data = {
            "durationMs": duration_minutes * 60 * 1000,  # Convert to milliseconds
            "agentName": agent_name,
            "note": note or f"Manual time entry from CRM"
        }
        
        return self._make_request(f"tasks/{task_id}/time/manual", "POST", data)
    
    def get_project_time_summary(self, project_id: str = None, mc_task_id: str = None) -> Dict[str, Any]:
        """
        Get time tracking summary for a project.
        
        Returns:
            Dictionary with time summary data:
            - total_hours: Total hours across all tasks
            - tasks_count: Number of tasks with time
            - recent_entries: Recent time entries
            - by_agent: Hours breakdown by agent
        """
        tasks = self.get_project_tasks(project_id, mc_task_id)
        
        total_hours = 0
        tasks_with_time = 0
        recent_entries = []
        by_agent = {}
        
        for task in tasks:
            time_entries = self.get_time_entries(task.get("id", ""))
            if time_entries:
                tasks_with_time += 1
                
                for entry in time_entries:
                    duration_ms = entry.get("duration", 0)
                    hours = duration_ms / (1000 * 60 * 60)  # Convert from milliseconds
                    total_hours += hours
                    
                    agent = entry.get("agentName", "Unknown")
                    by_agent[agent] = by_agent.get(agent, 0) + hours
                    
                    # Add to recent entries (with task context)
                    entry_with_task = entry.copy()
                    entry_with_task["task_title"] = task.get("title", "Unknown Task")
                    entry_with_task["task_id"] = task.get("id")
                    entry_with_task["hours"] = hours
                    recent_entries.append(entry_with_task)
        
        # Sort recent entries by timestamp, most recent first
        recent_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "total_hours": total_hours,
            "tasks_count": tasks_with_time,
            "recent_entries": recent_entries[:10],  # Last 10 entries
            "by_agent": by_agent,
            "connected": True
        }
    
    def link_project_to_task(self, task_id: str, crm_project_id: str) -> bool:
        """
        Link a CRM project to a Mission Control task by updating task tags.
        
        Args:
            task_id: Mission Control task ID
            crm_project_id: CRM project ID to link
            
        Returns:
            True if linked successfully
        """
        # Update task to include CRM project ID in tags or custom field
        data = {
            "crm_project_id": crm_project_id,
            "tags": [f"crm:{crm_project_id}"]
        }
        
        result = self._make_request(f"tasks/{task_id}", "PUT", data)
        return result is not None
    
    def create_task_from_project(self, project_data: Dict[str, Any]) -> Optional[dict]:
        """
        Create a new Mission Control task from a CRM project.
        
        Args:
            project_data: Dictionary with project info (name, description, etc.)
            
        Returns:
            Created task record if successful
        """
        task_data = {
            "title": f"CRM Project: {project_data.get('name', 'Unnamed Project')}",
            "description": project_data.get('description', ''),
            "priority": "medium",
            "status": "backlog",
            "crm_project_id": project_data.get('id'),
            "tags": [f"crm:{project_data.get('id')}", "project"],
            "checklist": [
                {"text": "Project setup and planning", "done": False},
                {"text": "Development/implementation", "done": False},
                {"text": "Testing and QA", "done": False},
                {"text": "Deployment and delivery", "done": False},
                {"text": "Client approval and sign-off", "done": False}
            ]
        }
        
        return self._make_request("tasks", "POST", task_data)

    def create_task_from_crm_item(self, item_data: Dict[str, Any], item_type: str) -> Optional[dict]:
        """
        Create a new Mission Control task from a CRM billable item (change order or service ticket).
        
        Args:
            item_data: Dictionary with item info (title, description, project_id, etc.)
            item_type: Type of item ("change_order", "service", "maintenance")
            
        Returns:
            Created task record if successful
        """
        # Map item type to Mission Control categories
        type_mapping = {
            'change_order': 'change-request',
            'service': 'support', 
            'maintenance': 'maintenance'
        }
        
        category = type_mapping.get(item_type, 'task')
        priority = 'high' if item_type == 'change_order' else 'medium'
        track = 'development' if item_type == 'change_order' else 'operations'
        
        # Get project info to build client context
        project_name = ""
        if item_data.get('project_id'):
            # Try to get project name from database
            try:
                from db_service import db_get_project
                project = db_get_project(item_data['project_id'])
                if project:
                    project_name = f" - {project.get('name', '')}"
            except:
                pass
        
        # Build title with appropriate badge
        title = item_data.get('title', 'Unnamed Item')
        ticket_id = item_data.get('id', 'UNKNOWN')
        
        if item_type == 'change_order':
            badge_title = f"[CO-{ticket_id[:8]}] {title}"
        elif item_type == 'service':
            badge_title = f"[TICKET-{ticket_id[:8]}] {title}" 
        elif item_type == 'maintenance':
            badge_title = f"[MAINT-{ticket_id[:8]}] {title}"
        else:
            badge_title = f"[{item_type.upper()}-{ticket_id[:8]}] {title}"
        
        task_data = {
            "title": badge_title + project_name,
            "description": item_data.get('description', ''),
            "priority": priority,
            "status": "backlog",
            "category": category,
            "track": track,
            "type": item_type,
            "ticketId": str(ticket_id),
            "clientId": item_data.get('client_id', 'client_001'),  # Default client
            "projectId": item_data.get('project_id'),
            "estimatedHours": item_data.get('estimated_hours', 0),
            "tags": [f"crm:{item_type}", f"ticket:{ticket_id}"]
        }
        
        # Use the /api/tasks/from-crm endpoint which handles badge generation
        return self._make_request("tasks/from-crm", "POST", task_data)


def create_mission_control_card(item_data: Dict[str, Any], item_type: str) -> Optional[str]:
    """
    Create Mission Control card for a CRM billable item.
    Called by db_service when creating change orders or service tickets.
    
    Args:
        item_data: The created CRM item (change order or service ticket)
        item_type: 'change_order', 'service', or 'maintenance'
        
    Returns:
        Mission Control task ID if successful, None otherwise
    """
    try:
        service = get_mission_control_service()
        result = service.create_task_from_crm_item(item_data, item_type)
        
        if result and result.get('task', {}).get('id'):
            return result['task']['id']
        
        return None
        
    except Exception as e:
        print(f"[mission_control_service] Error creating MC card: {e}")
        return None


# Singleton instance
_mc_service: Optional[MissionControlService] = None


def get_mission_control_service() -> MissionControlService:
    """Get singleton Mission Control service instance"""
    global _mc_service
    if _mc_service is None:
        _mc_service = MissionControlService()
    return _mc_service


def render_mission_control_time_tracking(project_id: str, mc_task_id: str = None):
    """
    Render Mission Control time tracking section for a project.
    Call this from the Projects detail page.
    
    Args:
        project_id: CRM project ID
        mc_task_id: Optional specific Mission Control task ID
    """
    service = get_mission_control_service()
    time_summary = service.get_project_time_summary(project_id, mc_task_id)
    
    if not time_summary.get("connected"):
        st.warning("⚠️ Cannot connect to Mission Control - time tracking unavailable")
        return
    
    st.markdown("### ⏱️ Time Tracking (Mission Control)")
    st.caption("*Live data from Mission Control*")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Hours", f"{time_summary['total_hours']:.1f}")
    
    with col2:
        st.metric("Tasks with Time", time_summary['tasks_count'])
    
    with col3:
        # Find primary agent (most hours)
        by_agent = time_summary.get('by_agent', {})
        primary_agent = max(by_agent.items(), key=lambda x: x[1])[0] if by_agent else "None"
        st.metric("Primary Agent", primary_agent)
    
    # Recent time entries
    recent_entries = time_summary.get('recent_entries', [])
    if recent_entries:
        st.markdown("#### 📋 Recent Time Entries")
        
        for entry in recent_entries[:5]:  # Show last 5
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    task_title = entry.get('task_title', 'Unknown Task')
                    task_id = entry.get('task_id')
                    
                    # Link to Mission Control
                    if task_id:
                        mc_link = f"https://mpt-mission-control.vercel.app/?task={task_id}"
                        st.markdown(f"**[{task_title}]({mc_link})**")
                    else:
                        st.markdown(f"**{task_title}**")
                    
                    note = entry.get('note', 'Time logged')
                    st.caption(note)
                    
                    agent = entry.get('agentName', 'Unknown')
                    timestamp = entry.get('timestamp', '')[:16] if entry.get('timestamp') else ''
                    st.caption(f"🤖 {agent} • {timestamp}")
                
                with col2:
                    st.markdown(f"{entry['hours']:.2f} hrs")
                
                with col3:
                    if entry.get('billable', True):
                        st.markdown("💰 Billable")
                    else:
                        st.markdown("⏸️ Non-billable")
                
                st.divider()
    else:
        st.info("No time entries found. Time will appear here as work is logged in Mission Control.")
    
    # Agent breakdown
    if by_agent:
        st.markdown("#### 👥 Time by Agent")
        
        for agent, hours in sorted(by_agent.items(), key=lambda x: x[1], reverse=True):
            percentage = (hours / time_summary['total_hours']) * 100 if time_summary['total_hours'] > 0 else 0
            st.progress(percentage / 100, text=f"{agent}: {hours:.1f} hrs ({percentage:.0f}%)")


def render_mission_control_integration(project_data: Dict[str, Any]):
    """
    Render Mission Control integration section with quick actions.
    
    Args:
        project_data: Project dictionary with id, name, etc.
    """
    service = get_mission_control_service()
    
    st.markdown("### 🎯 Mission Control Integration")
    
    mc_task_id = project_data.get("mc_task_id")
    
    if mc_task_id:
        # Show linked task
        mc_link = f"https://mpt-mission-control.vercel.app/?task={mc_task_id}"
        st.success(f"✅ Linked to Mission Control Task: [View Task]({mc_link})")
        
        # Quick actions
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 View in Mission Control", key="view_mc"):
                st.write(f"🔗 [Open Mission Control Task]({mc_link})")
        
        with col2:
            with st.popover("⏱️ Log Time"):
                hours = st.number_input("Hours", min_value=0.0, step=0.5, value=1.0)
                note = st.text_input("What did you work on?")
                
                if st.button("Log Time Entry"):
                    if hours > 0:
                        minutes = int(hours * 60)
                        result = service.log_manual_time(mc_task_id, minutes, "CRM User", note)
                        if result:
                            st.success("✅ Time logged successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to log time")
    else:
        # Offer to create/link task
        st.info("⚠️ This project is not linked to Mission Control yet.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔗 Create Mission Control Task"):
                task = service.create_task_from_project(project_data)
                if task:
                    # Update project with MC task ID
                    from db_service import get_db, db_update_project
                    if get_db():
                        db_update_project(project_data["id"], {"mc_task_id": task.get("id")})
                        st.success("✅ Mission Control task created and linked!")
                        st.rerun()
                else:
                    st.error("Failed to create Mission Control task")
        
        with col2:
            with st.popover("🔗 Link Existing Task"):
                existing_task_id = st.text_input("Mission Control Task ID")
                
                if st.button("Link Task") and existing_task_id:
                    # Update project with MC task ID
                    from db_service import get_db, db_update_project
                    if get_db():
                        success = service.link_project_to_task(existing_task_id, project_data["id"])
                        if success:
                            db_update_project(project_data["id"], {"mc_task_id": existing_task_id})
                            st.success("✅ Task linked successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to link task")