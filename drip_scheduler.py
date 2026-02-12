"""
drip_scheduler.py — Background Drip Campaign Scheduler for MPT-CRM
===================================================================

Runs as a background thread inside the Streamlit app.
Checks every hour for pending drip emails and sends them via SendGrid.

Schedule: Day 0 (immediate), then Day 3, 7, 14, 21, 28, 35, 42

Usage:
    from drip_scheduler import start_scheduler
    start_scheduler()  # Call once at app startup
"""

import os
import json
import threading
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drip_scheduler")

# ============================================================
# CAMPAIGN EMAIL TEMPLATES
# ============================================================

# Updated schedule: Day 0, 3, 7, 14, 21, 28, 35, 42
NETWORKING_DRIP_EMAILS = {
    0: {
        "purpose": "thank_you",
        "subject": "Great meeting you!",
        "body": """Hi {{first_name}},

It was great meeting you today. I enjoyed our conversation and learning about what you do{{#company}} at {{company}}{{/company}}.

I'm the owner of Metro Point Technology - we build custom software, websites, and business automation tools for local businesses.

I'd love to stay connected. Feel free to reach out anytime if there's ever anything I can help with.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}"""
    },
    3: {
        "purpose": "value_add",
        "subject": "Quick resource I thought you'd find useful",
        "body": """Hi {{first_name}},

I came across something that made me think of our conversation earlier this week and wanted to share it with you.

One thing I've noticed working with local businesses is that many are leaving money on the table with manual processes. Even simple automations - like auto-sending invoices or syncing customer data between tools - can save hours each week.

Hope that's useful! Let me know if you'd like to chat more about it.

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
    },
    7: {
        "purpose": "coffee_invite",
        "subject": "Let's grab coffee",
        "body": """Hi {{first_name}},

I hope things have been going well!

I'd love to continue our conversation over coffee. Are you free sometime this week or next? I'm usually flexible in the mornings or early afternoons.

There's a great spot near downtown Cape Coral if that works for you, or I'm happy to come to you.

Let me know what works!

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
    },
    14: {
        "purpose": "check_in",
        "subject": "Quick check-in",
        "body": """Hi {{first_name}},

Just wanted to touch base and see how things are going!

It's been a couple weeks since we connected, and I wanted to keep the relationship warm. If there's anything I can help with - technology questions, introductions to people in my network, or just bouncing ideas around - don't hesitate to reach out.

Hope business is treating you well!

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
    },
    21: {
        "purpose": "expertise_share",
        "subject": "Something I've been working on",
        "body": """Hi {{first_name}},

I wanted to share a quick win we recently had with a client. They were spending 10+ hours a week on manual data entry between their CRM and accounting software. We built a simple integration that cut that down to zero.

It got me thinking about how many businesses deal with similar pain points without realizing there's a straightforward fix.

If you or anyone you know is drowning in manual processes, I'm always happy to take a quick look and share ideas - no strings attached.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}

{{unsubscribe_link}}"""
    },
    28: {
        "purpose": "reconnect",
        "subject": "Checking in - how's business?",
        "body": """Hi {{first_name}},

It's been about a month since we met, and I just wanted to check in. How have things been going{{#company}} at {{company}}{{/company}}?

I've been staying busy with some exciting projects and always enjoy catching up with the people I've connected with through networking.

If you're ever up for a quick call or coffee, I'm around!

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
    },
    35: {
        "purpose": "referral_soft",
        "subject": "Quick thought",
        "body": """Hi {{first_name}},

Quick question for you - do you know anyone who's mentioned needing help with their website, custom software, or business automation?

I'm always looking to connect with business owners who could benefit from streamlining their tech. If anyone comes to mind, I'd really appreciate an intro.

And of course, if there's anything I can do for you, just say the word!

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
    },
    42: {
        "purpose": "referral_ask",
        "subject": "One last thing",
        "body": """Hi {{first_name}},

I hope all is well! I wanted to reach out one more time with a quick ask.

I'm always looking to connect with business owners who might benefit from custom software, websites, or automation tools. If you know anyone who's mentioned struggling with:
- Outdated or clunky software
- Manual processes that eat up their time
- A website that needs updating
- Data scattered across multiple systems

I'd really appreciate an introduction. No pressure at all - just thought I'd put it out there!

And of course, if there's ever anything I can do for you, just let me know. It's been great connecting with you.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}"""
    },
}

# Lead Nurture (4 Week) — for website leads
# Schedule: Day 0, 2, 5, 10, 18, 28
LEAD_DRIP_EMAILS = {
    0: {
        "purpose": "introduction",
        "subject": "How we help local businesses save time & grow",
        "body": """Hi {{first_name}},

Thanks for your interest in Metro Point Technology! I'm Patrick Stabell, the owner — and I wanted to personally reach out.

We work with local businesses here in Cape Coral and Southwest Florida to build custom software, websites, and automation tools that actually fit how you work. No cookie-cutter solutions — everything is built around your business.

Whether it's a website that brings in leads, software that replaces a clunky spreadsheet, or automation that saves your team hours every week — that's what we do.

I'd love to learn more about{{#company}} what you're working on at {{company}} and{{/company}} where technology might be able to help.

Feel free to reply to this email or give me a call anytime.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}"""
    },
    2: {
        "purpose": "pain_point_awareness",
        "subject": "Is this eating up your time?",
        "body": """Hi {{first_name}},

