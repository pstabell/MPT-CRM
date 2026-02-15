"""
E-Signature Email Service
=========================

Handles sending emails for the e-signature workflow:
- Signing request emails with secure links
- Completion notifications
- Reminder emails
- Status updates

Integrates with SendGrid API for reliable email delivery.
"""

import os
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    SENDGRID_AVAILABLE = True
except ImportError:
    print("⚠️  SendGrid not available. Install with: pip install sendgrid")
    SENDGRID_AVAILABLE = False

from esign_components import generate_signing_url

class ESignEmailService:
    """Email service for e-signature workflow"""
    
    def __init__(self):
        """Initialize email service with SendGrid configuration"""
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'patrick@metropointtechnology.com')
        self.from_name = os.getenv('SENDGRID_FROM_NAME', 'Patrick Stabell')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'patrick@metropointtechnology.com')
        
        if SENDGRID_AVAILABLE and self.api_key:
            self.client = SendGridAPIClient(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️  SendGrid not configured. Check SENDGRID_API_KEY in .env")
    
    def send_signing_request(self, document_data: Dict, signing_url: str, 
                           custom_message: Optional[str] = None) -> bool:
        """
        Send signing request email to signer
        
        Args:
            document_data: Document metadata from database
            signing_url: Secure signing URL
            custom_message: Optional custom message from sender
        
        Returns:
            bool: True if email sent successfully
        """
        if not self.client:
            print("❌ SendGrid not configured - cannot send email")
            return False
        
        try:
            # Calculate expiration date for display
            expires_at = document_data.get('expires_at')
            if expires_at:
                expiry_date = expires_at.split('T')[0] if 'T' in expires_at else expires_at
            else:
                expiry_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
            
            # Email subject
            subject = f"Document Signature Required: {document_data.get('title', 'Document')}"
            
            # Email content
            html_content = self._generate_signing_request_html(
                document_data, signing_url, expiry_date, custom_message
            )
            
            text_content = self._generate_signing_request_text(
                document_data, signing_url, expiry_date, custom_message
            )
            
            # Create email
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=document_data.get('signer_email'),
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code in [200, 202]:
                print(f"✅ Signing request sent to {document_data.get('signer_email')}")
                return True
            else:
                print(f"❌ Failed to send email. Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending signing request: {e}")
            return False
    
    def send_completion_notification(self, document_data: Dict, signed_pdf_path: Optional[str] = None) -> bool:
        """
        Send completion notification to sender and signer
        
        Args:
            document_data: Document metadata from database
            signed_pdf_path: Path to signed PDF file for attachment
        
        Returns:
            bool: True if notifications sent successfully
        """
        if not self.client:
            print("❌ SendGrid not configured - cannot send notifications")
            return False
        
        try:
            # Send to signer (confirmation)
            signer_success = self._send_signer_confirmation(document_data, signed_pdf_path)
            
            # Send to admin/sender (notification)
            admin_success = self._send_admin_notification(document_data, signed_pdf_path)
            
            return signer_success and admin_success
            
        except Exception as e:
            print(f"❌ Error sending completion notifications: {e}")
            return False
    
    def send_reminder_email(self, document_data: Dict, signing_url: str) -> bool:
        """
        Send reminder email for unsigned documents
        
        Args:
            document_data: Document metadata from database
            signing_url: Secure signing URL
        
        Returns:
            bool: True if reminder sent successfully
        """
        if not self.client:
            print("❌ SendGrid not configured - cannot send reminder")
            return False
        
        try:
            subject = f"Reminder: Document Signature Pending - {document_data.get('title', 'Document')}"
            
            html_content = self._generate_reminder_html(document_data, signing_url)
            text_content = self._generate_reminder_text(document_data, signing_url)
            
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=document_data.get('signer_email'),
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 202]:
                print(f"✅ Reminder sent to {document_data.get('signer_email')}")
                return True
            else:
                print(f"❌ Failed to send reminder. Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending reminder: {e}")
            return False
    
    def _send_signer_confirmation(self, document_data: Dict, signed_pdf_path: Optional[str] = None) -> bool:
        """Send confirmation to signer that document was completed"""
        try:
            subject = f"Document Signed Successfully: {document_data.get('title', 'Document')}"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                    <h1>✅ Document Signed Successfully</h1>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa;">
                    <p>Dear {document_data.get('signer_name', 'Valued Customer')},</p>
                    
                    <p>Thank you for signing the document: <strong>{document_data.get('title', 'Document')}</strong></p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>Signature Details:</h3>
                        <ul>
                            <li><strong>Document:</strong> {document_data.get('title', 'Document')}</li>
                            <li><strong>Signed On:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}</li>
                            <li><strong>Verification Hash:</strong> {document_data.get('signature_hash', 'Pending')[:16]}...</li>
                        </ul>
                    </div>
                    
                    <p>This document is now legally binding and has been securely stored. You will receive a copy for your records.</p>
                    
                    <p>If you have any questions, please contact us.</p>
                    
                    <p>Best regards,<br>
                    {self.from_name}<br>
                    Metro Point Technology</p>
                </div>
                
                <div style="background: #333; color: white; padding: 15px; text-align: center; font-size: 12px;">
                    This signature was captured using MPT-CRM E-Signature system and is legally compliant under the E-SIGN Act.
                </div>
            </div>
            """
            
            text_content = f"""
            Document Signed Successfully
            
            Dear {document_data.get('signer_name', 'Valued Customer')},
            
            Thank you for signing the document: {document_data.get('title', 'Document')}
            
            Signature Details:
            - Document: {document_data.get('title', 'Document')}
            - Signed On: {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}
            - Verification Hash: {document_data.get('signature_hash', 'Pending')[:16]}...
            
            This document is now legally binding and has been securely stored.
            
            Best regards,
            {self.from_name}
            Metro Point Technology
            """
            
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=document_data.get('signer_email'),
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            # Attach signed PDF if available
            if signed_pdf_path and os.path.exists(signed_pdf_path):
                with open(signed_pdf_path, 'rb') as f:
                    pdf_data = f.read()
                    encoded_pdf = base64.b64encode(pdf_data).decode()
                
                attachment = Attachment(
                    FileContent(encoded_pdf),
                    FileName(f"{document_data.get('title', 'document')}_signed.pdf"),
                    FileType("application/pdf"),
                    Disposition("attachment")
                )
                message.attachment = attachment
            
            response = self.client.send(message)
            return response.status_code in [200, 202]
            
        except Exception as e:
            print(f"❌ Error sending signer confirmation: {e}")
            return False
    
    def _send_admin_notification(self, document_data: Dict, signed_pdf_path: Optional[str] = None) -> bool:
        """Send notification to admin/sender that document was signed"""
        try:
            subject = f"✅ Document Signed: {document_data.get('title', 'Document')} - {document_data.get('signer_name')}"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #28a745; color: white; padding: 20px; text-align: center;">
                    <h1>✅ Document Signed</h1>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa;">
                    <p>Good news! Your document has been signed successfully.</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>Signature Details:</h3>
                        <ul>
                            <li><strong>Document:</strong> {document_data.get('title', 'Document')}</li>
                            <li><strong>Signer:</strong> {document_data.get('signer_name')} ({document_data.get('signer_email')})</li>
                            <li><strong>Client:</strong> {document_data.get('client_name', 'N/A')}</li>
                            <li><strong>Signed On:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}</li>
                            <li><strong>Status:</strong> Completed</li>
                        </ul>
                    </div>
                    
                    <p>The signed document has been processed and stored securely. The verification hash ensures document integrity and legal compliance.</p>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>Document will be automatically filed in SharePoint</li>
                        <li>Signer will receive confirmation copy</li>
                        <li>Audit trail has been updated</li>
                    </ul>
                </div>
            </div>
            """
            
            text_content = f"""
            Document Signed Successfully
            
            Your document has been signed:
            
            - Document: {document_data.get('title', 'Document')}
            - Signer: {document_data.get('signer_name')} ({document_data.get('signer_email')})
            - Client: {document_data.get('client_name', 'N/A')}
            - Signed On: {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}
            - Status: Completed
            
            The signed document has been processed and stored securely.
            """
            
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=self.admin_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            response = self.client.send(message)
            return response.status_code in [200, 202]
            
        except Exception as e:
            print(f"❌ Error sending admin notification: {e}")
            return False
    
    def _generate_signing_request_html(self, document_data: Dict, signing_url: str, 
                                     expiry_date: str, custom_message: Optional[str] = None) -> str:
        """Generate HTML content for signing request email"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                <h1>📝 Document Signature Required</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <p>Dear {document_data.get('signer_name', 'Valued Customer')},</p>
                
                <p>You have been requested to sign the following document:</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                    <h3 style="margin-top: 0; color: #333;">{document_data.get('title', 'Document')}</h3>
                    {f'<p><strong>Client:</strong> {document_data.get("client_name")}</p>' if document_data.get('client_name') else ''}
                    <p><strong>Requested by:</strong> {document_data.get('created_by', 'Metro Point Technology')}</p>
                    <p><strong>Expires on:</strong> {expiry_date}</p>
                </div>
                
                {f'<div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;"><p><strong>Message from sender:</strong><br>{custom_message}</p></div>' if custom_message else ''}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{signing_url}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                        ✍️ Review & Sign Document
                    </a>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h4 style="margin-top: 0; color: #856404;">🔒 Security & Legal Information</h4>
                    <ul style="color: #856404; font-size: 14px;">
                        <li>This link is secure and unique to you</li>
                        <li>Your signature will be legally binding</li>
                        <li>The document will be encrypted and stored securely</li>
                        <li>This link will expire on {expiry_date}</li>
                    </ul>
                </div>
                
                <p>If you have any questions about this document, please contact us directly.</p>
                
                <p>Best regards,<br>
                {self.from_name}<br>
                Metro Point Technology<br>
                <a href="mailto:{self.from_email}">{self.from_email}</a></p>
            </div>
            
            <div style="background: #333; color: white; padding: 15px; text-align: center; font-size: 12px;">
                This signature request was generated by MPT-CRM E-Signature system. 
                If you did not expect this email, please contact us immediately.
            </div>
        </div>
        """
    
    def _generate_signing_request_text(self, document_data: Dict, signing_url: str, 
                                     expiry_date: str, custom_message: Optional[str] = None) -> str:
        """Generate text content for signing request email"""
        text_parts = [
            f"Dear {document_data.get('signer_name', 'Valued Customer')},",
            "",
            f"You have been requested to sign the document: {document_data.get('title', 'Document')}",
            "",
            f"Requested by: {document_data.get('created_by', 'Metro Point Technology')}",
        ]
        
        if document_data.get('client_name'):
            text_parts.append(f"Client: {document_data.get('client_name')}")
        
        text_parts.extend([
            f"Expires on: {expiry_date}",
            ""
        ])
        
        if custom_message:
            text_parts.extend([
                "Message from sender:",
                custom_message,
                ""
            ])
        
        text_parts.extend([
            "Please click the following link to review and sign the document:",
            signing_url,
            "",
            "SECURITY INFORMATION:",
            "- This link is secure and unique to you",
            "- Your signature will be legally binding",
            "- The document will be encrypted and stored securely",
            f"- This link will expire on {expiry_date}",
            "",
            "If you have any questions about this document, please contact us directly.",
            "",
            f"Best regards,",
            f"{self.from_name}",
            f"Metro Point Technology",
            f"{self.from_email}"
        ])
        
        return "\n".join(text_parts)
    
    def _generate_reminder_html(self, document_data: Dict, signing_url: str) -> str:
        """Generate HTML for reminder email"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #ffc107; color: #212529; padding: 20px; text-align: center;">
                <h1>⏰ Signing Reminder</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <p>Dear {document_data.get('signer_name')},</p>
                
                <p>This is a friendly reminder that you have a document waiting for your signature:</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h3 style="margin-top: 0;">{document_data.get('title', 'Document')}</h3>
                    <p><strong>Status:</strong> Awaiting your signature</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{signing_url}" style="background: #ffc107; color: #212529; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                        ✍️ Sign Now
                    </a>
                </div>
                
                <p>Please sign at your earliest convenience to avoid expiration.</p>
                
                <p>Best regards,<br>
                {self.from_name}</p>
            </div>
        </div>
        """
    
    def _generate_reminder_text(self, document_data: Dict, signing_url: str) -> str:
        """Generate text for reminder email"""
        return f"""
        Signing Reminder
        
        Dear {document_data.get('signer_name')},
        
        This is a friendly reminder that you have a document waiting for your signature:
        
        Document: {document_data.get('title', 'Document')}
        Status: Awaiting your signature
        
        Please click the following link to sign:
        {signing_url}
        
        Please sign at your earliest convenience to avoid expiration.
        
        Best regards,
        {self.from_name}
        Metro Point Technology
        """


# Initialize global email service instance
email_service = ESignEmailService()


def send_esign_request_email(document_data: Dict, base_url: str, custom_message: Optional[str] = None) -> bool:
    """
    Convenience function to send signing request email
    
    Args:
        document_data: Document metadata from database
        base_url: Base URL for generating signing link
        custom_message: Optional custom message
    
    Returns:
        bool: True if sent successfully
    """
    signing_url = generate_signing_url(base_url, document_data.get('signing_token'))
    return email_service.send_signing_request(document_data, signing_url, custom_message)


def send_esign_completion_email(document_data: Dict, signed_pdf_path: Optional[str] = None) -> bool:
    """
    Convenience function to send completion notifications
    
    Args:
        document_data: Document metadata from database
        signed_pdf_path: Path to signed PDF for attachment
    
    Returns:
        bool: True if sent successfully
    """
    return email_service.send_completion_notification(document_data, signed_pdf_path)