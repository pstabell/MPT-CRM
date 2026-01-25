"""
SendGrid Email Service for MPT-CRM
Handles email sending, tracking, and template merging
"""

import os
import re
from typing import Optional, Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import sendgrid, handle if not installed
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, TrackingSettings, ClickTracking, OpenTracking
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False


class EmailService:
    """SendGrid email service wrapper for MPT-CRM"""

    def __init__(self):
        self.client = None
        self._configured = False

        if SENDGRID_AVAILABLE:
            api_key = os.getenv("SENDGRID_API_KEY")
            if api_key:
                try:
                    self.client = SendGridAPIClient(api_key)
                    self._configured = True
                except Exception as e:
                    print(f"Failed to initialize SendGrid: {e}")

        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "patrick@metropointtechnology.com")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "Patrick Stabell")

    @property
    def is_configured(self) -> bool:
        return self._configured and self.client is not None

    def merge_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        Replace merge fields in template with actual data

        Supports:
        - {{field_name}} - Standard merge fields
        - {{first_name}} - Contact first name
        - {{company_name}} - Company name
        etc.
        """
        result = template

        # Replace all {{field}} patterns
        for key, value in data.items():
            pattern = r'\{\{' + re.escape(key) + r'\}\}'
            result = re.sub(pattern, str(value) if value else '', result, flags=re.IGNORECASE)

        # Remove any remaining unmatched merge fields
        result = re.sub(r'\{\{[^}]+\}\}', '', result)

        return result

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        track_opens: bool = True,
        track_clicks: bool = True
    ) -> Dict[str, Any]:
        """
        Send a single email via SendGrid

        Returns:
            Dict with 'success', 'message_id', and 'error' keys
        """
        if not self.is_configured:
            return {
                "success": False,
                "message_id": None,
                "error": "SendGrid not configured. Check API key."
            }

        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email, to_name),
                subject=subject,
                html_content=html_content
            )

            if plain_content:
                message.add_content(Content("text/plain", plain_content))

            # Enable tracking
            tracking = TrackingSettings()
            tracking.click_tracking = ClickTracking(track_clicks, track_clicks)
            tracking.open_tracking = OpenTracking(track_opens)
            message.tracking_settings = tracking

            response = self.client.send(message)

            # Extract message ID from headers
            message_id = response.headers.get('X-Message-Id', '')

            return {
                "success": response.status_code in [200, 201, 202],
                "message_id": message_id,
                "status_code": response.status_code,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "message_id": None,
                "error": str(e)
            }

    def send_template_email(
        self,
        to_email: str,
        to_name: str,
        template_subject: str,
        template_body: str,
        merge_data: Dict[str, Any],
        track_opens: bool = True,
        track_clicks: bool = True
    ) -> Dict[str, Any]:
        """
        Send an email using a template with merge fields

        Args:
            to_email: Recipient email
            to_name: Recipient name
            template_subject: Subject with {{merge_fields}}
            template_body: Body with {{merge_fields}}
            merge_data: Dictionary of merge field values
        """
        # Add default merge data
        default_data = {
            "your_phone": "(239) 600-8159",
            "your_email": self.from_email,
            "your_website": "www.MetroPointTechnology.com",
            "unsubscribe_link": f"[Unsubscribe](mailto:{self.from_email}?subject=Unsubscribe)"
        }
        default_data.update(merge_data)

        # Merge templates
        subject = self.merge_template(template_subject, default_data)
        body = self.merge_template(template_body, default_data)

        # Convert plain text to simple HTML
        html_body = self._text_to_html(body)

        return self.send_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_body,
            plain_content=body,
            track_opens=track_opens,
            track_clicks=track_clicks
        )

    def send_bulk_emails(
        self,
        recipients: List[Dict[str, Any]],
        template_subject: str,
        template_body: str,
        common_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Send emails to multiple recipients

        Args:
            recipients: List of dicts with 'email', 'name', and any merge fields
            template_subject: Subject template
            template_body: Body template
            common_data: Merge data common to all recipients

        Returns:
            List of send results
        """
        results = []
        common = common_data or {}

        for recipient in recipients:
            merge_data = {**common, **recipient}
            result = self.send_template_email(
                to_email=recipient.get('email', ''),
                to_name=recipient.get('name', recipient.get('first_name', '')),
                template_subject=template_subject,
                template_body=template_body,
                merge_data=merge_data
            )
            result['recipient'] = recipient.get('email')
            results.append(result)

        return results

    def _text_to_html(self, text: str) -> str:
        """Convert plain text to simple HTML"""
        # Escape HTML entities
        import html
        text = html.escape(text)

        # Convert line breaks
        text = text.replace('\n\n', '</p><p>')
        text = text.replace('\n', '<br>')

        # Wrap in paragraph tags
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                p {{ margin: 0 0 1em 0; }}
            </style>
        </head>
        <body>
            <p>{text}</p>
        </body>
        </html>
        """

        return html_content

    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


# Singleton instance
email_service = EmailService()