Quick question — how much time does your team spend on manual processes each week?

I ask because most of the business owners I talk to here in SWFL are surprised when they add it up. Things like:

• Manually entering data into multiple systems
• Chasing invoices or following up on quotes by hand
• Updating spreadsheets that should update themselves
• Copying info from emails into your CRM or project tracker

These tasks feel small individually, but they add up to 10, 15, even 20+ hours a week. That's time you could be spending on growing your business or getting home earlier.

The good news? Most of these are straightforward to automate — and it's usually more affordable than people think.

If any of that sounds familiar, I'm happy to take a quick look at your workflow and share some ideas. No pitch, just honest perspective.

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
    },
    5: {
        "purpose": "case_study",
        "subject": "How a local business cut admin time by 60%",
        "body": """Hi {{first_name}},

I wanted to share a quick story that might resonate with you.

A service company here in Southwest Florida came to us spending 15+ hours a week on admin — manually scheduling jobs, sending invoices, and tracking customer info across three different tools.

We built them a simple custom system that:
✅ Auto-generates invoices when a job is completed
✅ Syncs their schedule, CRM, and accounting in real-time
✅ Sends automated follow-ups and review requests

The result? They cut their admin time by over 60% and freed up their team to focus on actual revenue-generating work.

Every business is different, but the pattern is the same — repetitive manual work that technology can handle for you.

If you're curious what that could look like for{{#company}} {{company}}{{/company}}{{^company}} your business{{/company}}, I'd love to chat.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}

{{unsubscribe_link}}"""
    },
    10: {
        "purpose": "consultation_offer",
        "subject": "Free 30-minute strategy call — no strings attached",
        "body": """Hi {{first_name}},

I know you're busy, so I'll keep this short.

I'd like to offer you a free 30-minute strategy call where we can:

📋 Walk through your current processes and tools
🔍 Identify the biggest time-wasters and bottlenecks
💡 Map out 2-3 specific ways technology could save you time and money

No sales pitch. No obligation. Just a straightforward conversation about where you are and what's possible.

I've done these calls with dozens of business owners in Cape Coral and Fort Myers, and the feedback is always the same — "I wish I'd done this sooner."

If you're interested, just reply to this email and we'll find a time that works.

Best,
{{your_name}}
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}"""
    },
    18: {
        "purpose": "overcome_objections",
        "subject": "The #1 concern I hear from business owners",
        "body": """Hi {{first_name}},

When I talk to business owners about custom software or automation, the most common concern I hear is:

"That sounds expensive — and I don't know if it'll actually work for my business."

Totally fair. So let me address both:

**On cost:** We're not talking about six-figure enterprise software. Most of our projects for local businesses range from a few thousand to mid five figures — and they typically pay for themselves within months through time savings and efficiency gains.

**On fit:** That's exactly why we start with a conversation, not a contract. We learn your business first, then recommend solutions that make sense. If something doesn't make sense for you, I'll tell you straight up.

We also work in phases — start small, prove the value, then expand. No big-bang projects that take a year to see results.

I genuinely just enjoy helping local businesses work smarter. If you've been thinking about it but haven't pulled the trigger, I'm here whenever you're ready.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}

{{unsubscribe_link}}"""
    },
    28: {
        "purpose": "final_push",
        "subject": "Quick offer before the month wraps up",
        "body": """Hi {{first_name}},

I wanted to reach out one last time with a quick offer.

Through the end of this month, I'm offering a **free technology assessment** for local businesses — a deeper dive than our usual strategy call. Here's what's included:

🔎 Full review of your current tools, software, and workflows
📊 A written report with prioritized recommendations
💰 Estimated ROI for the top 2-3 improvements
🗓️ An action plan you can use whether you work with us or not

There's no catch — I do these because they consistently lead to great working relationships. And even if we never work together, you'll walk away with a clear picture of where technology can help.

If you're interested, just reply and we'll get it scheduled.

Either way, I appreciate you taking the time to read my emails. If there's ever anything I can help with down the road, don't hesitate to reach out.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}"""
    },
}

