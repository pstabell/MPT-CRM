"""
Fax Service for MPT-CRM using Sinch Fax API
With email fallback when fax delivery fails
"""

import streamlit as st
import requests
import base64
import logging
from datetime import datetime
from supabase import create_client, Client as SupabaseClient
from typing import Optional
import re
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaxService:
    """Sinch Fax Service with Email Fallback"""
    
    SINCH_API_BASE = "https://fax.api.sinch.com"
    
    def __init__(self):
        """Initialize fax service with Sinch and Supabase clients"""
        try:
            # Sinch Fax credentials
            self.project_id = st.secrets.get("sinch", {}).get("PROJECT_ID", "2e3ddc60-d548-41a4-ba88-03f26fcfacbf")
            self.access_key = st.secrets.get("sinch", {}).get("ACCESS_KEY_ID", "c3050b80-f691-46b4-a4fb-b9896c674554")
            self.key_secret = st.secrets.get("sinch", {}).get("KEY_SECRET", "EGR3pLiv8l1Y1ptI1Pe~qjmJPH")
            self.from_fax = st.secrets.get("sinch", {}).get("FAX_NUMBER", "+12392687500")
            
            # Email fallback settings (SendGrid/SMTP)
            self.smtp_server = st.secrets.get("email", {}).get("SMTP_SERVER", "smtp.sendgrid.net")
            self.smtp_port = st.secrets.get("email", {}).get("SMTP_PORT", 587)
            self.smtp_user = st.secrets.get("email", {}).get("SMTP_USER", "apikey")
            self.smtp_password = st.secrets.get("email", {}).get("SMTP_PASSWORD", "")
            self.from_email = st.secrets.get("email", {}).get("FROM_EMAIL", "Support@MetroPointTech.com")
            
            # Initialize Supabase client for history
            self.supabase: SupabaseClient = create_client(
                st.secrets["supabase"]["url"],
                st.secrets["supabase"]["anon_key"]
            )
            
            logger.info("Fax Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Fax service: {str(e)}")
            raise e

    def _get_auth_headers(self) -> dict:
        """Get Sinch API authentication headers"""
        credentials = f"{self.access_key}:{self.key_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        }

    def send_fax(
        self,
        to_fax: str,
        pdf_path: str = None,
        pdf_content: bytes = None,
        contact_id: str = None,
        contact_email: str = None,
        contact_name: str = None,
        fallback_on_failure: bool = True
    ) -> dict:
        """
        Send fax using Sinch API with optional email fallback
        
        Args:
            to_fax (str): Recipient fax number in E.164 format (+1234567890)
            pdf_path (str): Path to PDF file to fax
            pdf_content (bytes): Raw PDF content (alternative to pdf_path)
            contact_id (str): CRM contact ID for history tracking
            contact_email (str): Email for fallback delivery
            contact_name (str): Contact name for fallback email
            fallback_on_failure (bool): Whether to send email if fax fails
            
        Returns:
            dict: Result with success status, fax_id, and delivery method
        """
        try:
            # Validate and format fax number
            fax_validation = self.validate_fax_number(to_fax)
            if not fax_validation["valid"]:
                return {
                    "success": False,
                    "error": fax_validation["error"],
                    "to": to_fax
                }
            to_fax = fax_validation["formatted"]
            
            # Get PDF content
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    pdf_content = f.read()
            
            if not pdf_content:
                return {
                    "success": False,
                    "error": "No PDF content provided",
                    "to": to_fax
                }
            
            # Encode PDF to base64
            pdf_base64 = base64.b64encode(pdf_content).decode()
            
            # Build Sinch fax request
            fax_payload = {
                "to": to_fax,
                "from": self.from_fax,
                "contentUrl": f"data:application/pdf;base64,{pdf_base64}",
                "headerText": "Metro Point Technology"
            }
            
            # Send fax via Sinch API
            response = requests.post(
                f"{self.SINCH_API_BASE}/v3/projects/{self.project_id}/faxes",
                headers=self._get_auth_headers(),
                json=fax_payload,
                timeout=60
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                fax_id = result.get("id", result.get("faxId"))
                
                logger.info(f"Fax sent successfully. ID: {fax_id}")
                
                # Log to history
                self._log_fax_to_history(
                    contact_id=contact_id,
                    to_fax=to_fax,
                    fax_id=fax_id,
                    status="sent",
                    delivery_method="fax"
                )
                
                return {
                    "success": True,
                    "fax_id": fax_id,
                    "status": "sent",
                    "to": to_fax,
                    "delivery_method": "fax"
                }
            else:
                error_msg = f"Sinch API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # Try email fallback
                if fallback_on_failure and contact_email:
                    return self._send_email_fallback(
                        contact_email=contact_email,
                        contact_name=contact_name,
                        pdf_content=pdf_content,
                        contact_id=contact_id,
                        original_fax=to_fax,
                        fax_error=error_msg
                    )
                
                # Log failed attempt
                self._log_fax_to_history(
                    contact_id=contact_id,
                    to_fax=to_fax,
                    fax_id=None,
                    status="failed",
                    delivery_method="fax",
                    error_message=error_msg
                )
                
                return {
                    "success": False,
                    "error": error_msg,
                    "to": to_fax,
                    "delivery_method": "fax_failed"
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error sending fax: {error_msg}")
            
            # Try email fallback on exception
            if fallback_on_failure and contact_email:
                return self._send_email_fallback(
                    contact_email=contact_email,
                    contact_name=contact_name,
                    pdf_content=pdf_content,
                    contact_id=contact_id,
                    original_fax=to_fax,
                    fax_error=error_msg
                )
            
            # Log failed attempt
            self._log_fax_to_history(
                contact_id=contact_id,
                to_fax=to_fax,
                fax_id=None,
                status="failed",
                delivery_method="fax",
                error_message=error_msg
            )
            
            return {
                "success": False,
                "error": error_msg,
                "to": to_fax,
                "delivery_method": "fax_failed"
            }

    def _send_email_fallback(
        self,
        contact_email: str,
        contact_name: str,
        pdf_content: bytes,
        contact_id: str,
        original_fax: str,
        fax_error: str
    ) -> dict:
        """
        Send email fallback when fax fails
        
        Args:
            contact_email: Recipient email
            contact_name: Recipient name
            pdf_content: PDF to attach
            contact_id: CRM contact ID
            original_fax: Original fax number (for logging)
            fax_error: Original fax error message
            
        Returns:
            dict: Email send result
        """
        try:
            logger.info(f"Fax failed, sending email fallback to {contact_email}")
            
            # Build email
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = contact_email
            msg['Subject'] = "Document from Metro Point Technology"
            
            # Email body
            body = f"""Hello{' ' + contact_name if contact_name else ''},

Please find attached a document from Metro Point Technology.

We attempted to send this via fax but encountered a delivery issue. 
We're sending it via email to ensure you receive it promptly.

If you have any questions, please don't hesitate to contact us.

Best regards,
Metro Point Technology
Support@MetroPointTech.com
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PDF
            pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition', 
                'attachment', 
                filename='document.pdf'
            )
            msg.attach(pdf_attachment)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email fallback sent successfully to {contact_email}")
            
            # Log to history as email fallback
            self._log_fax_to_history(
                contact_id=contact_id,
                to_fax=original_fax,
                to_email=contact_email,
                fax_id=None,
                status="delivered_via_email",
                delivery_method="email_fallback",
                error_message=f"Original fax error: {fax_error}"
            )
            
            return {
                "success": True,
                "delivery_method": "email_fallback",
                "to_email": contact_email,
                "original_fax": original_fax,
                "original_error": fax_error,
                "message": f"Fax failed but document delivered via email to {contact_email}"
            }
            
        except Exception as e:
            error_msg = f"Email fallback also failed: {str(e)}"
            logger.error(error_msg)
            
            # Log both failures
            self._log_fax_to_history(
                contact_id=contact_id,
                to_fax=original_fax,
                to_email=contact_email,
                fax_id=None,
                status="failed",
                delivery_method="both_failed",
                error_message=f"Fax: {fax_error} | Email: {str(e)}"
            )
            
            return {
                "success": False,
                "error": error_msg,
                "delivery_method": "both_failed",
                "fax_error": fax_error,
                "email_error": str(e)
            }

    def check_fax_status(self, fax_id: str) -> dict:
        """
        Check status of a sent fax
        
        Args:
            fax_id: Sinch fax ID
            
        Returns:
            dict: Fax status details
        """
        try:
            response = requests.get(
                f"{self.SINCH_API_BASE}/v3/projects/{self.project_id}/faxes/{fax_id}",
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Status check failed: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _log_fax_to_history(
        self,
        contact_id: str,
        to_fax: str,
        fax_id: str = None,
        to_email: str = None,
        status: str = "pending",
        delivery_method: str = "fax",
        error_message: str = None
    ) -> dict:
        """Log fax/email to Supabase history table"""
        try:
            history_data = {
                "contact_id": contact_id,
                "fax_number": to_fax,
                "email_address": to_email,
                "sinch_fax_id": fax_id,
                "status": status,
                "delivery_method": delivery_method,
                "sent_at": datetime.utcnow().isoformat(),
                "error_message": error_message
            }
            
            result = self.supabase.table("crm_fax_history").insert(history_data).execute()
            
            logger.info(f"Fax history logged for contact {contact_id}")
            return {"success": True, "history_id": result.data[0]["id"] if result.data else None}
            
        except Exception as e:
            logger.error(f"Error logging fax history: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_fax_history(self, contact_id: str, limit: int = 50) -> list:
        """Get fax history for a contact"""
        try:
            result = self.supabase.table("crm_fax_history")\
                .select("*")\
                .eq("contact_id", contact_id)\
                .order("sent_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching fax history: {str(e)}")
            return []

    def validate_fax_number(self, fax: str) -> dict:
        """Validate and format fax number for Sinch API"""
        try:
            # Remove all non-numeric characters except +
            clean_fax = re.sub(r'[^\d+]', '', fax)
            
            # Add + if not present
            if not clean_fax.startswith('+'):
                if len(clean_fax) == 10:
                    clean_fax = f"+1{clean_fax}"
                elif len(clean_fax) == 11 and clean_fax.startswith('1'):
                    clean_fax = f"+{clean_fax}"
                else:
                    clean_fax = f"+{clean_fax}"
            
            # Basic validation
            if len(clean_fax) < 11:
                return {
                    "valid": False,
                    "error": "Fax number too short",
                    "formatted": clean_fax
                }
            
            return {
                "valid": True,
                "formatted": clean_fax,
                "original": fax
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "formatted": fax
            }


# Global fax service instance
@st.cache_resource
def get_fax_service():
    """Get cached fax service instance"""
    return FaxService()


# Convenience functions
def send_fax(
    to_fax: str,
    pdf_path: str = None,
    pdf_content: bytes = None,
    contact_id: str = None,
    contact_email: str = None,
    contact_name: str = None,
    fallback_on_failure: bool = True
) -> dict:
    """Send fax with optional email fallback - convenience function"""
    fax_service = get_fax_service()
    return fax_service.send_fax(
        to_fax=to_fax,
        pdf_path=pdf_path,
        pdf_content=pdf_content,
        contact_id=contact_id,
        contact_email=contact_email,
        contact_name=contact_name,
        fallback_on_failure=fallback_on_failure
    )


def check_fax_status(fax_id: str) -> dict:
    """Check fax status - convenience function"""
    fax_service = get_fax_service()
    return fax_service.check_fax_status(fax_id)


def get_fax_history(contact_id: str, limit: int = 50) -> list:
    """Get fax history - convenience function"""
    fax_service = get_fax_service()
    return fax_service.get_fax_history(contact_id, limit)


def validate_fax_number(fax: str) -> dict:
    """Validate fax number - convenience function"""
    fax_service = get_fax_service()
    return fax_service.validate_fax_number(fax)
