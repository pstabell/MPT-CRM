"""
Twilio SMS Service for MPT-CRM
=============================

Handles sending and receiving SMS messages via Twilio API.
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional, List
import db_service

# Twilio Configuration - loaded from environment or Streamlit secrets
import streamlit as st

def get_twilio_config():
    """Get Twilio credentials from environment or Streamlit secrets"""
    # Try environment variables first
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    phone_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    # Fall back to Streamlit secrets
    if not account_sid:
        try:
            account_sid = st.secrets.get("twilio", {}).get("account_sid", "")
        except Exception:
            account_sid = ""
    if not auth_token:
        try:
            auth_token = st.secrets.get("twilio", {}).get("auth_token", "")
        except Exception:
            auth_token = ""
    if not phone_number:
        try:
            phone_number = st.secrets.get("twilio", {}).get("phone_number", "+12394267058")
        except Exception:
            phone_number = "+12394267058"
    
    return account_sid, auth_token, phone_number

TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER = get_twilio_config()

class TwilioSMSService:
    """Service class for Twilio SMS operations"""
    
    def __init__(self):
        self.account_sid = TWILIO_ACCOUNT_SID
        self.auth_token = TWILIO_AUTH_TOKEN
        self.from_number = TWILIO_PHONE_NUMBER
        self.api_base = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
    
    def send_sms(self, to_number: str, message: str, contact_id: str = None) -> Dict:
        """Send an SMS message via Twilio
        
        Args:
            to_number: Recipient phone number (E.164 format preferred)
            message: Message content (max 1600 chars)
            contact_id: CRM contact UUID (optional)
        
        Returns:
            Dict with success/error status and message details
        """
        try:
            # Normalize phone number
            to_number = self._normalize_phone_number(to_number)
            
            # Truncate message if too long
            if len(message) > 1600:
                message = message[:1597] + "..."
            
            # Twilio API request - use Messaging Service for 10DLC compliance
            url = f"{self.api_base}/Messages.json"
            data = {
                'MessagingServiceSid': 'MG816b5f0b45fd5d92e61d12c721ac14f0',  # MPT Customer Notifications
                'To': to_number,
                'Body': message
            }
            
            response = requests.post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=30
            )
            
            if response.status_code == 201:
                # Success - parse Twilio response
                twilio_data = response.json()
                twilio_sid = twilio_data.get('sid')
                status = twilio_data.get('status', 'sending')
                
                # Save to database
                if contact_id:
                    db_service.db_create_sms_message(
                        contact_id=contact_id,
                        body=message,
                        direction='outbound',
                        from_number=self.from_number,
                        to_number=to_number,
                        twilio_message_sid=twilio_sid,
                        status=status
                    )
                
                return {
                    'success': True,
                    'message_sid': twilio_sid,
                    'status': status,
                    'to': to_number,
                    'body': message
                }
            else:
                # Error from Twilio
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', f'HTTP {response.status_code}')
                error_code = error_data.get('code', response.status_code)
                
                return {
                    'success': False,
                    'error_code': error_code,
                    'error_message': error_msg,
                    'to': to_number,
                    'body': message
                }
                
        except Exception as e:
            return {
                'success': False,
                'error_message': f'Exception: {str(e)}',
                'to': to_number,
                'body': message
            }
    
    def handle_webhook(self, webhook_data: Dict) -> bool:
        """Handle incoming Twilio webhook (status updates and incoming messages)
        
        Args:
            webhook_data: Webhook payload from Twilio
        
        Returns:
            bool: True if handled successfully
        """
        try:
            message_sid = webhook_data.get('MessageSid') or webhook_data.get('SmsSid')
            status = webhook_data.get('MessageStatus') or webhook_data.get('SmsStatus')
            
            # Handle status updates for outbound messages
            if message_sid and status:
                error_code = webhook_data.get('ErrorCode')
                error_message = webhook_data.get('ErrorMessage')
                
                db_service.db_update_sms_status(
                    twilio_message_sid=message_sid,
                    status=status,
                    error_code=error_code,
                    error_message=error_message
                )
                
                print(f"[SMS] Updated status for {message_sid}: {status}")
            
            # Handle incoming messages
            if webhook_data.get('Body'):  # This indicates an incoming message
                return self._handle_incoming_message(webhook_data)
            
            return True
            
        except Exception as e:
            print(f"[SMS] Webhook error: {e}")
            return False
    
    def _handle_incoming_message(self, webhook_data: Dict) -> bool:
        """Handle incoming SMS message"""
        try:
            from_number = webhook_data.get('From')
            to_number = webhook_data.get('To', self.from_number)
            body = webhook_data.get('Body', '')
            message_sid = webhook_data.get('MessageSid')
            
            # Find contact by phone number
            contact = db_service.db_find_contact_by_phone(from_number)
            
            if contact:
                contact_id = contact['id']
                contact_name = f"{contact['first_name']} {contact['last_name']}"
                print(f"[SMS] Incoming from {contact_name}: {body[:50]}...")
            else:
                # Create a new prospect contact for unknown numbers
                contact_id = self._create_unknown_contact(from_number)
                print(f"[SMS] Incoming from unknown number {from_number}: {body[:50]}...")
            
            # Save incoming message to database
            if contact_id:
                db_service.db_create_sms_message(
                    contact_id=contact_id,
                    body=body,
                    direction='inbound',
                    from_number=from_number,
                    to_number=to_number,
                    twilio_message_sid=message_sid,
                    status='received'
                )
            
            return True
            
        except Exception as e:
            print(f"[SMS] Error handling incoming message: {e}")
            return False
    
    def _create_unknown_contact(self, phone_number: str) -> Optional[str]:
        """Create a prospect contact for unknown phone number"""
        try:
            # Extract area code for basic info
            clean_phone = phone_number.replace('+1', '').replace('+', '')
            area_code = clean_phone[:3] if len(clean_phone) >= 10 else '???'
            
            contact = db_service.db_create_contact({
                'type': 'prospect',
                'first_name': 'SMS',
                'last_name': f'Contact {area_code}',
                'company': '',
                'email': '',
                'phone': phone_number,
                'source': 'SMS Inbound',
                'source_detail': 'Auto-created from inbound SMS',
                'tags': ['sms-prospect'],
                'notes': f'Contact created automatically from inbound SMS on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            })
            
            return contact['id'] if contact else None
            
        except Exception as e:
            print(f"[SMS] Error creating unknown contact: {e}")
            return None
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number to E.164 format"""
        import re
        
        # Remove all non-digit characters
        digits = re.sub(r'[^0-9]', '', phone_number)
        
        # Add country code for US numbers
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        else:
            # Return as-is for international numbers
            return f"+{digits}" if not phone_number.startswith('+') else phone_number
    
    def get_message_status(self, message_sid: str) -> Dict:
        """Get current status of a message from Twilio"""
        try:
            url = f"{self.api_base}/Messages/{message_sid}.json"
            response = requests.get(
                url,
                auth=(self.account_sid, self.auth_token),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status'),
                    'error_code': data.get('error_code'),
                    'error_message': data.get('error_message'),
                    'date_sent': data.get('date_sent'),
                    'date_updated': data.get('date_updated')
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global service instance
sms_service = TwilioSMSService()

# Convenience functions for use in other modules
def send_sms(to_number: str, message: str, contact_id: str = None) -> Dict:
    """Send SMS (convenience function)"""
    return sms_service.send_sms(to_number, message, contact_id)

def handle_sms_webhook(webhook_data: Dict) -> bool:
    """Handle SMS webhook (convenience function)"""
    return sms_service.handle_webhook(webhook_data)