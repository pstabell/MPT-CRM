"""
MPT-CRM Marketing Page
Drip campaigns, email templates, SendGrid integration, and Business Card Scanner

Database operations are handled by db_service.py - the single source of truth.
"""

import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO
import base64
import json
import os
import re

# Load environment variables from .env file (do not override existing env vars)
from dotenv import load_dotenv
load_dotenv(override=False)

from db_service import (
    db_is_connected,
    db_create_contact, db_check_contact_exists, db_check_contacts_by_company,
    db_find_potential_duplicates_by_card, db_update_contact,
    upload_card_image_to_supabase, db_create_enrollment, db_log_activity,
    db_get_unprocessed_cards, db_list_card_images, db_get_card_image_url,
    db_delete_contact, db_update_enrollment, send_email_via_sendgrid,
)
from sso_auth import require_sso_auth, render_auth_status

def enroll_in_campaign(contact_id, event_name="", contact_type="networking"):
    """Enroll contact in the appropriate drip campaign based on contact type.

    Args:
        contact_id: The contact's database ID
        event_name: Source event name for tracking
        contact_type: Contact type to determine campaign (networking, lead, prospect, client, former_client, partner)
    """
    try:
        # Import CAMPAIGNS lazily (defined later in file) - fall back to networking
        campaign = CAMPAIGNS.get(contact_type, NETWORKING_DRIP_CAMPAIGN)

        schedule = []
        for i, email in enumerate(campaign["emails"]):
            scheduled_date = datetime.now() + timedelta(days=email["day"])
            schedule.append({
                "step": i,
                "day": email["day"],
                "purpose": email["purpose"],
                "subject": email["subject"],
                "scheduled_for": scheduled_date.isoformat(),
                "sent_at": None
            })

        enrollment_data = {
            "contact_id": contact_id,
            "campaign_id": campaign["campaign_id"],
            "campaign_name": campaign["campaign_name"],
            "status": "active",
            "current_step": 0,
            "total_steps": len(campaign["emails"]),
            "step_schedule": json.dumps(schedule),
            "source": "mobile_scanner",
            "source_detail": event_name,
            "emails_sent": 0,
            "next_email_scheduled": schedule[0]["scheduled_for"] if schedule else None
        }

        return db_create_enrollment(enrollment_data)

    except Exception as e:
        print(f"Error enrolling in campaign: {e}")
        return None

# ============================================
# PDF TO IMAGE CONVERSION
# ============================================

def convert_pdf_to_images(pdf_bytes):
    """
    Convert PDF pages to images using pypdfium2.
    Returns list of dicts with image_bytes, page_number, type.
    """
    try:
        import pypdfium2 as pdfium
        from PIL import Image
    except ImportError:
        return [{"error": "pypdfium2 or Pillow not installed. Run: pip install pypdfium2 Pillow"}]

    images = []
    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            # Render at 300 DPI for good OCR quality (scale = 300/72 ~ 4.17)
            bitmap = page.render(scale=4)
            pil_image = bitmap.to_pil()

            # Convert to PNG bytes
            img_buffer = BytesIO()
            pil_image.save(img_buffer, format="PNG")
            img_bytes = img_buffer.getvalue()

            images.append({
                "image_bytes": img_bytes,
                "page_number": page_num + 1,
                "type": "image/png"
            })
        pdf.close()
        return images
    except Exception as e:
        return [{"error": str(e)}]

# ============================================
# MULTI-CARD DETECTION & CROPPING
# ============================================

def detect_cards_on_page(image_bytes, image_type="image/png"):
    """
    Use Claude Vision to detect multiple business cards on a scanned page.
    Returns list of bounding boxes as percentages: [{"x": 0-100, "y": 0-100, "width": 0-100, "height": 0-100}, ...]
    """
    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic package not installed"}

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not configured"}

    # Debug: Show key length (not the actual key for security)
    print(f"[Card Detection] API key loaded: {len(api_key)} characters, starts with: {api_key[:15]}...")

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    detection_prompt = """This is a scanned page that may contain MULTIPLE business cards arranged in a grid.

Your task: Find and locate EVERY individual business card on this page.

For each business card, provide its bounding box as PERCENTAGES (0-100) of the total image dimensions.

Return a JSON object:
{
    "card_count": total number of individual cards found,
    "cards": [
        {
            "x": left edge percentage (0-100),
            "y": top edge percentage (0-100),
            "width": card width as percentage (0-100),
            "height": card height as percentage (0-100)
        }
    ]
}

CRITICAL RULES:
1. Count EVERY individual business card - there may be 6, 8, 10, or more cards on the page
2. Standard business cards are 3.5" x 2" - on 8.5"x11" paper, expect ~4 cards per row, ~5 rows
3. Each card should have width ~35-45% and height ~15-20% of the page
4. Scan the ENTIRE page systematically: top-left to top-right, then next row, etc.
5. Include 2-3% padding around each card boundary
6. Cards may be in portrait OR landscape orientation
7. Return ONLY the JSON object, no other text

Example for a page with 8 cards in 2 columns x 4 rows:
{"card_count": 8, "cards": [{"x": 5, "y": 5, "width": 40, "height": 18}, {"x": 55, "y": 5, "width": 40, "height": 18}, ...]}"""

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=60.0)  # 60 second timeout
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_type,
                                "data": image_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": detection_prompt
                        }
                    ]
                }
            ]
        )

        result_text = response.content[0].text

        # Handle markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        return json.loads(result_text.strip())
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse detection response: {e}", "card_count": 0, "cards": []}
    except Exception as e:
        return {"error": str(e), "card_count": 0, "cards": []}


def crop_card_from_image(image_bytes, bbox):
    """
    Crop a single card from an image using bounding box percentages.
    bbox: {"x": 0-100, "y": 0-100, "width": 0-100, "height": 0-100}
    Returns cropped image as PNG bytes.
    """
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        # Load image from bytes
        img = Image.open(BytesIO(image_bytes))
        img_width, img_height = img.size

        # Convert percentages to pixels
        x = int((bbox.get("x", 0) / 100) * img_width)
        y = int((bbox.get("y", 0) / 100) * img_height)
        width = int((bbox.get("width", 100) / 100) * img_width)
        height = int((bbox.get("height", 100) / 100) * img_height)

        # Ensure bounds are within image
        x = max(0, min(x, img_width))
        y = max(0, min(y, img_height))
        right = max(0, min(x + width, img_width))
        bottom = max(0, min(y + height, img_height))

        # Crop the card
        cropped = img.crop((x, y, right, bottom))

        # Convert back to PNG bytes
        output = BytesIO()
        cropped.save(output, format="PNG")
        return output.getvalue()
    except Exception as e:
        print(f"Error cropping card: {e}")
        return None


def grid_crop_cards(image_bytes, card_count):
    """
    Fallback: Crop cards using a simple grid pattern when AI detection fails.
    Assumes cards are arranged in a regular grid on the page.
    """
    try:
        from PIL import Image
        img = Image.open(BytesIO(image_bytes))
        img_width, img_height = img.size

        # Determine grid layout based on card count
        # Most business card scanners use 3 columns Ã- 4 rows (12 positions)
        # Common layouts:
        layouts = {
            6: (2, 3),   # 2 cols Ã- 3 rows
            8: (2, 4),   # 2 cols Ã- 4 rows
            9: (3, 4),   # 3 cols Ã- 4 rows (scanner with 12 positions, 9 filled)
            10: (2, 5),  # 2 cols Ã- 5 rows
            12: (3, 4),  # 3 cols Ã- 4 rows (full scanner)
            15: (3, 5),  # 3 cols Ã- 5 rows
            16: (4, 4),  # 4 cols Ã- 4 rows
            18: (3, 6),  # 3 cols Ã- 6 rows
            20: (4, 5)   # 4 cols Ã- 5 rows
        }

        if card_count in layouts:
            cols, rows = layouts[card_count]
        else:
            # Default: assume 3-column scanner layout
            cols = 3
            rows = (card_count + cols - 1) // cols

        # Calculate cell dimensions with minimal margins
        # Tightly packed cards need very small margins
        margin_x = int(img_width * 0.01)  # 1% outer margin
        margin_y = int(img_height * 0.01)

        usable_width = img_width - (2 * margin_x)
        usable_height = img_height - (2 * margin_y)

        cell_width = usable_width // cols
        cell_height = usable_height // rows

        # Very small inset to avoid bleeding into adjacent cards
        # Reduced from 8% to 2% to capture full cards
        inset_x = int(cell_width * 0.02)  # 2% inset from each side
        inset_y = int(cell_height * 0.02)  # 2% inset from top/bottom

        print(f"[Grid Crop] Image: {img_width}x{img_height}, Grid: {cols}x{rows}, Cell: {cell_width}x{cell_height}, Inset: {inset_x}x{inset_y}")

        # Crop each card
        cropped_cards = []
        for row in range(rows):
            for col in range(cols):
                if len(cropped_cards) >= card_count:
                    break

                # Calculate boundaries with insets to avoid adjacent cards
                x = margin_x + (col * cell_width) + inset_x
                y = margin_y + (row * cell_height) + inset_y
                right = margin_x + ((col + 1) * cell_width) - inset_x
                bottom = margin_y + ((row + 1) * cell_height) - inset_y

                print(f"[Grid Crop] Card {len(cropped_cards)+1} (row={row}, col={col}): x={x}, y={y}, right={right}, bottom={bottom}")

                # Ensure bounds are valid
                x = max(0, min(x, img_width))
                y = max(0, min(y, img_height))
                right = max(0, min(right, img_width))
                bottom = max(0, min(bottom, img_height))

                if right > x and bottom > y:
                    cropped = img.crop((x, y, right, bottom))
                    output = BytesIO()
                    cropped.save(output, format="PNG")
                    cropped_cards.append(output.getvalue())

            if len(cropped_cards) >= card_count:
                break

        img.close()
        return cropped_cards if cropped_cards else [image_bytes]
    except Exception as e:
        print(f"[Grid Crop] Error: {e}")
        return [image_bytes]


def process_page_for_cards(image_bytes, image_type="image/png", expected_count=0):
    """
    Process a scanned page to detect and crop individual business cards.
    Returns list of cropped card images as bytes.
    """
    # If user specified expected count > 1, try AI detection first
    if expected_count > 1:
        print(f"[Card Processing] User specified {expected_count} cards - trying AI detection first")
        detection_result = detect_cards_on_page(image_bytes, image_type)
        ai_card_count = detection_result.get("card_count", 0)

        print(f"[Card Processing] AI detected {ai_card_count} cards (expected {expected_count})")

        # Use AI detection results if we got any cards
        cards = detection_result.get("cards", [])
        if cards and ai_card_count > 0:
            cropped_cards = []
            for i, bbox in enumerate(cards):
                if bbox.get("width", 0) > 5 and bbox.get("height", 0) > 5:
                    cropped = crop_card_from_image(image_bytes, bbox)
                    if cropped:
                        cropped_cards.append(cropped)

            if len(cropped_cards) > 0:
                print(f"[Card Processing] AI detection successful: {len(cropped_cards)} cards (expected {expected_count})")
                return cropped_cards

        # Only fall back to grid if AI completely failed
        print(f"[Card Processing] AI detection found {ai_card_count} cards, falling back to grid cropping")
        return grid_crop_cards(image_bytes, expected_count)

    # Check image dimensions to see if this looks like a multi-card scan
    try:
        from PIL import Image
        img = Image.open(BytesIO(image_bytes))
        img_width, img_height = img.size
        # Standard letter page at 300 DPI is roughly 2550x3300 pixels
        # If image is large (like a scanned page), it likely has multiple cards
        is_likely_multicard = img_width > 1500 or img_height > 1500
        img.close()
    except Exception:
        is_likely_multicard = True  # Assume it could be multi-card

    if not is_likely_multicard:
        # Small image is probably a single card photo
        return [image_bytes]

    # Try AI detection first
    detection_result = detect_cards_on_page(image_bytes, image_type)

    if "error" in detection_result and detection_result.get("card_count", 0) == 0:
        # Detection failed, return the whole image as a single card
        print("[Card Detection] AI detection failed")
        return [image_bytes]

    card_count = detection_result.get("card_count", 0)
    cards = detection_result.get("cards", [])

    print(f"[Card Detection] AI found {card_count} cards with bounding boxes: {cards}")

    if card_count <= 1 or not cards:
        # Single card detected, return the whole image
        print("[Card Detection] Only 1 card detected, returning full image")
        return [image_bytes]

    # Crop each detected card
    cropped_cards = []
    for i, bbox in enumerate(cards):
        # Validate bounding box has reasonable dimensions
        if bbox.get("width", 0) > 5 and bbox.get("height", 0) > 5:
            cropped = crop_card_from_image(image_bytes, bbox)
            if cropped:
                print(f"[Card Detection] Successfully cropped card {i+1}")
                cropped_cards.append(cropped)

    # If cropping failed for all cards, return original
    if not cropped_cards:
        print("[Card Detection] Cropping failed, returning original image")
        return [image_bytes]

    return cropped_cards


# ============================================
# CLAUDE VISION API FOR CARD EXTRACTION
# ============================================

