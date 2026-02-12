"""
Cross-System Service Layer for CRM
===================================

Enables CRM to query Accounting for invoice/financial data.

Architecture:
- CRM queries Accounting for project financials
- Invoice data flows FROM Accounting (source of truth)
- Time entries are shown from invoices, not raw MC data

This ensures CRM shows VERIFIED financial data (invoiced, reconciled)
rather than raw time entries.
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from datetime import datetime
import os


class AccountingService:
    """Query Accounting for invoice and financial data"""
    
    def __init__(self):
        # Accounting Supabase credentials
        self.url = st.secrets.get("accounting", {}).get(
            "SUPABASE_URL",
            os.environ.get("ACCOUNTING_SUPABASE_URL", "https://pezgfalkjoucwnfytubb.supabase.co")
        )
        self.key = st.secrets.get("accounting", {}).get(
            "SUPABASE_ANON_KEY",
            os.environ.get("ACCOUNTING_SUPABASE_ANON_KEY", "")
        )
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Optional[Client]:
        if not self._client and self.key:
            try:
                self._client = create_client(self.url, self.key)
            except Exception as e:
                st.warning(f"Could not connect to Accounting: {e}")
        return self._client
    
    def get_project_financials(self, project_id: str) -> Dict[str, Any]:
        """
        Get financial summary for a project from Accounting
        
        Returns:
        - total_invoiced: Total amount invoiced
        - total_paid: Amount received
        - balance_due: Outstanding balance
        - hours_billed: Total hours on invoices
        - invoices: List of invoices for this project
        - time_entries: Invoice line items (the verified time entries)
        """
        if not self.client:
            return self._empty_financials()
        
        try:
            # Query invoices for this project
            invoices_result = self.client.table("acc_invoices").select(
                "*"
            ).eq("project_id", project_id).execute()
            
            invoices = invoices_result.data or []
            
            # Calculate totals
            total_invoiced = sum(float(inv.get("total", 0)) for inv in invoices)
            total_paid = sum(float(inv.get("amount_paid", 0)) for inv in invoices)
            
            # Get line items for all invoices
            invoice_ids = [inv.get("id") for inv in invoices]
            time_entries = []
            hours_billed = 0
            
            if invoice_ids:
                # Query invoice line items
                line_items_result = self.client.table("acc_invoice_line_items").select(
                    "*"
                ).in_("invoice_id", invoice_ids).execute()
                
                for item in line_items_result.data or []:
                    hours = float(item.get("hours", 0))
                    hours_billed += hours
                    
                    time_entries.append({
                        "id": item.get("id"),
                        "invoice_id": item.get("invoice_id"),
                        "date": item.get("date"),
                        "task_id": item.get("task_id"),
                        "task_title": item.get("task_title"),
                        "description": item.get("description"),
                        "agent_name": item.get("agent_name"),
                        "hours": hours,
                        "rate": float(item.get("rate", 0)),
                        "amount": float(item.get("amount", 0)),
                        "billable": True  # If it's on an invoice, it's billable
                    })
            
            return {
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "balance_due": total_invoiced - total_paid,
                "hours_billed": hours_billed,
                "invoice_count": len(invoices),
                "invoices": invoices,
                "time_entries": time_entries
            }
            
        except Exception as e:
            st.error(f"Error fetching project financials: {e}")
            return self._empty_financials()
    
    def get_client_financials(self, client_id: str) -> Dict[str, Any]:
        """Get financial summary for a client (all their projects)"""
        if not self.client:
            return self._empty_financials()
        
        try:
            # Query all invoices for this client
            invoices_result = self.client.table("acc_invoices").select(
                "*"
            ).eq("client_id", client_id).execute()
            
            invoices = invoices_result.data or []
            
            total_invoiced = sum(float(inv.get("total", 0)) for inv in invoices)
            total_paid = sum(float(inv.get("amount_paid", 0)) for inv in invoices)
            
            return {
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "balance_due": total_invoiced - total_paid,
                "invoice_count": len(invoices),
                "invoices": invoices
            }
            
        except Exception as e:
            st.error(f"Error fetching client financials: {e}")
            return self._empty_financials()
    
    def _empty_financials(self) -> Dict[str, Any]:
        """Return empty financials structure"""
        return {
            "total_invoiced": 0,
            "total_paid": 0,
            "balance_due": 0,
            "hours_billed": 0,
            "invoice_count": 0,
            "invoices": [],
            "time_entries": []
        }


# Singleton instance
_accounting_service: Optional[AccountingService] = None


def get_accounting_service() -> AccountingService:
    global _accounting_service
    if _accounting_service is None:
        _accounting_service = AccountingService()
    return _accounting_service


def render_project_financials(project_id: str, project_estimate: float = 0):
    """
    Render the financials section for a project
    Call this from the Projects page to show live financial data.
    """
    service = get_accounting_service()
    financials = service.get_project_financials(project_id)
    
    st.markdown("### 💰 Project Financials")
    st.caption("*Live data from Accounting*")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Invoiced", f"${financials['total_invoiced']:,.2f}")
    
    with col2:
        st.metric("Total Paid", f"${financials['total_paid']:,.2f}")
    
    with col3:
        st.metric("Balance Due", f"${financials['balance_due']:,.2f}")
    
    with col4:
        st.metric("Hours Billed", f"{financials['hours_billed']:.1f}")
    
    # Budget progress if estimate provided
    if project_estimate > 0:
        budget_used = (financials['total_invoiced'] / project_estimate) * 100
        st.progress(min(budget_used / 100, 1.0), text=f"Budget: {budget_used:.1f}% used (${financials['total_invoiced']:,.2f} of ${project_estimate:,.2f})")
    
    # Time entries from invoices
    if financials['time_entries']:
        st.markdown("#### 📋 Billed Time Entries")
        
        for entry in financials['time_entries']:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    task_title = entry.get('task_title', 'Unknown Task')
                    task_id = entry.get('task_id')
                    
                    # Link to Mission Control card if task_id exists
                    if task_id:
                        mc_link = f"https://mpt-mission-control.vercel.app/?task={task_id}"
                        st.markdown(f"**[{task_title}]({mc_link})**")
                    else:
                        st.markdown(f"**{task_title}**")
                    
                    description = entry.get('description', '')
                    if description:
                        st.caption(description)
                    
                    agent = entry.get('agent_name', 'Unknown')
                    date = entry.get('date', '')[:10] if entry.get('date') else ''
                    st.caption(f"🤖 {agent} • {date}")
                
                with col2:
                    st.markdown(f"{entry['hours']:.2f} hrs")
                
                with col3:
                    st.markdown(f"${entry['rate']:.2f}/hr")
                
                with col4:
                    st.markdown(f"**${entry['amount']:.2f}**")
                
                st.divider()
    else:
        st.info("No invoiced time entries yet. Time entries appear here after invoicing in Accounting.")
    
    # Invoices list
    if financials['invoices']:
        with st.expander(f"📄 Invoices ({financials['invoice_count']})"):
            for inv in financials['invoices']:
                st.markdown(f"**Invoice #{inv.get('invoice_number', inv.get('id')[:8])}** — ${float(inv.get('total', 0)):,.2f} — {inv.get('status', 'draft')}")