# Campaign ID → email templates mapping
CAMPAIGN_EMAIL_MAP = {
    "networking-drip-6week": NETWORKING_DRIP_EMAILS,
    "lead-drip": LEAD_DRIP_EMAILS,
}


# ============================================================
# MERGE FIELD REPLACEMENT (standalone, no Streamlit dependency)
# ============================================================

def replace_merge_fields(template, contact, event_name=""):
    """Replace merge fields in email template with contact values."""
    import re

    replacements = {
        "{{first_name}}": contact.get("first_name", ""),
        "{{last_name}}": contact.get("last_name", ""),
        "{{company}}": contact.get("company", ""),
        "{{company_name}}": contact.get("company", ""),
        "{{email}}": contact.get("email", ""),
        "{{phone}}": contact.get("phone", ""),
        "{{title}}": contact.get("title", ""),
        "{{event_name}}": event_name or contact.get("source_detail", ""),
        "{{your_name}}": os.getenv("SENDGRID_FROM_NAME", "Patrick Stabell"),
        "{{your_phone}}": "(239) 600-8159",
        "{{your_email}}": os.getenv("SENDGRID_FROM_EMAIL", "patrick@metropointtechnology.com"),
        "{{your_website}}": "www.MetroPointTechnology.com",
        "{{unsubscribe_link}}": "[Unsubscribe](mailto:patrick@metropointtechnology.com?subject=Unsubscribe)",
    }

    result = template
    for field, value in replacements.items():
        result = result.replace(field, value or "")

    # Handle conditional blocks like {{#company}}...{{/company}}
    conditional_pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'

    def replace_conditional(match):
        field_name = match.group(1)
        content = match.group(2)
        value = replacements.get(f"{{{{{field_name}}}}}", "")
        return content if value else ""

    result = re.sub(conditional_pattern, replace_conditional, result, flags=re.DOTALL)

    return result


# ============================================================
# SENDGRID SEND (standalone, no Streamlit dependency)
# ============================================================