def extract_contact_from_business_card(image_bytes, image_type="image/png"):
    """
    Use Claude Vision API to extract contact info from a business card image.
    Returns dict with first_name, last_name, company, email, phone, title, confidence, raw_text.
    """
    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic package not installed. Run: pip install anthropic"}

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not configured in environment variables"}

    # Debug: Show key info
    print(f"[Contact Extraction] API key loaded: {len(api_key)} characters, starts with: {api_key[:15]}...")

    # Optimize image size to avoid timeouts
    try:
        from PIL import Image
        img = Image.open(BytesIO(image_bytes))

        # Resize if image is very large (max 1600px on longest side)
        max_size = 1600
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            print(f"[Contact Extraction] Resized image from {img.size} to {new_size}")

        # Convert to JPEG with quality 85 to reduce size
        output = BytesIO()
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        img.save(output, format="JPEG", quality=85, optimize=True)
        image_bytes = output.getvalue()
        image_type = "image/jpeg"
        print(f"[Contact Extraction] Optimized image size: {len(image_bytes)} bytes")
    except Exception as e:
        print(f"[Contact Extraction] Image optimization failed: {e}, using original")

    # Encode image to base64
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    extraction_prompt = """Analyze this business card image and extract the contact information.

Return a JSON object with these fields (use null for any field not found):
{
    "first_name": "extracted first name",
    "last_name": "extracted last name",
    "company": "company/organization name",
    "email": "email address",
    "phone": "phone number (preserve formatting)",
    "title": "job title/position",
    "website": "website URL if present",
    "address": "physical address if present",
    "confidence": 0.0 to 1.0 rating of extraction confidence,
    "raw_text": "all text visible on the card"
}

Important:
- Extract the primary contact's name, not company name as the person's name
- If multiple phone numbers, prefer mobile/cell
- If multiple emails, prefer personal over generic (info@, contact@)
- Clean up any OCR artifacts in the text
- Return ONLY the JSON object, no other text"""

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=60.0)  # 60 second timeout
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_type,
                                "data": image_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": extraction_prompt
                        }
                    ]
                }
            ]
        )

        result_text = response.content[0].text

        # Handle markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        return json.loads(result_text.strip())
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response: {e}", "raw_text": result_text if 'result_text' in dir() else ""}
    except Exception as e:
        return {"error": str(e)}

def extract_contact_from_card(image_url):
    """
    Wrapper function that accepts an image URL and extracts contact info.
    Fetches the image from the URL and calls the main extraction function.
    """
    import requests
    try:
        # Fetch image from URL
        response = requests.get(image_url, timeout=10)
        if response.status_code != 200:
            return {"error": f"Failed to fetch image: HTTP {response.status_code}"}

        image_bytes = response.content

        # Detect content type
        content_type = response.headers.get('Content-Type', 'image/jpeg')

        # Call main extraction function
        return extract_contact_from_business_card(image_bytes, content_type)

    except Exception as e:
        return {"error": f"Failed to fetch image: {str(e)}"}

# ============================================
# MERGE FIELD REPLACEMENT
# ============================================

def replace_merge_fields(template, contact, event_name=""):
    """
    Replace merge fields in email template with actual values.
    Supports: {{first_name}}, {{last_name}}, {{company}}, {{event_name}}, {{your_name}}, etc.
    """
    # Get settings from session state or use defaults
    settings = st.session_state.get('settings_data', {})

    replacements = {
        "{{first_name}}": contact.get("first_name", ""),
        "{{last_name}}": contact.get("last_name", ""),
        "{{company}}": contact.get("company", ""),
        "{{company_name}}": contact.get("company", ""),
        "{{email}}": contact.get("email", ""),
        "{{phone}}": contact.get("phone", ""),
        "{{title}}": contact.get("title", ""),
        "{{event_name}}": event_name or contact.get("source_detail", ""),
        "{{your_name}}": settings.get("owner_name", "Patrick Stabell"),
        "{{your_phone}}": settings.get("phone", "(239) 600-8159"),
        "{{your_email}}": settings.get("email", "patrick@metropointtechnology.com"),
        "{{your_website}}": settings.get("website", "www.MetroPointTechnology.com"),
        "{{unsubscribe_link}}": "[Unsubscribe](mailto:patrick@metropointtechnology.com?subject=Unsubscribe)",
    }

    result = template
    for field, value in replacements.items():
        result = result.replace(field, value or "")

    # Handle conditional blocks like {{#event_name}}...{{/event_name}}
    conditional_pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'

    def replace_conditional(match):
        field_name = match.group(1)
        content = match.group(2)
        value = replacements.get(f"{{{{{field_name}}}}}", "")
        return content if value else ""

    result = re.sub(conditional_pattern, replace_conditional, result, flags=re.DOTALL)

    return result

# ============================================
# 6-WEEK NETWORKING DRIP CAMPAIGN TEMPLATES
# ============================================

