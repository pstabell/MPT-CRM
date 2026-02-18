"""
SMS Service for MPT-CRM using Twilio
Handles SMS sending and message history tracking
"""

import streamlit as st
from twilio.rest import Client
from datetime import datetime
from supabase import create_client, Client as SupabaseClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        """Initialize SMS service with Twilio and Supabase clients"""
        try:
            # Get Twilio credentials from Streamlit secrets
            self.account_sid = st.secrets["twilio"]["TWILIO_ACCOUNT_SID"]
            self.auth_token = st.secrets["twilio"]["TWILIO_AUTH_TOKEN"] 
            self.from_phone = st.secrets["twilio"]["TWILIO_PHONE_NUMBER"]
            
            # Initialize Twilio client
            self.client = Client(self.account_sid, self.auth_token)
            
            # Initialize Supabase client for message history
            self.supabase: SupabaseClient = create_client(
                st.secrets["supabase"]["url"],
                st.secrets["supabase"]["anon_key"]
            )
            
            logger.info("SMS Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing SMS service: {str(e)}")
            raise e

    def send_sms(self, to_phone: str, message: str, contact_id: str = None) -> dict:
        """
        Send SMS message using Twilio and log to Supabase
        
        Args:
            to_phone (str): Recipient phone number in E.164 format (+1234567890)
            message (str): Message content (max 160 chars)
            contact_id (str): CRM contact ID for history tracking
            
        Returns:
            dict: Result with success status, message_id, and any error info
        """
        try:
            # Validate phone number format
            if not to_phone.startswith('+'):
                to_phone = f"+{to_phone}"
            
            # Validate message length
            if len(message) > 160:
                return {
                    "success": False,
                    "error": "Message exceeds 160 character limit",
                    "message_length": len(message)
                }
            
            # Send SMS via Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=to_phone
            )
            
            logger.info(f"SMS sent successfully. SID: {twilio_message.sid}")
            
            # Log message to Supabase history
            history_result = self._log_sms_to_history(
                contact_id=contact_id,
                to_phone=to_phone,
                message=message,
                twilio_sid=twilio_message.sid,
                status=twilio_message.status
            )
            
            return {
                "success": True,
                "message_id": twilio_message.sid,
                "status": twilio_message.status,
                "to": to_phone,
                "message": message,
                "history_logged": history_result["success"]
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            
            # Still try to log failed attempt
            self._log_sms_to_history(
                contact_id=contact_id,
                to_phone=to_phone,
                message=message,
                twilio_sid=None,
                status="failed",
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "to": to_phone,
                "message": message
            }

    def _log_sms_to_history(self, contact_id: str, to_phone: str, message: str, 
                           twilio_sid: str, status: str, error_message: str = None) -> dict:
        """
        Log SMS to Supabase crm_sms_history table
        
        Args:
            contact_id (str): CRM contact ID
            to_phone (str): Recipient phone number
            message (str): Message content
            twilio_sid (str): Twilio message SID (None if failed)
            status (str): Message status (sent, failed, etc.)
            error_message (str): Error message if failed
            
        Returns:
            dict: Result of history logging
        """
        try:
            history_data = {
                "contact_id": contact_id,
                "phone_number": to_phone,
                "message": message,
                "twilio_sid": twilio_sid,
                "status": status,
                "sent_at": datetime.utcnow().isoformat(),
                "error_message": error_message
            }
            
            result = self.supabase.table("crm_sms_history").insert(history_data).execute()
            
            logger.info(f"SMS history logged for contact {contact_id}")
            return {"success": True, "history_id": result.data[0]["id"] if result.data else None}
            
        except Exception as e:
            logger.error(f"Error logging SMS history: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_sms_history(self, contact_id: str, limit: int = 50) -> list:
        """
        Get SMS history for a contact
        
        Args:
            contact_id (str): CRM contact ID
            limit (int): Number of messages to retrieve
            
        Returns:
            list: SMS history records
        """
        try:
            result = self.supabase.table("crm_sms_history")\
                .select("*")\
                .eq("contact_id", contact_id)\
                .order("sent_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching SMS history: {str(e)}")
            return []

    def validate_phone_number(self, phone: str) -> dict:
        """
        Validate and format phone number for SMS
        
        Args:
            phone (str): Phone number to validate
            
        Returns:
            dict: Validation result with formatted number
        """
        try:
            # Remove all non-numeric characters except +
            import re
            clean_phone = re.sub(r'[^\d+]', '', phone)
            
            # Add + if not present
            if not clean_phone.startswith('+'):
                # Assume US number if 10 digits
                if len(clean_phone) == 10:
                    clean_phone = f"+1{clean_phone}"
                elif len(clean_phone) == 11 and clean_phone.startswith('1'):
                    clean_phone = f"+{clean_phone}"
                else:
                    clean_phone = f"+{clean_phone}"
            
            # Basic validation - should be at least 10 digits after +
            if len(clean_phone) < 11:
                return {
                    "valid": False,
                    "error": "Phone number too short",
                    "formatted": clean_phone
                }
            
            return {
                "valid": True,
                "formatted": clean_phone,
                "original": phone
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "formatted": phone
            }


# Global SMS service instance
@st.cache_resource
def get_sms_service():
    """Get cached SMS service instance"""
    return SMSService()


# Convenience functions for easy import
def send_sms(to_phone: str, message: str, contact_id: str = None) -> dict:
    """Send SMS message - convenience function"""
    sms_service = get_sms_service()
    return sms_service.send_sms(to_phone, message, contact_id)


def get_sms_history(contact_id: str, limit: int = 50) -> list:
    """Get SMS history - convenience function"""
    sms_service = get_sms_service()
    return sms_service.get_sms_history(contact_id, limit)


def validate_phone_number(phone: str) -> dict:
    """Validate phone number - convenience function"""
    sms_service = get_sms_service()
    return sms_service.validate_phone_number(phone)