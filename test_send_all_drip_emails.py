"""
Test script to send all drip campaign emails to Jack@Metropointtech.com
Run one campaign at a time and verify receipt
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import time

# Test recipient
TEST_EMAIL = "Jack@Metropointtech.com"

# Merge field values for test
MERGE_DATA = {
    "first_name": "Jack",
    "last_name": "MetroBot",
    "company": "Test Company Inc",  # Set to "" to test without company
    "your_name": "Patrick Stabell",
    "your_phone": "(239) 426-7058",
    "your_email": "patrick@metropointtechnology.com",
    "your_website": "https://metropointtech.com",
    "unsubscribe_link": "[Unsubscribe Link]",
}

import re

def apply_merge_fields(text, data):
    """Replace merge fields with actual values, handling Mustache-style conditionals"""
    result = text
    
    # Handle positive conditionals: {{#field}}content{{/field}} - show if field exists and is truthy
    def replace_positive(match):
        field = match.group(1)
        content = match.group(2)
        if data.get(field):
            return content
        return ""
    result = re.sub(r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}', replace_positive, result, flags=re.DOTALL)
    
    # Handle negative conditionals: {{^field}}content{{/field}} - show if field is empty/missing
    def replace_negative(match):
        field = match.group(1)
        content = match.group(2)
        if not data.get(field):
            return content
        return ""
    result = re.sub(r'\{\{\^(\w+)\}\}(.*?)\{\{/\1\}\}', replace_negative, result, flags=re.DOTALL)
    
    # Replace simple merge fields: {{field}}
    for field, value in data.items():
        result = result.replace(f"{{{{{field}}}}}", str(value))
    
    return result

def send_test_email(subject, body, campaign_name, email_num, total_emails):
    """Send a test email via SendGrid"""
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    
    # Apply merge fields
    final_subject = f"[TEST {email_num}/{total_emails}] {apply_merge_fields(subject, MERGE_DATA)}"
    final_body = apply_merge_fields(body, MERGE_DATA)
    
    # Add campaign info header
    final_body = f"--- CAMPAIGN: {campaign_name} | EMAIL {email_num} of {total_emails} ---\n\n{final_body}"
    
    message = Mail(
        from_email=Email(os.getenv('SENDGRID_FROM_EMAIL'), os.getenv('SENDGRID_FROM_NAME')),
        to_emails=To(TEST_EMAIL),
        subject=final_subject,
        plain_text_content=Content("text/plain", final_body)
    )
    
    try:
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

# Import campaign templates
from drip_scheduler import (
    NETWORKING_DRIP_EMAILS,
    LEAD_DRIP_EMAILS,
    PROSPECT_DRIP_EMAILS,
    CLIENT_DRIP_EMAILS
)

CAMPAIGNS = {
    "NETWORKING": NETWORKING_DRIP_EMAILS,
    "LEAD": LEAD_DRIP_EMAILS,
    "PROSPECT": PROSPECT_DRIP_EMAILS,
    "CLIENT": CLIENT_DRIP_EMAILS,
}

def test_campaign(campaign_name):
    """Send all emails from a campaign"""
    if campaign_name not in CAMPAIGNS:
        print(f"Unknown campaign: {campaign_name}")
        print(f"Available: {list(CAMPAIGNS.keys())}")
        return
    
    emails = CAMPAIGNS[campaign_name]
    total = len(emails)
    
    print(f"\n{'='*60}")
    print(f"TESTING CAMPAIGN: {campaign_name} ({total} emails)")
    print(f"Sending to: {TEST_EMAIL}")
    print(f"{'='*60}\n")
    
    success_count = 0
    for idx, (day, email_data) in enumerate(sorted(emails.items()), 1):
        subject = email_data["subject"]
        body = email_data["body"]
        purpose = email_data.get("purpose", "unknown")
        
        print(f"[{idx}/{total}] Day {day} - {purpose}: {subject[:40]}...", end=" ")
        
        if send_test_email(subject, body, campaign_name, idx, total):
            print("[OK] SENT")
            success_count += 1
        else:
            print("[FAIL]")
        
        # Small delay between sends
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {success_count}/{total} emails sent successfully")
    print(f"{'='*60}\n")
    
    return success_count == total

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_send_all_drip_emails.py <CAMPAIGN_NAME>")
        print(f"Available campaigns: {list(CAMPAIGNS.keys())}")
        sys.exit(1)
    
    campaign = sys.argv[1].upper()
    test_campaign(campaign)