NETWORKING_DRIP_CAMPAIGN = {
    "campaign_id": "networking-drip-6week",
    "campaign_name": "Networking Follow-Up (6 Week)",
    "emails": [
        {
            "day": 0,
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
        {
            "day": 3,
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
        {
            "day": 7,
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
        {
            "day": 14,
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
        {
            "day": 21,
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
        {
            "day": 28,
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
        {
            "day": 35,
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
        {
            "day": 42,
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
        }
    ]
}

# ============================================
# LEAD NURTURE DRIP CAMPAIGN (4 WEEK)
# ============================================

LEAD_DRIP_CAMPAIGN = {
    "campaign_id": "lead-drip",
    "campaign_name": "Lead Nurture (4 Week)",
    "emails": [
        {
            "day": 0,
            "purpose": "introduction",
            "subject": "How we help local businesses save time & grow",
            "body": """Hi {{first_name}},

Thanks for your interest in Metro Point Technology! I'm Patrick Stabell, the owner - and I wanted to personally reach out.

We work with local businesses here in Cape Coral and Southwest Florida to build custom software, websites, and automation tools that actually fit how you work. No cookie-cutter solutions - everything is built around your business.

Whether it's a website that brings in leads, software that replaces a clunky spreadsheet, or automation that saves your team hours every week - that's what we do.

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
        {
            "day": 2,
            "purpose": "pain_point_awareness",
            "subject": "Is this eating up your time?",
            "body": """Hi {{first_name}},

Quick question - how much time does your team spend on manual processes each week?

I ask because most of the business owners I talk to here in SWFL are surprised when they add it up. Things like:

* Manually entering data into multiple systems
* Chasing invoices or following up on quotes by hand
* Updating spreadsheets that should update themselves
* Copying info from emails into your CRM or project tracker

These tasks feel small individually, but they add up to 10, 15, even 20+ hours a week. That's time you could be spending on growing your business or getting home earlier.

The good news? Most of these are straightforward to automate - and it's usually more affordable than people think.

If any of that sounds familiar, I'm happy to take a quick look at your workflow and share some ideas. No pitch, just honest perspective.

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 5,
            "purpose": "case_study",
            "subject": "How a local business cut admin time by 60%",
            "body": """Hi {{first_name}},

I wanted to share a quick story that might resonate with you.

A service company here in Southwest Florida came to us spending 15+ hours a week on admin - manually scheduling jobs, sending invoices, and tracking customer info across three different tools.

We built them a simple custom system that:
✅ Auto-generates invoices when a job is completed
✅ Syncs their schedule, CRM, and accounting in real-time
✅ Sends automated follow-ups and review requests

The result? They cut their admin time by over 60% and freed up their team to focus on actual revenue-generating work.

Every business is different, but the pattern is the same - repetitive manual work that technology can handle for you.

If you're curious what that could look like for{{#company}} {{company}}{{/company}}{{^company}} your business{{/company}}, I'd love to chat.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 10,
            "purpose": "consultation_offer",
            "subject": "Free 30-minute strategy call - no strings attached",
            "body": """Hi {{first_name}},

I know you're busy, so I'll keep this short.

I'd like to offer you a free 30-minute strategy call where we can:

📋 Walk through your current processes and tools
👍 Identify the biggest time-wasters and bottlenecks
💡 Map out 2-3 specific ways technology could save you time and money

No sales pitch. No obligation. Just a straightforward conversation about where you are and what's possible.

I've done these calls with dozens of business owners in Cape Coral and Fort Myers, and the feedback is always the same - "I wish I'd done this sooner."

If you're interested, just reply to this email and we'll find a time that works.

Best,
{{your_name}}
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}"""
        },
        {
            "day": 18,
            "purpose": "overcome_objections",
            "subject": "The #1 concern I hear from business owners",
            "body": """Hi {{first_name}},

When I talk to business owners about custom software or automation, the most common concern I hear is:

"That sounds expensive - and I don't know if it'll actually work for my business."

Totally fair. So let me address both:

**On cost:** We're not talking about six-figure enterprise software. Most of our projects for local businesses range from a few thousand to mid five figures - and they typically pay for themselves within months through time savings and efficiency gains.

**On fit:** That's exactly why we start with a conversation, not a contract. We learn your business first, then recommend solutions that make sense. If something doesn't make sense for you, I'll tell you straight up.

We also work in phases - start small, prove the value, then expand. No big-bang projects that take a year to see results.

I genuinely just enjoy helping local businesses work smarter. If you've been thinking about it but haven't pulled the trigger, I'm here whenever you're ready.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 28,
            "purpose": "final_push",
            "subject": "Quick offer before the month wraps up",
            "body": """Hi {{first_name}},

I wanted to reach out one last time with a quick offer.

Through the end of this month, I'm offering a **free technology assessment** for local businesses - a deeper dive than our usual strategy call. Here's what's included:

📝  Full review of your current tools, software, and workflows
📊 A written report with prioritized recommendations
💰 Estimated ROI for the top 2-3 improvements
💴   An action plan you can use whether you work with us or not

There's no catch - I do these because they consistently lead to great working relationships. And even if we never work together, you'll walk away with a clear picture of where technology can help.

If you're interested, just reply and we'll get it scheduled.

Either way, I appreciate you taking the time to read my emails. If there's ever anything I can help with down the road, don't hesitate to reach out.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}"""
        }
    ]
}

# ============================================
# PROSPECT CONVERSION DRIP CAMPAIGN (5 WEEK)
# ============================================

PROSPECT_DRIP_CAMPAIGN = {
    "campaign_id": "prospect-drip-5week",
    "campaign_name": "Prospect Conversion (5 Week)",
    "emails": [
        {
            "day": 0,
            "purpose": "personalized_followup",
            "subject": "Following up on our conversation",
            "body": """Hi {{first_name}},

Great speaking with you! I wanted to follow up while our conversation is still fresh.

Based on what you shared about{{#company}} {{company}} and{{/company}} your goals, I think there's a real opportunity to streamline things and save your team significant time.

I've already been thinking about a few approaches that could work well for your situation. I'd love to dig deeper and put something specific together for you.

In the meantime, feel free to reach out if any other questions come up - I'm always available.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}"""
        },
        {
            "day": 3,
            "purpose": "relevant_case_study",
            "subject": "A project that reminded me of your situation",
            "body": """Hi {{first_name}},

I was working on a project this week and it reminded me of our conversation.

We recently worked with a business similar to yours that was dealing with a lot of the same challenges - disconnected systems, manual processes, and a team spending too much time on tasks that should be automated.

Here's what we built for them:
* A centralized dashboard that pulled data from all their tools into one view
* Automated workflows that eliminated hours of weekly data entry
* A client-facing portal that reduced back-and-forth emails by 80%

The whole project took about 6 weeks, and they saw ROI within the first two months.

I think we could do something similar for{{#company}} {{company}}{{/company}}{{^company}} your business{{/company}} - tailored to your specific needs, of course.

Would you be open to a quick call this week to explore it?

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 7,
            "purpose": "roi_breakdown",
            "subject": "The numbers behind automation (they're pretty compelling)",
            "body": """Hi {{first_name}},

I put together some quick numbers that I think you'll find interesting.

Based on what you shared about your current processes, here's a conservative estimate of what automation could look like:

📊 **Time Saved:** 10-15 hours/week across your team
💹  **Annual Value:** $25,000 - $40,000 in recaptured productivity
⚡ **Error Reduction:** 90%+ fewer manual entry mistakes
📋  **Capacity:** Handle 30-40% more volume without adding headcount

These are based on what we typically see with businesses your size. The actual numbers for{{#company}} {{company}}{{/company}}{{^company}} your business{{/company}} could be even better depending on the specifics.

The investment to get there is usually a fraction of the annual savings - meaning most clients see full payback within 3-6 months.

If you'd like me to run more detailed numbers for your specific situation, I'm happy to do that. Just say the word.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 14,
            "purpose": "proposal_offer",
            "subject": "Ready to put something concrete together for you",
            "body": """Hi {{first_name}},

I've been thinking about your situation and I'd love to put together a specific proposal for you.

Here's what I have in mind:

1âƒ£ **Quick discovery call** (30 min) - Walk me through your day-to-day workflows so I can understand exactly what needs to happen
2âƒ£ **Custom proposal** - I'll put together a detailed plan with scope, timeline, and investment - no vague estimates
3âƒ£ **Live demo** - If you'd like, I can show you similar solutions we've built so you can see exactly what you'd be getting

The discovery call is completely free, and the proposal comes with no obligation. I want you to have something concrete to evaluate - not just a sales pitch.

What does your schedule look like this week or next?

Best,
{{your_name}}
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}"""
        },
        {
            "day": 21,
            "purpose": "social_proof_urgency",
            "subject": "Our schedule is filling up - wanted to let you know",
            "body": """Hi {{first_name}},

Quick heads up - our project calendar is starting to fill up for the next couple of months.

I didn't want you to miss out if this is something you've been thinking about. We're a small, focused team (by design), and we only take on a limited number of projects at a time so we can deliver great results.

Here's what a few recent clients have said:

⭐ "Patrick and his team delivered exactly what we needed, on time and on budget. Our team saves hours every week."

⭐ "I wish we'd done this two years ago. The ROI was almost immediate."

⭐ "Working with Metro Point felt like having a tech partner, not just a vendor."

If you'd like to get on the calendar, now would be a great time to start the conversation. Even a quick call to scope things out would give us a better timeline.

No pressure at all - just wanted to keep you in the loop.

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 35,
            "purpose": "last_chance",
            "subject": "The door is always open",
            "body": """Hi {{first_name}},

I realize I've sent you a few emails and I want to be respectful of your time. This will be my last planned follow-up.

If now isn't the right time - that's completely okay. Business priorities shift, budgets change, and sometimes the timing just isn't right. I get it.

But I want you to know that whenever you are ready, the door is wide open. Whether it's next month, next quarter, or next year - I'd love to help{{#company}} {{company}}{{/company}}{{^company}} your business{{/company}} work smarter with technology.

In the meantime, feel free to reach out anytime with questions - even just to bounce an idea around. That's what I'm here for.

Wishing you and your team all the best!

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}"""
        }
    ]
}

# ============================================
# CLIENT SUCCESS DRIP CAMPAIGN (8 WEEK)
# ============================================

CLIENT_DRIP_CAMPAIGN = {
    "campaign_id": "client-drip-8week",
    "campaign_name": "Client Success (8 Week)",
    "emails": [
        {
            "day": 0,
            "purpose": "welcome_onboarding",
            "subject": "Welcome aboard - here's what to expect!",
            "body": """Hi {{first_name}},

Welcome to the Metro Point Technology family! I'm thrilled to be working with{{#company}} {{company}} and{{/company}} you on this project.

Here's what you can expect from us:

📋 **This Week:** I'll send over a kickoff questionnaire and we'll schedule our first working session
📞 **Communication:** You'll hear from me at least weekly with progress updates
👍  **Access:** You'll have direct access to me via email, phone, or text - no support tickets or runaround
🔌  **Timeline:** We'll have a detailed project timeline within the first week

A few things that make working with us different:
* We're a small team, which means you work directly with me - not a rotating cast of account managers
* We build in phases so you see progress early and often
* Your feedback drives the process - this is your solution, built your way

I'm genuinely excited about what we're going to build together. If you have any questions before we officially kick off, don't hesitate to reach out.

Let's do this!

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}"""
        },
        {
            "day": 7,
            "purpose": "check_in",
            "subject": "Quick check-in - how's everything going?",
            "body": """Hi {{first_name}},

We're one week in and I wanted to do a quick check-in outside of our regular project updates.

How are you feeling about everything so far? Is the process making sense? Any questions or concerns I can address?

I know starting a new tech project can feel like a lot, so I want to make sure you're comfortable with the pace and direction. If anything feels off or unclear, please tell me - I'd much rather adjust early than find out later.

Also, if there's anything you need from my end that I haven't provided, just say the word.

Looking forward to hearing from you!

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 14,
            "purpose": "tips_best_practices",
            "subject": "Tips to get the most out of your new solution",
            "body": """Hi {{first_name}},

As we continue building out your solution, I wanted to share some tips and best practices that our most successful clients follow:

💯 **Start with the core workflow** - Don't try to use every feature on day one. Master the primary workflow first, then expand.

👥 **Get your team involved early** - The sooner your team starts using the system (even in its early stages), the smoother the transition will be.

📧  **Keep a running list** - As you use the system, jot down things you'd like tweaked or added. We'll incorporate these in our review sessions.

📊 **Track your baseline** - Note how long things take now so you can measure the improvement. Clients love seeing the before-and-after numbers.

💴  **Give honest feedback** - If something doesn't feel right, tell me. It's much easier to adjust during development than after launch.

These might seem simple, but they make a huge difference in how quickly you see value from your investment.

Any questions? I'm always just a call or email away.

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 28,
            "purpose": "satisfaction_review",
            "subject": "How are we doing? (+ a quick favor)",
            "body": """Hi {{first_name}},

We're about a month into our work together and I wanted to check in on how things are going.

A few questions I'd love your honest answers on:

1. Is the solution meeting your expectations so far?
2. Is the communication working for you, or would you prefer more/less?
3. Is there anything you wish we were doing differently?

Your feedback is incredibly valuable to me - it helps me make sure we're delivering exactly what you need.

**And a quick favor:** If you're happy with our work so far, would you mind leaving us a quick Google review? It makes a huge difference for a small local business like ours. Here's the link: {{your_website}}

If you're NOT happy with something - please tell me first! I want to make it right.

Thanks for being a great client, {{first_name}}. I genuinely appreciate working with you{{#company}} and the {{company}} team{{/company}}.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 42,
            "purpose": "upsell_awareness",
            "subject": "Have you thought about this?",
            "body": """Hi {{first_name}},

Now that your solution is up and running, I wanted to share some ideas for what's possible next.

Some of our clients have gotten great results by adding:

👥 **Website integration** - Connect your internal tools to your public website for seamless data flow
📧  **Mobile access** - Access your system on the go from any device
👍  **Third-party integrations** - Connect with QuickBooks, Google Workspace, Mailchimp, and hundreds of other tools
📊 **Reporting dashboards** - Visual dashboards that give you real-time business insights
💡  **Additional automation** - Automate more repetitive tasks as you identify them

I'm not trying to upsell you - I just want you to know what's on the table. Sometimes clients don't realize how much more their system can do until someone mentions it.

If any of these sound interesting, or if you have other ideas, I'd love to chat about what would make sense for{{#company}} {{company}}{{/company}}{{^company}} your business{{/company}}.

No rush - just planting seeds! 👥±

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 56,
            "purpose": "referral_ask",
            "subject": "Know anyone who could use our help?",
            "body": """Hi {{first_name}},

It's been about two months since we started working together, and I hope you're seeing real results from your new system!

I have a quick ask: **Do you know any other business owners who might benefit from custom software, a new website, or business automation?**

Most of our best clients come from referrals - and that's because a recommendation from someone they trust means a lot more than any ad we could run.

If anyone comes to mind - a fellow business owner, a colleague, someone from your networking group - I'd really appreciate an introduction. I promise I'll take great care of them, just like I do with you.

And of course, if there's anything else I can do for{{#company}} {{company}} or{{/company}} you, just let me know. It's been a pleasure working together and I look forward to continuing the partnership!

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}"""
        }
    ]
}

# ============================================
# FORMER CLIENT WIN-BACK DRIP CAMPAIGN (6 WEEK)
# ============================================

FORMER_CLIENT_DRIP_CAMPAIGN = {
    "campaign_id": "former-client-drip-6week",
    "campaign_name": "Win-Back (6 Week)",
    "emails": [
        {
            "day": 0,
            "purpose": "reconnect",
            "subject": "It's been a while - here's what's new at MPT",
            "body": """Hi {{first_name}},

It's been a while since we last worked together and I wanted to reach out and say hello!

I hope things are going well{{#company}} at {{company}}{{/company}}. A lot has been happening at Metro Point Technology, and I thought you'd want to know about some of the new things we've been building:

🔌  **Expanded automation capabilities** - We've gotten even better at connecting systems and eliminating manual processes
👥 **Modern website builds** - Fast, mobile-first websites that actually convert visitors into customers
📊 **Business dashboards** - Real-time visibility into the metrics that matter most
💡  **AI-powered tools** - Smart automation that goes beyond simple rule-based workflows

The Cape Coral and SWFL business community has been growing fast, and we've been growing right alongside it - helping local businesses compete with the big guys through smart technology.

I'd love to catch up and hear how things have been going on your end. No agenda - just reconnecting.

Feel free to reply or give me a call anytime.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}"""
        },
        {
            "day": 7,
            "purpose": "capabilities_showcase",
            "subject": "Some cool things we've been building lately",
            "body": """Hi {{first_name}},

I wanted to share a few recent projects that showcase what we've been up to. These might spark some ideas for{{#company}} {{company}}{{/company}}{{^company}} your business{{/company}}:

**🏏  Client Portal for a Service Company**
Built a self-service portal where their customers can request services, track status, and view invoices - all automated. Cut their phone call volume by 50%.

**📧  Mobile Inventory System for a Local Retailer**
Replaced their clipboard-and-spreadsheet inventory process with a mobile scanning app. Real-time inventory counts, automatic reorder alerts, and zero manual data entry.

**👍  CRM + Accounting Integration for a Professional Services Firm**
Connected their CRM to QuickBooks so invoices, payments, and client data all stay in sync automatically. Saved their admin team 12 hours a week.

Technology has come a long way since we last worked together, and there might be some new possibilities for your business that weren't available before.

If anything here caught your attention, I'd love to explore what it could look like for you.

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 14,
            "purpose": "returning_client_offer",
            "subject": "A special offer for our returning friends",
            "body": """Hi {{first_name}},

Since we've worked together before, I wanted to extend a special offer to you:

📝 **Returning Client Package:**
* **Free technology assessment** - Full review of your current tools and processes (normally a $500 value)
* **Priority scheduling** - Jump to the front of our project queue
* **10% returning client discount** - On your first new project with us

I genuinely value the relationships we've built with past clients. You already know how we work, what we deliver, and that we stand behind our work. I'd love the chance to help{{#company}} {{company}}{{/company}}{{^company}} your business{{/company}} again.

Whether it's updating something we built previously, tackling a new challenge, or just getting a second opinion on a tech decision - I'm here.

This offer doesn't expire, by the way. Whenever the timing is right for you, just reach out.

Best,
{{your_name}}
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}"""
        },
        {
            "day": 28,
            "purpose": "success_story",
            "subject": "How a returning client transformed their business",
            "body": """Hi {{first_name}},

I wanted to share a quick story about a client who came back to us after a couple of years - and the results were amazing.

They originally hired us to build a basic website. When they came back, their business had grown significantly and they were drowning in manual processes. Sound familiar?

Here's what we did in the second engagement:
* Automated their entire client onboarding process (went from 2 hours to 15 minutes per client)
* Built a custom dashboard that gave them real-time visibility into revenue, projects, and team utilization
* Integrated their website with their backend systems so leads flowed directly into their pipeline

**The result:** They grew their client base by 40% the following year without adding any admin staff. The technology paid for itself in under 3 months.

The best part? Because we'd already worked together, we hit the ground running. No ramp-up time, no getting-to-know-you phase - just results.

If you're ready to take things to the next level, I'd love to help.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 42,
            "purpose": "door_open",
            "subject": "The door is always open, {{first_name}}",
            "body": """Hi {{first_name}},

This is my last planned check-in, but I wanted you to know something: the door is always open.

Whether it's a quick question about technology, a second opinion on a vendor you're evaluating, or a full-blown project - I'm here. That's true whether it's next week or next year.

You can always reach me at:
📧 {{your_email}}
📞 {{your_phone}}
👥 {{your_website}}

It was a pleasure working with{{#company}} {{company}} and{{/company}} you, and I'd welcome the chance to do it again someday.

Wishing you continued success!

Best,
{{your_name}}
Metro Point Technology, LLC

{{unsubscribe_link}}"""
        }
    ]
}

# ============================================
# PARTNER ENGAGEMENT DRIP CAMPAIGN (6 WEEK)
# ============================================

PARTNER_DRIP_CAMPAIGN = {
    "campaign_id": "partner-drip-6week",
    "campaign_name": "Partner Engagement (6 Week)",
    "emails": [
        {
            "day": 0,
            "purpose": "partnership_appreciation",
            "subject": "Grateful for our partnership!",
            "body": """Hi {{first_name}},

I just wanted to take a moment to say how much I appreciate our partnership{{#company}} between Metro Point Technology and {{company}}{{/company}}.

Relationships like ours are what make the Cape Coral and Southwest Florida business community so great. We're all out here building something, and it's a lot better when we do it together.

As a quick refresher, here's what Metro Point Technology specializes in - so you know exactly who to think of when opportunities come up:

💳  **Custom Software** - Built-from-scratch applications tailored to specific business needs
👥 **Websites** - Modern, fast, conversion-focused websites for local businesses
💡  **Business Automation** - Connecting systems, eliminating manual processes, saving time

If there's ever anything I can do to support{{#company}} {{company}} or{{/company}} you, please don't hesitate to reach out. That's what partners are for.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}"""
        },
        {
            "day": 7,
            "purpose": "co_marketing",
            "subject": "Quick idea - let's promote each other",
            "body": """Hi {{first_name}},

I had an idea I wanted to run by you.

What if we did some co-marketing together? Nothing complicated - just simple ways to get in front of each other's audiences:

📧  **Social media shoutouts** - I feature{{#company}} {{company}}{{/company}}{{^company}} your business{{/company}} on our social media, you feature us on yours
📧  **Guest content** - I write a short piece for your audience about how tech can help their business, you share your expertise with mine
💡 **Joint networking** - Attend events together and introduce each other to our respective networks
📧 **Email features** - Mention each other in newsletters or client communications

It's a win-win - we both get exposure to a warm, trusted audience without spending a dime on ads.

What do you think? Even one of these could be a great start. I'm flexible on format - whatever works best for you.

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 14,
            "purpose": "referral_framework",
            "subject": "Let's make referrals easy for both of us",
            "body": """Hi {{first_name}},

I've been thinking about how we can make referring business to each other as easy as possible. Here's a simple framework:

**When to refer someone to Metro Point Technology:**
* They mention needing a website (new or redesign)
* They complain about manual processes or clunky software
* They're using spreadsheets for things that should be automated
* They need systems integrated (CRM, accounting, scheduling, etc.)
* They're growing and their current tech can't keep up

**What I do for the referral:**
* I'll mention your name and how you connected us
* I'll give them the same quality experience you'd expect
* I'll keep you posted on how it goes

**What I'd love to refer to you:**
* [I'd love to know what your ideal referral looks like! Reply and let me know]

I'm a big believer in mutual referrals - it's the best business development there is. No cold calls, no ads, just trusted introductions.

Let me know if this framework works for you, and feel free to modify it!

Best,
{{your_name}}
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 28,
            "purpose": "joint_success_story",
            "subject": "Let's create a success story together",
            "body": """Hi {{first_name}},

Here's an idea that could benefit both of us:

What if we put together a joint case study or success story? Something that showcases how our businesses complement each other and deliver more value together than either of us could alone.

Here's what I'm thinking:
📧  A short write-up (or even a quick video) about how we've helped a mutual client or how our services work together
👥 We both share it on our websites, social media, and with our networks
📧 Use it in our marketing materials to show the power of local business partnerships

It doesn't have to be fancy - even a short testimonial exchange would be valuable. People love seeing that local businesses collaborate and support each other.

Have you worked with any clients where our services overlapped or complemented each other? Or is there a scenario we could highlight?

I'd love to brainstorm this with you over coffee if you're up for it.

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}

{{unsubscribe_link}}"""
        },
        {
            "day": 42,
            "purpose": "quarterly_planning",
            "subject": "Quarterly check-in - let's stay connected",
            "body": """Hi {{first_name}},

It's been about six weeks since we last connected, and I wanted to do a quick quarterly check-in.

A few things I'd love to catch up on:

📊 **How's business?** - Anything exciting happening{{#company}} at {{company}}{{/company}}?
💡 **Referral check** - Have you come across anyone who might need tech help? I've been keeping an eye out for referrals for you too.
💡 **New ideas** - Any new ways we could collaborate or support each other?
📧  **Events** - Any upcoming networking events, chamber meetings, or industry events we should attend together?

I find that partnerships work best when there's regular, intentional communication - not just reaching out when we need something.

Would you be up for a quick 20-minute call or coffee to sync up? I'm flexible on timing.

Looking forward to hearing from you!

Best,
{{your_name}}
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}"""
        }
    ]
}

# ============================================
# ALL CAMPAIGNS MAP
# ============================================

CAMPAIGNS = {
    "networking": NETWORKING_DRIP_CAMPAIGN,
    "lead": LEAD_DRIP_CAMPAIGN,
    "prospect": PROSPECT_DRIP_CAMPAIGN,
    "client": CLIENT_DRIP_CAMPAIGN,
    "former_client": FORMER_CLIENT_DRIP_CAMPAIGN,
    "partner": PARTNER_DRIP_CAMPAIGN,
}

def calculate_drip_schedule(start_date=None, campaign=None):
    """Calculate the dates for each email in a drip campaign.

    Args:
        start_date: When the campaign starts (defaults to now)
        campaign: Campaign dict to use (defaults to NETWORKING_DRIP_CAMPAIGN for backwards compat)
    """
    if start_date is None:
        start_date = datetime.now()

    if campaign is None:
        campaign = NETWORKING_DRIP_CAMPAIGN

    schedule = []
    for email in campaign["emails"]:
        scheduled_date = start_date + timedelta(days=email["day"])
        schedule.append({
            "step": email["day"],
            "day": email["day"],
            "purpose": email["purpose"],
            "subject": email["subject"],
            "scheduled_for": scheduled_date.isoformat(),
            "sent_at": None
        })
    return schedule

# ============================================
# NAVIGATION SIDEBAR (self-contained)
# ============================================
HIDE_STREAMLIT_NAV = """
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: white;
    }
    section[data-testid="stSidebar"] .stRadio label span {
        color: white !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: rgba(255,255,255,0.7) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: white !important;
    }
</style>
"""

PAGE_CONFIG = {
    "Dashboard": {"icon": "\U0001F4CA", "path": "app.py"},
    "Discovery Call": {"icon": "\U0001F4DE", "path": "pages/01_Discovery.py"},
    "Companies": {"icon": "\U0001F3E2", "path": "pages/01a_Companies.py"},
    "Contacts": {"icon": "\U0001F465", "path": "pages/02_Contacts.py"},
    "Sales Pipeline": {"icon": "\U0001F4C8", "path": "pages/03_Pipeline.py"},
    "Projects": {"icon": "\U0001F4C1", "path": "pages/04_Projects.py"},
    "Service": {"icon": "\U0001f527", "path": "pages/10_Service.py"},
    "Tasks": {"icon": "\u2705", "path": "pages/05_Tasks.py"},
    "Time & Billing": {"icon": "\U0001F4B0", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "\U0001F4E7", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "\U0001F4CA", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "\u2699\uFE0F", "path": "pages/09_Settings.py"},
    "Help": {"icon": "\u2753", "path": "pages/11_Help.py"},
}

def render_sidebar(current_page="Marketing"):
    """Render the navigation sidebar"""
    st.markdown(HIDE_STREAMLIT_NAV, unsafe_allow_html=True)

    with st.sidebar:
        # Logo/Title
        st.image("logo.jpg", use_container_width=True)
        st.markdown("---")

        # Navigation using radio buttons
        pages = [f"{config['icon']} {name}" for name, config in PAGE_CONFIG.items()]
        current_index = list(PAGE_CONFIG.keys()).index(current_page) if current_page in PAGE_CONFIG else 0

        selected = st.radio("Navigation", pages, index=current_index, label_visibility="collapsed")

        # Handle navigation
        selected_name = selected.split(" ", 1)[1] if " " in selected else selected
        if selected_name != current_page:
            config = PAGE_CONFIG.get(selected_name)
            if config and config['path']:
                st.switch_page(config['path'])

        st.markdown("---")

def render_sidebar_stats(stats: dict):
    """Render stats in the sidebar"""
    with st.sidebar:
        st.markdown("### Quick Stats")
        for label, value in stats.items():
            st.metric(label, value)

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="MPT-CRM - Marketing",
    page_icon="favicon.jpg",
    layout="wide"
)

require_sso_auth(allow_bypass=False)

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar("Marketing")

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if 'mkt_campaigns' not in st.session_state:
    st.session_state.mkt_campaigns = []

if 'mkt_view_campaign' not in st.session_state:
    st.session_state.mkt_view_campaign = None

if 'mkt_email_templates' not in st.session_state:
    st.session_state.mkt_email_templates = [
        {
            "id": "tmpl-1",
            "name": "Networking Follow-Up - New Contact",
            "category": "follow_up",
            "subject": "Great meeting you at {{event_name}}",
            "body": """Hi {{first_name}},

It was great meeting you at {{event_name}} today. I enjoyed learning about {{conversation_topic}}.

I'm the owner of Metro Point Technology - we build custom software and web applications for businesses, with a focus on the insurance industry. If you ever need help streamlining operations with technology, I'd be happy to chat.

Would you like to grab coffee sometime and continue the conversation?

Best,
Patrick
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "event_name", "conversation_topic", "your_phone", "your_email", "your_website", "unsubscribe_link"],
            "tips": "Send within 24 hours of meeting. Reference something specific you discussed. Keep it short and personal."
        },
        {
            "id": "tmpl-2",
            "name": "Networking Follow-Up - Reconnection",
            "category": "follow_up",
            "subject": "Good seeing you again at {{event_name}}",
            "body": """Hi {{first_name}},

It was good seeing you again at {{event_name}} today. Always nice to catch up with familiar faces.

{{optional_reference}}

Quick update on my end - I recently launched Metro Point Technology, a custom software and web development company. We're focused on helping businesses (especially in the insurance space) automate and streamline their operations.

If you know anyone who could use help with software, websites, or business automation, I'd appreciate the referral. And if there's anything I can do for you, just let me know.

Let's grab lunch soon and catch up properly.

Best,
Patrick
Metro Point Technology, LLC
{{your_phone}}
{{your_email}}
{{your_website}}

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "event_name", "optional_reference", "your_phone", "your_email", "your_website", "unsubscribe_link"],
            "tips": "Acknowledge the existing relationship. Share your news briefly. Ask for referrals - warm contacts are great sources."
        },
        {
            "id": "tmpl-3",
            "name": "New Client Welcome",
            "category": "welcome",
            "subject": "Welcome to Metro Point Technology!",
            "body": """Hi {{first_name}},

Welcome to Metro Point Technology! I'm thrilled to be working with {{company_name}} on {{deal_title}}.

Here's what you can expect:

1. **Kickoff Call**: We'll schedule a call this week to align on goals and timeline
2. **Communication**: I'll send weekly progress updates every Friday
3. **Access**: You'll have direct access to me via email, phone, or our project portal

If you have any questions before we get started, don't hesitate to reach out.

Looking forward to building something great together!

Best,
Patrick
{{your_phone}}
{{your_email}}

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "company_name", "deal_title", "your_phone", "your_email", "unsubscribe_link"],
            "tips": "Send immediately when deal is won. Set clear expectations. Make them feel valued."
        },
        {
            "id": "tmpl-4",
            "name": "Proposal Follow-Up",
            "category": "proposal",
            "subject": "Following up on your proposal",
            "body": """Hi {{first_name}},

I wanted to check in on the proposal I sent for {{deal_title}}.

Have you had a chance to review it? I'm happy to jump on a quick call to walk through any questions or discuss adjustments.

Just let me know what works best for your schedule.

Best,
Patrick
{{your_phone}}

{{unsubscribe_link}}""",
            "merge_fields": ["first_name", "deal_title", "your_phone", "unsubscribe_link"],
            "tips": "Send 2-3 days after proposal. Don't be pushy. Offer to clarify."
        },
    ]

if 'mkt_selected_campaign' not in st.session_state:
    st.session_state.mkt_selected_campaign = None

if 'mkt_selected_template' not in st.session_state:
    st.session_state.mkt_selected_template = None

# Card Scanner session state
if 'mkt_scanned_contacts' not in st.session_state:
    st.session_state.mkt_scanned_contacts = []

if 'mkt_scanning_in_progress' not in st.session_state:
    st.session_state.mkt_scanning_in_progress = False

if 'mkt_scan_event_name' not in st.session_state:
    st.session_state.mkt_scan_event_name = ""

if 'mkt_import_results' not in st.session_state:
    st.session_state.mkt_import_results = None

if 'mkt_card_images' not in st.session_state:
    st.session_state.mkt_card_images = []


def show_campaign_detail(campaign_id):
    """Show full campaign detail with email sequence"""
    campaign = next((c for c in st.session_state.mkt_campaigns if c['id'] == campaign_id), None)
    if not campaign:
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        status_icon = {"active": "💢", "paused": "💡", "draft": "âšª", "completed": "✅"}.get(campaign['status'], "âšª")
        st.markdown(f"## {status_icon} {campaign['name']}")
    with col2:
        if st.button("- Back to Campaigns"):
            st.session_state.mkt_selected_campaign = None
            st.rerun()

    st.markdown("---")

    # Campaign info and stats
    info_col, stats_col = st.columns([2, 1])

    with info_col:
        st.markdown("### Campaign Settings")

        # Status toggle
        status_options = ["active", "paused", "draft"]
        status_labels = ["💢 Active", "💡 Paused", "âšª Draft"]
        current_idx = status_options.index(campaign['status']) if campaign['status'] in status_options else 0
        new_status_label = st.selectbox("Status", status_labels, index=current_idx)
        campaign['status'] = status_options[status_labels.index(new_status_label)]

        st.markdown(f"**Trigger:** {campaign['trigger']}")
        st.markdown(f"**Target Types:** {', '.join(campaign['target_types'])}")
        st.markdown(f"**Created:** {campaign['created_at']}")

    with stats_col:
        st.markdown("### Performance")
        st.metric("Enrolled", campaign['enrollments'])
        st.metric("Emails Sent", campaign['sent'])

        if campaign['sent'] > 0:
            open_rate = (campaign['opened'] / campaign['sent']) * 100
            click_rate = (campaign['clicked'] / campaign['sent']) * 100
            st.metric("Open Rate", f"{open_rate:.0f}%")
            st.metric("Click Rate", f"{click_rate:.0f}%")

    # Email sequence
    st.markdown("---")
    st.markdown("### 📧 Email Sequence")

    for i, email in enumerate(campaign['emails']):
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                if email['day'] == 0:
                    st.markdown("**Day 0**")
                    st.caption("(Trigger)")
                else:
                    st.markdown(f"**Day {email['day']}**")
                    st.caption(f"+{email['day']} days")

            with col2:
                st.markdown(f"**{email['subject']}**")
                if st.button("Edit Email", key=f"edit_email_{i}"):
                    st.toast("Email editor coming soon!")

            with col3:
                status_badge = {"active": "💢", "draft": "âšª", "paused": "💡"}.get(email['status'], "âšª")
                st.markdown(f"{status_badge} {email['status'].title()}")

    # Add email button
    if st.button("➕ Add Email to Sequence"):
        st.toast("Email builder coming soon!")

    # Enrollments section
    st.markdown("---")
    st.markdown("### 👥 Current Enrollments")

    if campaign['enrollments'] > 0:
        st.info(f"📊 {campaign['enrollments']} contacts currently enrolled in this campaign")
        if st.button("View All Enrollments"):
            st.toast("Enrollment list coming soon!")
    else:
        st.warning("No contacts enrolled yet.")

    if st.button("➕ Manually Enroll Contacts"):
        st.toast("Manual enrollment coming soon!")


def show_template_detail(template_id):
    """Show and edit email template"""
    template = next((t for t in st.session_state.mkt_email_templates if t['id'] == template_id), None)
    if not template:
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## ✉ {template['name']}")
    with col2:
        if st.button("- Back to Templates"):
            st.session_state.mkt_selected_template = None
            st.rerun()

    st.markdown("---")

    # Template editor
    col1, col2 = st.columns([2, 1])

    with col1:
        new_name = st.text_input("Template Name", template['name'])
        new_subject = st.text_input("Subject Line", template['subject'])
        new_body = st.text_area("Email Body", template['body'], height=400)

        if new_name != template['name'] or new_subject != template['subject'] or new_body != template['body']:
            template['name'] = new_name
            template['subject'] = new_subject
            template['body'] = new_body

        if st.button("💹  Save Template", type="primary"):
            st.success("Template saved!")

        # Send Test Email section
        st.markdown("---")
        st.markdown("### 📧  Send Test Email")
        test_email = st.text_input("Send test to:", value="patrick@metropointtechnology.com", key="test_email_addr")
        test_first_name = st.text_input("Test first name:", value="Patrick", key="test_first_name")

        if st.button("📧 Send Test Email", type="secondary"):
            st.toast("SendGrid integration coming soon!")

    with col2:
        st.markdown("### 👍  Merge Fields")
        st.caption("Click to copy")

        merge_fields = [
            ("{{first_name}}", "Contact's first name"),
            ("{{last_name}}", "Contact's last name"),
            ("{{company_name}}", "Company name"),
            ("{{event_name}}", "Event/source detail"),
            ("{{deal_title}}", "Deal/project name"),
            ("{{your_name}}", "Your name"),
            ("{{your_phone}}", "Your phone"),
            ("{{your_email}}", "Your email"),
            ("{{calendar_link}}", "Scheduling link"),
            ("{{unsubscribe_link}}", "Unsubscribe link"),
        ]

        for field, description in merge_fields:
            st.code(field)
            st.caption(description)

        st.markdown("---")
        st.markdown("### 📧  Category")
        categories = ["follow_up", "welcome", "proposal", "nurture", "re_engagement"]
        cat_labels = ["Follow-up", "Welcome", "Proposal", "Nurture", "Re-engagement"]
        current_idx = categories.index(template['category']) if template['category'] in categories else 0
        new_cat_label = st.selectbox("Category", cat_labels, index=current_idx)
        template['category'] = categories[cat_labels.index(new_cat_label)]

        # Show tips if available
        if template.get('tips'):
            st.markdown("---")
            st.markdown("### 💡 Tips")
            st.info(template['tips'])


# ============================================
# MAIN PAGE
# ============================================
st.title("\U0001F4E7 Marketing")

# Check if we're enrolling a contact from the Contacts page
enroll_contact_id = st.session_state.get('mkt_enroll_contact_id')
enroll_contact_name = st.session_state.get('mkt_enroll_contact_name', '')
enroll_contact_email = st.session_state.get('mkt_enroll_contact_email', '')

if enroll_contact_id:
    st.markdown("---")
    st.markdown(f"### 📧 Enroll Contact in Campaign")
    st.info(f"**Contact:** {enroll_contact_name} ({enroll_contact_email})")

    # Show available campaigns
    active_campaigns = [c for c in st.session_state.mkt_campaigns if c['status'] == 'active']

    if active_campaigns:
        campaign_options = {c['id']: f"{c['name']} ({len(c['emails'])} emails)" for c in active_campaigns}
        selected_campaign_id = st.selectbox(
            "Select a campaign:",
            options=list(campaign_options.keys()),
            format_func=lambda x: campaign_options[x]
        )

        col_enroll, col_cancel = st.columns(2)
        with col_enroll:
            if st.button("Enroll", type="primary", use_container_width=True):
                # Find the campaign and increment enrollments
                campaign = next((c for c in st.session_state.mkt_campaigns if c['id'] == selected_campaign_id), None)
                if campaign:
                    campaign['enrollments'] += 1
                    st.success(f"**{enroll_contact_name}** enrolled in **{campaign['name']}**!")
                    # Clear prefill values
                    for key in ['mkt_enroll_contact_id', 'mkt_enroll_contact_name', 'mkt_enroll_contact_email']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                # Clear prefill values
                for key in ['mkt_enroll_contact_id', 'mkt_enroll_contact_name', 'mkt_enroll_contact_email']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    else:
        st.warning("No active campaigns available. Create and activate a campaign first.")
        if st.button("- Back"):
            for key in ['mkt_enroll_contact_id', 'mkt_enroll_contact_name', 'mkt_enroll_contact_email']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# Show detail views if selected
elif st.session_state.mkt_selected_campaign:
    show_campaign_detail(st.session_state.mkt_selected_campaign)
elif st.session_state.mkt_selected_template:
    show_template_detail(st.session_state.mkt_selected_template)
else:
    # Tab navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["\U0001F4CA Dashboard", "\U0001F4E7 Campaigns", "\U0001F4DD Templates", "\U0001F4C7 Card Scanner", "\U0001F504 Process Cards", "\u2699\uFE0F Settings"])

    with tab1:
        # Marketing Dashboard
        st.markdown("### Campaign Performance Overview")
        st.info("📊 Campaign analytics will appear here once you start importing contacts and sending campaigns via the Card Scanner.")

        st.markdown("---")

        # Recent activity
        st.markdown("### 📬 Recent Email Activity")
        st.info("📊 SendGrid integration will show real-time email activity here (opens, clicks, bounces)")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        action_cols = st.columns(3)
        with action_cols[0]:
            if st.button("📧 Send One-Time Email", use_container_width=True):
                st.toast("One-time email sender coming soon!")
        with action_cols[1]:
            if st.button("👥 Enroll Contacts", use_container_width=True):
                st.toast("Bulk enrollment coming soon!")
        with action_cols[2]:
            if st.button("📋  View Full Reports", use_container_width=True):
                st.toast("Detailed reports coming soon!")

    with tab2:
        # Campaigns list - show the 6 predefined drip campaigns
        st.markdown("### 👍 Drip Campaigns")
        st.caption("Contact-type based drip campaigns. Contacts are automatically enrolled based on their type.")
        
        # Get enrollment stats from database using db_service
        try:
            from db_service import db_is_connected, db_get_active_enrollments
            campaign_stats = {}
            
            if db_is_connected():
                # Use the existing db_service function to get enrollments
                enrollments = db_get_active_enrollments() or []
                
                # Also get completed enrollments for stats
                from db_service import db
                if db:
                    all_enrollments_resp = db.table("campaign_enrollments").select("campaign_id, status").execute()
                    all_enrollments = all_enrollments_resp.data or []
                    
                    # Count by campaign_id and status
                    for e in all_enrollments:
                        cid = e.get("campaign_id", "unknown")
                        status = e.get("status", "unknown")
                        if cid not in campaign_stats:
                            campaign_stats[cid] = {"active": 0, "completed": 0, "paused": 0, "total": 0}
                        campaign_stats[cid][status] = campaign_stats[cid].get(status, 0) + 1
                        campaign_stats[cid]["total"] += 1
        except Exception as e:
            campaign_stats = {}
            # Don't show warning - just show 0 stats if DB unavailable
        
        # Display each campaign template
        campaign_icons = {
            "networking": "🤝",
            "lead": "🎯",
            "prospect": "📊",
            "client": "⭐",
            "former_client": "🔄",
            "partner": "🤝"
        }
        
        for campaign_type, campaign in CAMPAIGNS.items():
            stats = campaign_stats.get(campaign.get("campaign_id", ""), {"active": 0, "completed": 0, "total": 0})
            icon = campaign_icons.get(campaign_type, "📧")
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{icon} {campaign['campaign_name']}**")
                    st.caption(f"Type: {campaign_type.replace('_', ' ').title()}")
                
                with col2:
                    num_emails = len(campaign.get("emails", []))
                    last_day = max([e.get("day", 0) for e in campaign.get("emails", [])], default=0)
                    st.markdown(f"📧 {num_emails} emails")
                    st.caption(f"⏱️ {last_day} day campaign")
                
                with col3:
                    active = stats.get("active", 0)
                    completed = stats.get("completed", 0)
                    st.markdown(f"👥 {active} active")
                    st.caption(f"✅ {completed} completed")
                
                with col4:
                    if st.button("View", key=f"view_camp_{campaign_type}"):
                        st.session_state.mkt_view_campaign = campaign_type
                        st.rerun()
        
        # Show campaign details if one is selected
        if st.session_state.get('mkt_view_campaign'):
            campaign_type = st.session_state.mkt_view_campaign
            campaign = CAMPAIGNS.get(campaign_type)
            
            if campaign:
                st.markdown("---")
                st.markdown(f"### {campaign['campaign_name']} - Email Sequence")
                
                if st.button("← Back to Campaigns"):
                    st.session_state.mkt_view_campaign = None
                    st.rerun()
                
                for i, email in enumerate(campaign.get("emails", [])):
                    with st.expander(f"Day {email['day']}: {email['subject']}", expanded=(i == 0)):
                        st.caption(f"Purpose: {email.get('purpose', 'N/A').replace('_', ' ').title()}")
                        st.markdown("**Email Body:**")
                        st.text(email.get("body", "")[:500] + "..." if len(email.get("body", "")) > 500 else email.get("body", ""))

    with tab3:
        # Email templates
        st.markdown("### ✉ Email Templates")

        toolbar_col1, toolbar_col2 = st.columns([3, 1])
        with toolbar_col2:
            if st.button("➕ New Template", type="primary"):
                st.toast("Template builder coming soon!")

        # Group by category
        categories = {}
        for template in st.session_state.mkt_email_templates:
            cat = template['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(template)

        cat_labels = {
            "follow_up": "📞 Follow-up",
            "welcome": "💰   Welcome",
            "proposal": "📧  Proposal",
            "nurture": "👥± Nurture",
            "re_engagement": "👍  Re-engagement"
        }

        for cat, templates in categories.items():
            st.markdown(f"#### {cat_labels.get(cat, cat.title())}")

            for template in templates:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.markdown(f"**{template['name']}**")
                        st.caption(f"Subject: {template['subject']}")

                    with col2:
                        if st.button("Edit", key=f"edit_tmpl_{template['id']}"):
                            st.session_state.mkt_selected_template = template['id']
                            st.rerun()

    with tab4:
        # ============================================
        # CARD SCANNER TAB
        # ============================================
        st.markdown("### 📧  Business Card Scanner")
        st.caption("Upload business cards from networking events to extract contacts and start drip campaigns")

        # Check for import results to display
        if st.session_state.mkt_import_results:
            results = st.session_state.mkt_import_results
            st.success(f"**Import Complete!** {results['contacts_created']} contacts imported successfully")

            # Summary stats
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Contacts Created", results.get('contacts_created', 0))
            with col_stat2:
                st.metric("Enrolled in Campaign", results.get('enrollments_created', 0))
            with col_stat3:
                st.metric("Welcome Emails Sent", results.get('emails_sent', 0))

            # Show skipped contacts if any
            if results.get('skipped'):
                with st.expander(f"⚠ {len(results['skipped'])} Contacts Skipped", expanded=True):
                    st.warning("The following contacts were skipped because they already exist in your database:")
                    for skip in results['skipped']:
                        st.markdown(f"- **{skip['name']}** ({skip['email']}) - {skip['reason']}")
                    st.caption("💡 Tip: To add card info to existing contacts, select 'merge' from the dropdown during review.")

            # Show merged contacts if any
            if results.get('merged'):
                with st.expander(f"👍   {len(results['merged'])} Contacts Merged"):
                    st.info("The following cards were merged into existing contacts:")
                    for merge in results['merged']:
                        st.markdown(f"- **{merge['name']}** â†' merged with **{merge['merged_with']}**")

            # Show errors if any
            if results.get('errors'):
                with st.expander(f"âŒ {len(results['errors'])} Errors", expanded=True):
                    st.error("Some issues occurred during import:")
                    for error in results['errors']:
                        st.markdown(f"- {error}")

            # Detailed import log
            if results.get('import_log'):
                with st.expander("📋 Detailed Import Log", expanded=False):
                    for log_entry in results['import_log']:
                        st.text(log_entry)

            if results.get('enrollments_created', 0) > 0:
                # Show email schedule (use networking as default preview)
                with st.expander("📧  View Email Schedule", expanded=True):
                    schedule = calculate_drip_schedule(campaign=NETWORKING_DRIP_CAMPAIGN)
                    for i, step in enumerate(schedule):
                        scheduled_date = datetime.fromisoformat(step['scheduled_for'])
                        status_icon = "✅" if i == 0 else "📧 "
                        status_text = "Sent" if i == 0 else scheduled_date.strftime("%b %d, %Y")
                        st.markdown(f"**Day {step['day']}** - {step['purpose'].replace('_', ' ').title()} | {status_icon} {status_text}")
                        st.caption(f"Subject: {step['subject']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("👥 View Contacts", use_container_width=True):
                    st.switch_page("pages/02_Contacts.py")
            with col2:
                if st.button("👍  View Campaigns", use_container_width=True):
                    st.session_state.mkt_import_results = None
                    st.rerun()
            with col3:
                if st.button("📧  Scan More Cards", use_container_width=True):
                    st.session_state.mkt_import_results = None
                    st.session_state.mkt_scanned_contacts = []
                    st.session_state.mkt_card_images = []
                    st.rerun()

        # Show review interface if we have scanned contacts
        elif st.session_state.mkt_scanned_contacts:
            st.markdown("---")
            st.markdown(f"### Review Extracted Contacts ({len(st.session_state.mkt_scanned_contacts)} cards scanned)")

            # Event name (editable)
            event_name = st.text_input(
                "Event Name (for email personalization)",
                value=st.session_state.mkt_scan_event_name,
                key="review_event_name"
            )
            st.session_state.mkt_scan_event_name = event_name

            st.markdown("---")

            # Quick Apply to All section
            with st.expander("⚡ Quick Apply to All Contacts", expanded=True):
                st.markdown("Set defaults for all contacts at once. You can still edit individual contacts below.")

                quick_col1, quick_col2 = st.columns(2)

                with quick_col1:
                    # Contact Type
                    quick_contact_types = ["prospect", "lead", "client", "networking", "partner"]
                    quick_type_labels = ["💰  Prospect", "💯 Lead", "✅ Client", "💡 Networking", "💣💡  Partner"]
                    quick_contact_type_idx = 3  # Default to "networking"
                    quick_selected_type_label = st.selectbox("Contact Type", quick_type_labels, index=quick_contact_type_idx, key="quick_type")
                    quick_contact_type = quick_contact_types[quick_type_labels.index(quick_selected_type_label)]

                    # Source
                    quick_sources = ["networking", "referral", "website", "linkedin", "cold_outreach", "conference"]
                    quick_source_labels = ["Networking Event", "Referral", "Website", "LinkedIn", "Cold Outreach", "Conference"]
                    quick_source_idx = 0  # Default to "networking"
                    quick_selected_source_label = st.selectbox("Source", quick_source_labels, index=quick_source_idx, key="quick_source")
                    quick_source = quick_sources[quick_source_labels.index(quick_selected_source_label)]

                with quick_col2:
                    # Source Detail (pre-filled with event name)
                    quick_source_detail = st.text_input("Source Detail", value=event_name, key="quick_src_detail", help="Event name, referral source, etc.")

                    # Tags
                    quick_default_tags = ["Card Scanner", event_name] if event_name else ["Card Scanner"]
                    quick_tags_input = st.text_input("Tags (comma-separated)", value=", ".join(quick_default_tags), key="quick_tags")
                    quick_tags = [t.strip() for t in quick_tags_input.split(",") if t.strip()]

                if st.button("âœ¨ Apply to All Contacts", type="primary", use_container_width=True):
                    st.session_state.mkt_apply_to_all = {
                        "contact_type": quick_contact_type,
                        "source": quick_source,
                        "source_detail": quick_source_detail,
                        "tags": quick_tags
                    }
                    st.success("✅ Settings applied to all contacts! Review individual contacts below if you need to make changes.")
                    st.rerun()

            st.markdown("---")

            # Track which contacts to import
            contacts_to_import = []
            apply_to_all_settings = st.session_state.get('mkt_apply_to_all', {})

            for idx, contact in enumerate(st.session_state.mkt_scanned_contacts):
                confidence = contact.get('confidence', 0.5)
                confidence_icon = "✅" if confidence >= 0.7 else "⚠"
                confidence_label = "High confidence" if confidence >= 0.7 else "Low confidence - please verify"

                with st.expander(f"{confidence_icon} Card {idx + 1}: {contact.get('first_name', 'Unknown')} {contact.get('last_name', '')} ({confidence_label})", expanded=(confidence < 0.7)):

                    # Two-column layout: image on left, form on right
                    if idx < len(st.session_state.mkt_card_images):
                        col_img, col_form = st.columns([1, 2])
                        with col_img:
                            st.image(st.session_state.mkt_card_images[idx], caption="Original Card", use_container_width=True)
                    else:
                        col_img = None
                        col_form = st.container()

                    with col_form:
                        col1, col2 = st.columns(2)

                        with col1:
                            first_name = st.text_input("First Name", value=contact.get('first_name', '') or '', key=f"fn_{idx}")
                            company = st.text_input("Company", value=contact.get('company', '') or '', key=f"co_{idx}")
                            phone = st.text_input("Phone", value=contact.get('phone', '') or '', key=f"ph_{idx}")

                        with col2:
                            last_name = st.text_input("Last Name", value=contact.get('last_name', '') or '', key=f"ln_{idx}")
                            email = st.text_input("Email", value=contact.get('email', '') or '', key=f"em_{idx}")
                            title = st.text_input("Title", value=contact.get('title', '') or '', key=f"ti_{idx}")

                    # Check for potential duplicates using name -> company -> email priority
                    potential_duplicates = db_find_potential_duplicates_by_card(first_name, last_name, company, email)
                    merge_with_contact = None
                    is_exact_email_match = False

                    if potential_duplicates:
                        # Check if any match is an exact email match (highest certainty of duplicate)
                        email_matches = [d for d in potential_duplicates if "Same email" in d.get('match_reasons', [])]
                        if email_matches:
                            is_exact_email_match = True
                            st.warning(f"⚠ Contact with this email already exists: **{email_matches[0]['first_name']} {email_matches[0]['last_name']}**")

                        # Show all potential duplicates (sorted by priority: name > company > email)
                        st.info(f"👍 Found {len(potential_duplicates)} potential match(es)")

                        for dup in potential_duplicates[:3]:  # Show top 3
                            match_info = ", ".join(dup.get('match_reasons', []))
                            dup_name = f"{dup.get('first_name', '')} {dup.get('last_name', '')}".strip()
                            dup_email = dup.get('email', 'no email')
                            st.caption(f"* {dup_name} ({dup_email}) - **{match_info}**")

                        # Option to merge or create new
                        merge_options = ["Create new contact"] + [
                            f"{d['first_name']} {d['last_name']} ({d.get('email', 'no email')}) - {', '.join(d.get('match_reasons', []))}"
                            for d in potential_duplicates
                        ]
                        merge_choice = st.selectbox(
                            "Add to existing contact or create new?",
                            merge_options,
                            key=f"merge_{idx}",
                            index=1 if is_exact_email_match else 0  # Default to merge if exact email match
                        )

                        if merge_choice != "Create new contact":
                            # Find selected contact
                            selected_idx = merge_options.index(merge_choice) - 1
                            merge_with_contact = potential_duplicates[selected_idx]
                            st.success(f"Will add this card's info to **{merge_with_contact['first_name']} {merge_with_contact['last_name']}**'s record")

                    # Contact metadata (Type, Source, Tags)
                    st.markdown("---")
                    meta_col1, meta_col2 = st.columns(2)

                    with meta_col1:
                        # Contact Type - use Apply to All if set, otherwise default
                        contact_types = ["prospect", "lead", "client", "networking", "partner"]
                        type_labels = ["💰  Prospect", "💯 Lead", "✅ Client", "💡 Networking", "💣💡  Partner"]
                        default_type = apply_to_all_settings.get('contact_type', 'networking')
                        contact_type_idx = contact_types.index(default_type) if default_type in contact_types else 3
                        selected_type_label = st.selectbox("Contact Type", type_labels, index=contact_type_idx, key=f"type_{idx}")
                        contact_type = contact_types[type_labels.index(selected_type_label)]

                        # Source - use Apply to All if set, otherwise default
                        sources = ["networking", "referral", "website", "linkedin", "cold_outreach", "conference"]
                        source_labels = ["Networking Event", "Referral", "Website", "LinkedIn", "Cold Outreach", "Conference"]
                        default_source = apply_to_all_settings.get('source', 'networking')
                        source_idx = sources.index(default_source) if default_source in sources else 0
                        selected_source_label = st.selectbox("Source", source_labels, index=source_idx, key=f"source_{idx}")
                        source = sources[source_labels.index(selected_source_label)]

                    with meta_col2:
                        # Source Detail - use Apply to All if set, otherwise event name
                        default_source_detail = apply_to_all_settings.get('source_detail', event_name)
                        source_detail = st.text_input("Source Detail", value=default_source_detail, key=f"src_detail_{idx}", help="Event name, referral source, etc.")

                        # Tags - use Apply to All if set, otherwise default
                        default_tags = apply_to_all_settings.get('tags', ["Card Scanner", event_name] if event_name else ["Card Scanner"])
                        tags_input = st.text_input("Tags (comma-separated)", value=", ".join(default_tags), key=f"tags_{idx}")
                        tags = [t.strip() for t in tags_input.split(",") if t.strip()]

                    # Options
                    col_opt1, col_opt2, col_opt3, col_opt4 = st.columns(4)
                    with col_opt1:
                        include = st.checkbox("Include in import", value=True, key=f"inc_{idx}")
                    with col_opt2:
                        enroll = st.checkbox("Enroll in drip campaign", value=True, key=f"enr_{idx}")
                    with col_opt3:
                        send_email = st.checkbox("Send first email", value=True, key=f"send_{idx}")
                    with col_opt4:
                        save_card_image = st.checkbox("Save card image", value=True, key=f"img_{idx}")

                    if include:
                        print(f"[Review] Card {idx+1} checked for import: {first_name} {last_name}")
                        contacts_to_import.append({
                            "first_name": first_name,
                            "last_name": last_name,
                            "company": company,
                            "email": email,
                            "phone": phone,
                            "title": title,
                            "contact_type": contact_type,
                            "source": source,
                            "source_detail": source_detail,
                            "tags": tags,
                            "enroll": enroll,
                            "send_email": send_email,
                            "save_card_image": save_card_image,
                            "card_image_idx": idx,
                            "is_exact_email_match": is_exact_email_match and merge_with_contact is None,  # Skip only if email match AND not merging
                            "merge_with_contact": merge_with_contact
                        })
                    else:
                        print(f"[Review] Card {idx+1} NOT checked for import: {first_name} {last_name}")

            print(f"[Review] Total contacts to import: {len(contacts_to_import)}")
            st.markdown("---")

            # Import buttons
            col_back, col_skip, col_import = st.columns([1, 1, 2])

            with col_back:
                if st.button("- Back", use_container_width=True):
                    st.session_state.mkt_scanned_contacts = []
                    st.session_state.mkt_card_images = []
                    st.rerun()

            with col_import:
                if st.button(f"✅ Import {len(contacts_to_import)} Contacts & Start Campaign", type="primary", use_container_width=True):
                    if not contacts_to_import:
                        st.error("No contacts selected for import")
                    else:
                        print(f"[Import] Starting import of {len(contacts_to_import)} contacts")
                        # Process imports
                        results = {
                            "contacts_created": 0,
                            "emails_sent": 0,
                            "enrollments_created": 0,
                            "errors": [],
                            "skipped": [],
                            "merged": [],
                            "import_log": []
                        }

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for i, contact_data in enumerate(contacts_to_import):
                            print(f"[Import] Processing contact {i+1}: {contact_data.get('first_name')} {contact_data.get('last_name')}")
                            progress = (i + 1) / len(contacts_to_import)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing {contact_data['first_name']} {contact_data['last_name']}...")

                            # Skip if exact email match exists and user didn't choose to merge
                            if contact_data.get('is_exact_email_match'):
                                skip_reason = f"Duplicate email already exists"
                                skip_name = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip()
                                print(f"[Import] SKIPPING - exact email match: {contact_data['email']}")
                                results['skipped'].append({
                                    "name": skip_name,
                                    "email": contact_data.get('email', 'No email'),
                                    "reason": skip_reason
                                })
                                results['import_log'].append(f"âŒ Skipped: {skip_name} ({contact_data.get('email', 'no email')}) - {skip_reason}")
                                continue

                            print(f"[Import] No duplicate detected, proceeding with contact creation")

                            # Check if merging with existing contact
                            merge_contact = contact_data.get('merge_with_contact')
                            if merge_contact:
                                # Update existing contact with additional info from this card
                                contact_id = merge_contact['id']
                                merge_name = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip()
                                existing_notes = merge_contact.get('notes', '') or ''
                                new_notes = f"{existing_notes}\n\n--- Additional Card ({datetime.now().strftime('%Y-%m-%d')}) ---\nTitle: {contact_data.get('title', '')}\nPhone: {contact_data.get('phone', '')}\nEmail: {contact_data.get('email', '')}"

                                update_data = {"notes": new_notes.strip()}

                                # Add phone/email if missing on existing contact
                                if not merge_contact.get('phone') and contact_data.get('phone'):
                                    update_data['phone'] = contact_data['phone']
                                if not merge_contact.get('email') and contact_data.get('email'):
                                    update_data['email'] = contact_data['email']

                                db_update_contact(contact_id, update_data)

                                db_log_activity(
                                    "contact_updated",
                                    f"Additional card info added from {event_name or 'networking event'}",
                                    contact_id
                                )
                                results['contacts_created'] += 1  # Count as processed
                                results['merged'].append({
                                    "name": merge_name,
                                    "email": contact_data.get('email', 'No email'),
                                    "merged_with": f"{merge_contact.get('first_name', '')} {merge_contact.get('last_name', '')}".strip()
                                })
                                results['import_log'].append(f"👍   Merged: {merge_name} into existing contact {merge_contact.get('first_name', '')} {merge_contact.get('last_name', '')}")
                            else:
                                # Create new contact in database
                                new_contact = {
                                    "first_name": contact_data['first_name'],
                                    "last_name": contact_data['last_name'],
                                    "company": contact_data.get('company', ''),
                                    "email": contact_data.get('email', ''),
                                    "phone": contact_data.get('phone', ''),
                                    "type": contact_data.get('contact_type', 'networking'),
                                    "source": contact_data.get('source', 'networking'),
                                    "source_detail": contact_data.get('source_detail', event_name),
                                    "tags": contact_data.get('tags', ["Card Scanner"]),
                                    "notes": f"Title: {contact_data.get('title', '')}\nImported via Card Scanner on {datetime.now().strftime('%Y-%m-%d')}",
                                    "email_status": "active"
                                }

                                print(f"[Import] Creating contact in database: {new_contact}")
                                created = db_create_contact(new_contact)
                                print(f"[Import] Database response: {created}")

                                if created:
                                    results['contacts_created'] += 1
                                    contact_id = created['id']
                                    contact_name = f"{contact_data['first_name']} {contact_data['last_name']}"
                                    print(f"[Import] Contact created successfully with ID: {contact_id}")
                                    results['import_log'].append(f"✅ Created: {contact_name} ({contact_data.get('email', 'no email')})")

                                    # Log activity
                                    db_log_activity(
                                        "contact_created",
                                        f"Contact created via Card Scanner from {event_name or 'networking event'}",
                                        contact_id
                                    )
                                else:
                                    print(f"[Import] FAILED to create contact: {contact_data['first_name']} {contact_data['last_name']}")
                                    contact_name = f"{contact_data['first_name']} {contact_data['last_name']}"
                                    results['errors'].append(f"Failed to create: {contact_name}")
                                    results['import_log'].append(f"âŒ Error: Failed to create {contact_name}")
                                    continue

                            # Upload card image to Supabase Storage (if selected)
                            if contact_data.get('save_card_image', True):
                                card_idx = contact_data.get('card_image_idx', i)
                                if card_idx < len(st.session_state.mkt_card_images):
                                    image_url = upload_card_image_to_supabase(
                                        st.session_state.mkt_card_images[card_idx],
                                        contact_id
                                    )
                                    if image_url:
                                        db_update_contact(contact_id, {"card_image_url": image_url})

                            # Create campaign enrollment (for both new and merged contacts)
                            contact_name = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip()
                            enrollment = None
                            if contact_data.get('enroll', True):
                                # Select campaign based on contact type
                                ct = contact_data.get('contact_type', 'networking')
                                selected_campaign = CAMPAIGNS.get(ct, NETWORKING_DRIP_CAMPAIGN)
                                schedule = calculate_drip_schedule(campaign=selected_campaign)
                                enrollment_data = {
                                    "contact_id": contact_id,
                                    "campaign_id": selected_campaign["campaign_id"],
                                    "campaign_name": selected_campaign["campaign_name"],
                                    "status": "active",
                                    "current_step": 0,
                                    "total_steps": len(selected_campaign["emails"]),
                                    "step_schedule": json.dumps(schedule),
                                    "source": "business_card_scanner",
                                    "source_detail": event_name,
                                    "emails_sent": 0,
                                    "next_email_scheduled": schedule[0]["scheduled_for"] if schedule else None
                                }

                                enrollment = db_create_enrollment(enrollment_data)
                                if enrollment:
                                    results['enrollments_created'] += 1
                                    results['import_log'].append(f"📧 Enrolled: {contact_name} in {selected_campaign['campaign_name']}")
                                else:
                                    results['import_log'].append(f"⚠ Warning: Failed to enroll {contact_name} in campaign")
                            else:
                                results['import_log'].append(f"⏭ Skipped enrollment: {contact_name} (not selected for campaign)")

                            # Send first email (for both new and merged contacts)
                            if contact_data.get('send_email', True) and contact_data.get('email'):
                                first_email = selected_campaign["emails"][0]
                                subject = replace_merge_fields(first_email["subject"], contact_data, event_name)
                                body = replace_merge_fields(first_email["body"], contact_data, event_name)

                                email_result = send_email_via_sendgrid(
                                    to_email=contact_data['email'],
                                    to_name=f"{contact_data['first_name']} {contact_data['last_name']}",
                                    subject=subject,
                                    html_body=body,
                                    contact_id=contact_id,
                                    enrollment_id=enrollment["id"] if enrollment else None
                                )

                                if email_result.get('success'):
                                    results['emails_sent'] += 1
                                    results['import_log'].append(f"📨 Email sent: {contact_name}")
                                    db_log_activity(
                                        "email_sent",
                                        f"Welcome email sent: {subject}",
                                        contact_id
                                    )
                                    if enrollment:
                                        try:
                                            now = datetime.now().isoformat()
                                            if schedule:
                                                schedule[0]["sent_at"] = now
                                            next_scheduled = schedule[1].get("scheduled_for") if schedule and len(schedule) > 1 else None
                                            update_data = {
                                                "current_step": 1 if schedule else 0,
                                                "emails_sent": 1 if schedule else 0,
                                                "last_email_sent_at": now,
                                                "next_email_scheduled": next_scheduled,
                                                "step_schedule": json.dumps(schedule) if schedule else json.dumps([])
                                            }
                                            if not next_scheduled and schedule:
                                                update_data["status"] = "completed"
                                            db_update_enrollment(enrollment["id"], update_data)
                                        except Exception as update_err:
                                            results['import_log'].append(f"⚠ Enrollment update failed: {update_err}")
                                else:
                                    error_msg = f"Email failed for {contact_data['email']}: {email_result.get('error')}"
                                    results['errors'].append(error_msg)
                                    results['import_log'].append(f"âŒ Email error: {contact_name} - {email_result.get('error')}")
                            elif contact_data.get('send_email', True) and not contact_data.get('email'):
                                results['import_log'].append(f"⚠ No email: {contact_name} - cannot send welcome email")

                        progress_bar.empty()
                        status_text.empty()

                        # Store results and show success screen
                        st.session_state.mkt_import_results = results
                        st.session_state.mkt_scanned_contacts = []
                        st.session_state.mkt_card_images = []
                        st.rerun()

        # Show upload interface (default state)
        else:
            st.markdown("---")

            # Check for required API keys
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            sendgrid_key = os.getenv("SENDGRID_API_KEY")

            if not anthropic_key:
                st.error("⚠ **Anthropic API Key not configured.** Add ANTHROPIC_API_KEY to your .env file to enable card scanning.")
                st.code("ANTHROPIC_API_KEY=your-api-key-here")

            if not sendgrid_key:
                st.warning("⚠ **SendGrid API Key not configured.** Emails will not be sent. Add SENDGRID_API_KEY to your .env file.")

            # Upload section
            with st.container(border=True):
                st.markdown("#### Upload Business Cards")

                uploaded_files = st.file_uploader(
                    "Drop scanned sheets or card images here",
                    type=["pdf", "jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=True,
                    help="Upload 8.5x11 scanned sheets with multiple cards - AI will detect and crop each card individually. Or upload individual card photos."
                )

                event_name_input = st.text_input(
                    "Event Name (optional)",
                    placeholder="e.g., Cape Coral Chamber Networking, SWFL Tech Meetup",
                    help="This will be used in follow-up emails for personalization"
                )

                col_cards, col_event = st.columns(2)
                with col_cards:
                    expected_card_count = st.number_input(
                        "Expected cards per page (optional)",
                        min_value=0,
                        max_value=50,
                        value=0,
                        help="If you know how many cards are on each page (e.g., 9 cards), enter it here. 0 = auto-detect"
                    )

                if uploaded_files:
                    st.info(f"📝 {len(uploaded_files)} file(s) selected")

                    if st.button("👍 Scan Cards", type="primary", use_container_width=True, disabled=not anthropic_key):
                        st.session_state.mkt_expected_card_count = expected_card_count
                        st.session_state.mkt_scan_event_name = event_name_input
                        st.session_state.mkt_scanning_in_progress = True

                        # Process files - Step 1: Convert PDFs and collect raw page images
                        raw_page_images = []

                        with st.spinner("Processing uploaded files..."):
                            for file in uploaded_files:
                                file_bytes = file.read()

                                if file.type == "application/pdf":
                                    # Convert PDF pages to images
                                    pdf_images = convert_pdf_to_images(file_bytes)
                                    for img in pdf_images:
                                        if "error" in img:
                                            st.error(f"PDF Error: {img['error']}")
                                        else:
                                            raw_page_images.append({
                                                "image_bytes": img['image_bytes'],
                                                "type": "image/png",
                                                "source": f"PDF page {img['page_number']}"
                                            })
                                else:
                                    # Direct image upload
                                    mime_type = file.type or "image/jpeg"
                                    raw_page_images.append({
                                        "image_bytes": file_bytes,
                                        "type": mime_type,
                                        "source": file.name
                                    })

                        # Step 2: Detect and crop individual cards from each page
                        all_images = []
                        image_bytes_list = []
                        expected_count = st.session_state.get('mkt_expected_card_count', 0)

                        if raw_page_images:
                            if expected_count > 0:
                                st.info(f"📧  Processing {len(raw_page_images)} page(s), expecting {expected_count} cards per page...")
                            else:
                                st.info(f"📧  Processing {len(raw_page_images)} page(s), detecting individual cards...")
                            detect_progress = st.progress(0)

                            for page_idx, page_data in enumerate(raw_page_images):
                                detect_progress.progress((page_idx + 1) / len(raw_page_images))

                                with st.spinner(f"Detecting cards on {page_data['source']}..."):
                                    # Detect and crop individual cards from this page
                                    cropped_cards = process_page_for_cards(
                                        page_data['image_bytes'],
                                        page_data['type'],
                                        expected_count
                                    )

                                    for card_bytes in cropped_cards:
                                        all_images.append({
                                            "image_bytes": card_bytes,
                                            "type": "image/png",
                                            "source": page_data['source']
                                        })
                                        image_bytes_list.append(card_bytes)

                            detect_progress.empty()

                            # Store raw page and cropped cards for manual adjustment
                            st.session_state.mkt_raw_page_images = raw_page_images
                            st.session_state.mkt_cropped_cards = all_images
                            st.session_state.mkt_manual_crop_mode = True
                            st.rerun()
                        else:
                            st.error("No valid images found in uploaded files")

        # Manual crop adjustment interface - REDESIGNED
        if st.session_state.get('mkt_manual_crop_mode'):
            from PIL import Image

            st.markdown("### âœ' Manual Card Cropping")
            st.info("💰   View the full scanned page below. For each card, enter the crop coordinates to capture just that card.")

            raw_pages = st.session_state.mkt_raw_page_images
            expected_count = st.session_state.get('mkt_expected_card_count', 10)

            # Initialize crop boxes if not exists
            if 'mkt_crop_boxes' not in st.session_state:
                st.session_state.mkt_crop_boxes = []

            if not raw_pages:
                st.error("No page image available")
                st.session_state.mkt_manual_crop_mode = False
                st.rerun()

            # Get the first page (assuming single page for now)
            page_img_bytes = raw_pages[0]['image_bytes']
            page_img = Image.open(BytesIO(page_img_bytes))
            page_width, page_height = page_img.size

            # Display the full page prominently
            st.markdown(f"**Full Scanned Page** ({page_width} Ã- {page_height} pixels)")
            st.image(page_img_bytes, use_container_width=False, width=800)

            st.markdown("---")
            st.markdown(f"### Define {expected_count} Card Crop Boxes")
            st.caption(f"💡 Tip: Look at the page above and note the pixel coordinates around each card. Enter them below.")

            # Number of cards to extract
            num_cards = st.number_input("Number of cards to extract", min_value=1, max_value=20, value=expected_count, key="num_cards_to_crop")

            crop_boxes = []

            for i in range(num_cards):
                st.markdown(f"#### 📧  Card {i + 1}")
                col1, col2, col3, col4 = st.columns(4)

                # Default values for 2x5 grid
                default_cell_width = page_width // 2
                default_cell_height = page_height // 5
                col_idx = i % 2
                row_idx = i // 2

                default_left = col_idx * default_cell_width + 50
                default_top = row_idx * default_cell_height + 50
                default_right = default_left + default_cell_width - 100
                default_bottom = default_top + default_cell_height - 100

                with col1:
                    left = st.number_input(f"Left (X)", min_value=0, max_value=page_width, value=default_left, key=f"crop_left_{i}")
                with col2:
                    top = st.number_input(f"Top (Y)", min_value=0, max_value=page_height, value=default_top, key=f"crop_top_{i}")
                with col3:
                    right = st.number_input(f"Right (X)", min_value=0, max_value=page_width, value=default_right, key=f"crop_right_{i}")
                with col4:
                    bottom = st.number_input(f"Bottom (Y)", min_value=0, max_value=page_height, value=default_bottom, key=f"crop_bottom_{i}")

                # Preview this crop
                if right > left and bottom > top:
                    try:
                        cropped = page_img.crop((left, top, right, bottom))
                        st.image(cropped, caption=f"Preview Card {i + 1}", width=300)
                        crop_boxes.append((left, top, right, bottom))
                    except Exception as e:
                        st.warning(f"Invalid crop coordinates: {e}")
                else:
                    st.warning("Right must be > Left and Bottom must be > Top")

                st.markdown("---")

            # Generate cropped cards
            adjusted_cards = []
            for i, (left, top, right, bottom) in enumerate(crop_boxes):
                try:
                    cropped = page_img.crop((left, top, right, bottom))
                    output = BytesIO()
                    cropped.save(output, format="PNG")
                    adjusted_cards.append(output.getvalue())
                except Exception as e:
                    st.error(f"Failed to crop card {i + 1}: {e}")

            st.markdown("---")
            st.success(f"✅ {len(adjusted_cards)} cards ready to scan")

            col_back, col_continue = st.columns(2)
            with col_back:
                if st.button("- Back to Upload"):
                    st.session_state.mkt_manual_crop_mode = False
                    st.session_state.mkt_cropped_cards = []
                    st.session_state.mkt_raw_page_images = []
                    st.rerun()

            with col_continue:
                if st.button("✅ Continue to Scan", type="primary"):
                    st.session_state.mkt_manual_crop_mode = False

                    # Extract contacts from adjusted images
                    st.info(f"📧  Extracting contact information from {len(adjusted_cards)} cards...")
                    scanned_contacts = []
                    progress = st.progress(0)

                    for i in range(len(adjusted_cards)):
                        progress.progress((i + 1) / len(adjusted_cards))

                        with st.spinner(f"Scanning card {i + 1} of {len(adjusted_cards)}..."):
                            result = extract_contact_from_business_card(
                                adjusted_cards[i],
                                'image/png'
                            )

                            if "error" in result:
                                st.warning(f"Card {i + 1}: {result['error']}")
                                # Add placeholder with error
                                scanned_contacts.append({
                                    "first_name": "",
                                    "last_name": "",
                                    "company": "",
                                    "email": "",
                                    "phone": "",
                                    "title": "",
                                    "confidence": 0.0,
                                    "error": result['error'],
                                    "raw_text": result.get('raw_text', '')
                                })
                            else:
                                scanned_contacts.append(result)

                    progress.empty()

                    # Store results in session state
                    st.session_state.mkt_scanned_contacts = scanned_contacts
                    st.session_state.mkt_card_images = adjusted_cards
                    st.session_state.mkt_scanning_in_progress = False
                    st.session_state.mkt_cropped_cards = []
                    st.session_state.mkt_raw_page_images = []

                    st.rerun()

        # Info section (only show when not in manual crop mode)
        if not st.session_state.get('mkt_manual_crop_mode'):
            st.markdown("---")
            st.markdown("#### How It Works")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**1. Upload Cards**")
                st.caption("Upload scanned sheets with multiple cards or individual photos. AI automatically detects and crops each card from the page.")

            with col2:
                st.markdown("**2. Review & Edit**")
                st.caption("AI extracts contact details. Review the extracted data, fix any errors, and select contacts to import.")

            with col3:
                st.markdown("**3. Auto-Campaign**")
                st.caption("Contacts are added to your CRM and enrolled in the appropriate drip campaign based on contact type, with the first email sent immediately.")

            # Show campaign previews
            for campaign_type, campaign_data in CAMPAIGNS.items():
                with st.expander(f"📧 Preview: {campaign_data['campaign_name']}"):
                    for i, email in enumerate(campaign_data["emails"]):
                        purpose_icons = {"thank_you": "💡", "value_add": "💡", "coffee_invite": "â˜•",
                                         "check_in": "💰  ", "referral_ask": "🔢 ", "introduction": "💰  ",
                                         "pain_point_awareness": "💯", "case_study": "📊",
                                         "consultation_offer": "📞", "overcome_objections": "💹 ",
                                         "final_push": "🏁", "personalized_followup": "✉",
                                         "relevant_case_study": "📧 ", "roi_breakdown": "💰",
                                         "proposal_offer": "📧 ", "social_proof_urgency": "â°",
                                         "last_chance": "🔊", "welcome_onboarding": "📝 ",
                                         "tips_best_practices": "💡", "satisfaction_review": "â­",
                                         "upsell_awareness": "📋 ", "reconnect": "👍 ",
                                         "capabilities_showcase": "🔌 ", "returning_client_offer": "📝",
                                         "success_story": "🏏 ", "door_open": "🔊",
                                         "partnership_appreciation": "💡", "co_marketing": "📧 ",
                                         "referral_framework": "👍 ", "joint_success_story": "📧 ",
                                         "quarterly_planning": "📧 ", "expertise_share": "💡",
                                         "referral_soft": "🔢 "}
                        st.markdown(f"**Day {email['day']}** - {purpose_icons.get(email['purpose'], '📧')} {email['purpose'].replace('_', ' ').title()}")
                        st.caption(f"Subject: {email['subject']}")
                        if i < len(campaign_data["emails"]) - 1:
                            st.markdown("---")

    with tab5:
        # Process Cards - Queue System
        st.markdown("### 👍 Process Cards Queue")
        st.markdown("Cards captured with Quick Capture mode on mobile. Extract contact info with AI and import to CRM.")

        if not db_is_connected():
            st.error("âŒ Database not connected. Please check your Supabase configuration.")
        else:
            # Add retry button if there was a previous error
            if 'process_cards_error' in st.session_state:
                st.error(f"Previous error: {st.session_state.process_cards_error}")
                if st.button("👍  Retry Loading Cards"):
                    del st.session_state.process_cards_error
                    st.rerun()

            try:
                # Query contacts that need processing (first_name starts with [Unprocessed])
                with st.spinner("Loading cards from queue..."):
                    import time
                    # Retry logic for connection timeouts
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            unprocessed_cards = db_get_unprocessed_cards()
                            # Clear any previous errors on success
                            if 'process_cards_error' in st.session_state:
                                del st.session_state.process_cards_error
                            break
                        except Exception as retry_err:
                            if attempt < max_retries - 1:
                                st.warning(f"Connection timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                                time.sleep(2)
                            else:
                                raise retry_err

                if not unprocessed_cards:
                    st.info("📧  No cards in queue. Use Quick Capture on mobile to snap cards at events!")
                    st.markdown("#### How to Use Quick Capture:")
                    st.markdown("""
                    1. Open Quick Capture on your phone: `http://YOUR-IP:5000/quick`
                    2. Snap front/back photos of business cards (5 sec each)
                    3. Cards appear here automatically
                    4. Extract contact info with AI and import
                    """)
                else:
                    st.success(f"📬 {len(unprocessed_cards)} cards ready to process")

                    # Process cards one at a time
                    for idx, card in enumerate(unprocessed_cards):
                        with st.container(border=True):
                            col1, col2 = st.columns([1, 2])

                            with col1:
                                # Display card images (front and back) - use direct URL fields
                                card_image_url = card.get('card_image_url')
                                card_image_url_2 = card.get('card_image_url_2')

                                if card_image_url or card_image_url_2:
                                    if card_image_url and card_image_url_2:
                                        # Both sides available
                                        st.image(card_image_url, caption="📇 Front Side", use_container_width=True)
                                        st.image(card_image_url_2, caption="📇 Back Side", use_container_width=True)
                                    elif card_image_url:
                                        # Only front
                                        st.image(card_image_url, caption="📇 Business Card", use_container_width=True)
                                    elif card_image_url_2:
                                        # Only back (unusual)
                                        st.image(card_image_url_2, caption="📇 Business Card", use_container_width=True)
                                else:
                                    st.warning("No image available")

                                st.caption(f"Captured: {card.get('created_at', 'Unknown')[:10]}")
                                if card.get('source_detail'):
                                    st.caption(f"Event: {card['source_detail']}")

                            with col2:
                                st.markdown(f"**Card #{idx + 1}**")

                                # Action buttons
                                btn_col1, btn_col2 = st.columns(2)
                                with btn_col1:
                                    extract_btn = st.button(f"💡  Extract Info", key=f"extract_{card['id']}", use_container_width=True)
                                with btn_col2:
                                    delete_btn = st.button(f"💴   Delete", key=f"delete_{card['id']}", use_container_width=True, type="secondary")

                                # Handle delete
                                if delete_btn:
                                    try:
                                        # Delete the contact
                                        db_delete_contact(card['id'])
                                        st.success(f"✅ Card #{idx + 1} deleted")
                                        # Clear any extracted data
                                        if f'extracted_{card["id"]}' in st.session_state:
                                            del st.session_state[f'extracted_{card["id"]}']
                                        st.rerun()
                                    except Exception as del_err:
                                        st.error(f"Error deleting card: {del_err}")

                                # Handle extract
                                if extract_btn:
                                    with st.spinner("Extracting contact info with Claude Vision..."):
                                        # Call Claude Vision API
                                        extracted_data = extract_contact_from_card(card['card_image_url'])

                                        if extracted_data:
                                            st.session_state[f'extracted_{card["id"]}'] = extracted_data
                                            st.rerun()
                                        else:
                                            st.error("Failed to extract contact info. Please enter manually.")

                                # Show extracted data if available
                                if f'extracted_{card["id"]}' in st.session_state:
                                    extracted = st.session_state[f'extracted_{card["id"]}']

                                    st.markdown("#### Extracted Info (Review & Edit)")

                                    with st.form(key=f"form_{card['id']}"):
                                        first_name = st.text_input("First Name", value=extracted.get('first_name', ''))
                                        last_name = st.text_input("Last Name", value=extracted.get('last_name', ''))
                                        company = st.text_input("Company", value=extracted.get('company', ''))
                                        title = st.text_input("Title", value=extracted.get('title', ''))
                                        email = st.text_input("Email", value=extracted.get('email', ''))
                                        phone = st.text_input("Phone", value=extracted.get('phone', ''))

                                        # Contact type selection
                                        process_contact_types = ["networking", "lead", "prospect", "client", "former_client", "partner"]
                                        process_type_labels = ["💡 Networking", "💯 Lead", "💰  Prospect", "✅ Client", "👍  Former Client", "💣💡  Partner"]
                                        process_type_label = st.selectbox("Contact Type", process_type_labels, index=0, key=f"ptype_{card['id']}")
                                        process_contact_type = process_contact_types[process_type_labels.index(process_type_label)]

                                        # Show which campaign they'll be enrolled in
                                        campaign_for_type = CAMPAIGNS.get(process_contact_type, NETWORKING_DRIP_CAMPAIGN)
                                        enroll = st.checkbox(f"Enroll in {campaign_for_type['campaign_name']}", value=True, key=f"penroll_{card['id']}")

                                        col_a, col_b = st.columns(2)
                                        with col_a:
                                            submit = st.form_submit_button("✅ Save Contact", type="primary", use_container_width=True)
                                        with col_b:
                                            skip = st.form_submit_button("⏭ Skip", use_container_width=True)

                                        if submit:
                                            # Update the contact with extracted data
                                            update_data = {
                                                "first_name": first_name,
                                                "last_name": last_name,
                                                "company": company,
                                                "email": email,
                                                "phone": phone,
                                                "type": process_contact_type,
                                                "source": "mobile_scanner_processed",
                                                "notes": f"Title: {title}\nProcessed from Quick Capture on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                                "email_status": "active"
                                            }

                                            try:
                                                db_update_contact(card['id'], update_data)

                                                # Enroll in campaign if requested
                                                if enroll:
                                                    enroll_in_campaign(card['id'], card.get('source_detail', ''), contact_type=process_contact_type)

                                                st.success(f"✅ Contact saved: {first_name} {last_name}")
                                                del st.session_state[f'extracted_{card["id"]}']
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error saving contact: {e}")

                                        if skip:
                                            # Delete the unprocessed card
                                            try:
                                                db_delete_contact(card['id'])
                                                st.success("Card skipped and removed from queue")
                                                if f'extracted_{card["id"]}' in st.session_state:
                                                    del st.session_state[f'extracted_{card["id"]}']
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error skipping card: {e}")

            except Exception as e:
                error_msg = str(e)
                st.session_state.process_cards_error = error_msg
                st.error(f"Error loading queue: {error_msg}")
                st.info("💡 **Troubleshooting:** This error usually means a network timeout. Try:\n1. Refresh the page\n2. Check your internet connection\n3. Click the 'Retry' button above")

    with tab6:
        # SendGrid settings
        st.markdown("### ⚙ SendGrid Configuration")

        st.markdown("#### API Settings")
        api_key = st.text_input("SendGrid API Key", type="password", placeholder="SG.xxxxxxxxxxxx")
        st.caption("Get your API key from [SendGrid Dashboard](https://app.sendgrid.com/settings/api_keys)")

        st.markdown("#### Sender Settings")
        sender_email = st.text_input("Sender Email", value="patrick@metropointtechnology.com")
        sender_name = st.text_input("Sender Name", value="Patrick - Metro Point Technology")

        st.markdown("#### Tracking Settings")
        track_opens = st.checkbox("Track email opens", value=True)
        track_clicks = st.checkbox("Track link clicks", value=True)

        st.markdown("#### Unsubscribe Settings")
        unsubscribe_text = st.text_area(
            "Unsubscribe footer text",
            value="You're receiving this because you connected with Metro Point Technology. [Unsubscribe]({{unsubscribe_link}})"
        )

        if st.button("💹  Save Settings", type="primary"):
            st.success("Settings saved! (Note: Full SendGrid integration coming in Phase 4)")

        st.markdown("---")
        st.markdown("#### 📧  Webhook Status")
        st.warning("⚠ Webhook not configured. Set up webhook URL in SendGrid to receive open/click/bounce events.")
        st.code("Webhook URL: https://your-app-url.com/api/sendgrid/webhook")

        st.markdown("---")
        st.markdown("#### 👍  Claude API (for Card Scanner)")
        anthropic_configured = bool(os.getenv("ANTHROPIC_API_KEY"))
        if anthropic_configured:
            st.success("✅ Anthropic API Key configured")
        else:
            st.error("âŒ Anthropic API Key not configured")
            st.caption("Add ANTHROPIC_API_KEY to your .env file to enable business card scanning")