def send_drip_email(to_email, to_name, subject, html_body, contact_id=None):
    """Send an email via SendGrid. Returns dict with success status."""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, TrackingSettings, ClickTracking, OpenTracking
    except ImportError:
        return {"success": False, "error": "sendgrid package not installed"}

    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "patrick@metropointtechnology.com")
    from_name = os.getenv("SENDGRID_FROM_NAME", "Patrick Stabell")

    if not api_key:
        return {"success": False, "error": "SENDGRID_API_KEY not configured"}

    try:
        message = Mail(
            from_email=(from_email, from_name),
            to_emails=(to_email, to_name),
            subject=subject,
            html_content=html_body.replace("\n", "<br>")
        )

        tracking_settings = TrackingSettings()
        tracking_settings.click_tracking = ClickTracking(True, True)
        tracking_settings.open_tracking = OpenTracking(True)
        message.tracking_settings = tracking_settings

        sg = SendGridAPIClient(api_key)
        response = sg.send(message)

        return {
            "success": True,
            "message_id": response.headers.get("X-Message-Id", ""),
            "status_code": response.status_code
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# SCHEDULER CORE
# ============================================================

_scheduler_thread = None
_scheduler_running = False
CHECK_INTERVAL_SECONDS = 3600  # Check every hour


def process_pending_drip_emails():
    """Check all active enrollments and send any emails that are due.

    This is the core scheduler function. It:
    1. Gets all active enrollments
    2. For each, checks the step_schedule for emails due today or earlier
    3. Sends the email via SendGrid
    4. Updates the enrollment record
    """
    from db_service import (
        db_get_active_enrollments,
        db_update_enrollment,
        db_complete_enrollment,
        db_record_email_send,
        db_log_activity,
    )

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    logger.info("[Drip Scheduler] Checking for pending drip emails...")

    enrollments = db_get_active_enrollments()
    if not enrollments:
        logger.info("[Drip Scheduler] No active enrollments found.")
        return 0

    now = datetime.now()
    emails_sent = 0

    for enrollment in enrollments:
        try:
            contact = enrollment.get("contacts", {})
            if not contact:
                logger.warning(f"[Drip Scheduler] Enrollment {enrollment['id']} has no contact data, skipping.")
                continue

            # Skip contacts with no email or unsubscribed/bounced status
            email_addr = contact.get("email", "")
            email_status = contact.get("email_status", "active")
            if not email_addr or email_status in ("unsubscribed", "bounced"):
                logger.info(f"[Drip Scheduler] Skipping {contact.get('first_name', '?')} - no email or {email_status}")
                continue

            # Parse the step schedule
            schedule_raw = enrollment.get("step_schedule", "[]")
            if isinstance(schedule_raw, str):
                schedule = json.loads(schedule_raw)
            else:
                schedule = schedule_raw

            current_step = enrollment.get("current_step", 0)
            total_steps = enrollment.get("total_steps", len(schedule))
            campaign_id = enrollment.get("campaign_id", "")

            # Find the next step that hasn't been sent yet
            for step_idx, step in enumerate(schedule):
                if step.get("sent_at"):
                    continue  # Already sent

                # Check if this step is due
                scheduled_for = step.get("scheduled_for", "")
                if not scheduled_for:
                    continue

                try:
                    scheduled_date = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
                    # Remove timezone info for comparison (we work in local time)
                    if scheduled_date.tzinfo:
                        scheduled_date = scheduled_date.replace(tzinfo=None)
                except (ValueError, TypeError):
                    logger.warning(f"[Drip Scheduler] Invalid date: {scheduled_for}")
                    continue

                if scheduled_date > now:
                    # Not due yet — skip remaining steps (they're in order)
                    break

                # This step is due! Get the email template based on campaign
                day_number = step.get("day", 0)
                campaign_emails = CAMPAIGN_EMAIL_MAP.get(campaign_id, NETWORKING_DRIP_EMAILS)
                email_template = campaign_emails.get(day_number)

                if not email_template:
                    logger.warning(f"[Drip Scheduler] No template for day {day_number}")
                    step["sent_at"] = now.isoformat()
                    step["skipped"] = True
                    continue

                # Skip Day 0 — that's sent immediately at import time
                if day_number == 0:
                    step["sent_at"] = enrollment.get("created_at", now.isoformat())
                    continue

                # Prepare and send the email
                event_name = enrollment.get("source_detail", "")
                subject = replace_merge_fields(email_template["subject"], contact, event_name)
                body = replace_merge_fields(email_template["body"], contact, event_name)
                to_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()

                logger.info(f"[Drip Scheduler] Sending Day {day_number} email to {email_addr} ({to_name})")

                result = send_drip_email(
                    to_email=email_addr,
                    to_name=to_name,
                    subject=subject,
                    html_body=body,
                    contact_id=contact.get("id")
                )

                if result.get("success"):
                    # Mark step as sent
                    step["sent_at"] = now.isoformat()
                    step["message_id"] = result.get("message_id", "")
                    emails_sent += 1

                    # Record in email_sends table
                    db_record_email_send(
                        contact_id=contact["id"],
                        subject=subject,
                        sendgrid_message_id=result.get("message_id"),
                        enrollment_id=enrollment["id"]
                    )

                    # Log activity
                    db_log_activity(
                        "email_sent",
                        f"Drip email Day {day_number} ({email_template['purpose']}): {subject}",
                        contact["id"]
                    )

                    logger.info(f"[Drip Scheduler] Sent Day {day_number} to {email_addr}")
                else:
                    logger.error(f"[Drip Scheduler] Failed Day {day_number} to {email_addr}: {result.get('error')}")
                    step["error"] = result.get("error", "Unknown error")

                # Only send one email per enrollment per check cycle
                break

            # Update the enrollment with new schedule and step count
            sent_count = sum(1 for s in schedule if s.get("sent_at") and not s.get("skipped"))
            update_data = {
                "step_schedule": json.dumps(schedule),
                "emails_sent": sent_count,
                "current_step": sent_count,
                "last_email_sent_at": now.isoformat(),
            }

            # Calculate next email date
            next_steps = [s for s in schedule if not s.get("sent_at")]
            if next_steps:
                update_data["next_email_scheduled"] = next_steps[0].get("scheduled_for")
            else:
                # All steps sent — mark as completed
                update_data["status"] = "completed"

            db_update_enrollment(enrollment["id"], update_data)

            # If completed, also mark via the complete function
            if update_data.get("status") == "completed":
                db_log_activity(
                    "campaign_completed",
                    f"Completed drip campaign: {enrollment.get('campaign_name', 'Unknown')}",
                    contact["id"]
                )

        except Exception as e:
            logger.error(f"[Drip Scheduler] Error processing enrollment {enrollment.get('id', '?')}: {e}")
            continue

    logger.info(f"[Drip Scheduler] Done. Sent {emails_sent} email(s).")
    return emails_sent


def _scheduler_loop():
    """Background thread loop: checks for pending emails every CHECK_INTERVAL_SECONDS."""
    global _scheduler_running
    logger.info("[Drip Scheduler] Background thread started.")

    while _scheduler_running:
        try:
            process_pending_drip_emails()
        except Exception as e:
            logger.error(f"[Drip Scheduler] Error in scheduler loop: {e}")

        # Sleep in small increments so we can stop quickly
        for _ in range(CHECK_INTERVAL_SECONDS):
            if not _scheduler_running:
                break
            time.sleep(1)

    logger.info("[Drip Scheduler] Background thread stopped.")


def start_scheduler():
    """Start the drip campaign scheduler as a background daemon thread.

    Safe to call multiple times — will only start one thread.
    The thread is a daemon, so it dies when the main process exits.
    """
    global _scheduler_thread, _scheduler_running

    if _scheduler_running and _scheduler_thread and _scheduler_thread.is_alive():
        logger.info("[Drip Scheduler] Already running.")
        return

    _scheduler_running = True
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True, name="drip-scheduler")
    _scheduler_thread.start()
    logger.info("[Drip Scheduler] Started background scheduler (checking every hour).")


def stop_scheduler():
    """Stop the drip campaign scheduler."""
    global _scheduler_running
    _scheduler_running = False
    logger.info("[Drip Scheduler] Stop requested.")


def is_scheduler_running():
    """Check if the scheduler is currently running."""
    global _scheduler_thread, _scheduler_running
    return _scheduler_running and _scheduler_thread is not None and _scheduler_thread.is_alive()
