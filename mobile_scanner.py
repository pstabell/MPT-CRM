"""
Mobile Business Card Scanner - Flask Web App
Companion to MPT-CRM for mobile card scanning
Simple, fast manual entry (no OCR complexity, no API keys needed)
"""

from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta
import json
import base64
from io import BytesIO
from PIL import Image
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize clients
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

print("Mobile scanner ready!")

def find_duplicate_contact(first_name, last_name, email, company):
    """Find existing contact by email, name, or company"""
    try:
        # Check by email first (strongest match)
        if email:
            response = supabase.table("contacts").select("*").eq("email", email).execute()
            if response.data:
                return response.data[0]

        # Check by name + company
        if first_name and last_name and company:
            response = supabase.table("contacts").select("*")\
                .eq("first_name", first_name)\
                .eq("last_name", last_name)\
                .eq("company", company)\
                .execute()
            if response.data:
                return response.data[0]

        # Check by name only
        if first_name and last_name:
            response = supabase.table("contacts").select("*")\
                .eq("first_name", first_name)\
                .eq("last_name", last_name)\
                .execute()
            if response.data:
                return response.data[0]

        return None
    except Exception as e:
        print(f"Error checking duplicates: {e}")
        return None

def update_contact(contact_id, contact_data):
    """Update existing contact with new card info"""
    try:
        # Get existing contact
        existing = supabase.table("contacts").select("*").eq("id", contact_id).execute()
        if not existing.data:
            return {"success": False, "error": "Contact not found"}

        existing_contact = existing.data[0]
        existing_notes = existing_contact.get('notes', '') or ''

        # Append new card info to notes
        new_notes = f"{existing_notes}\n\n--- Additional Card ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ---\n"
        new_notes += f"Title: {contact_data.get('title', '')}\n"
        new_notes += f"Phone: {contact_data.get('phone', '')}\n"
        new_notes += f"Email: {contact_data.get('email', '')}\n"
        new_notes += f"Company: {contact_data.get('company', '')}"

        update_data = {"notes": new_notes.strip()}

        # Update phone/email if missing
        if not existing_contact.get('phone') and contact_data.get('phone'):
            update_data['phone'] = contact_data['phone']
        if not existing_contact.get('email') and contact_data.get('email'):
            update_data['email'] = contact_data['email']
        if not existing_contact.get('company') and contact_data.get('company'):
            update_data['company'] = contact_data['company']

        response = supabase.table("contacts").update(update_data).eq("id", contact_id).execute()
        return {"success": True, "contact": response.data[0], "updated": True}

    except Exception as e:
        return {"success": False, "error": str(e)}

def create_contact(contact_data):
    """Create contact in Supabase (or update if duplicate found)"""
    try:
        # Check for duplicates first
        duplicate = find_duplicate_contact(
            contact_data.get('first_name', ''),
            contact_data.get('last_name', ''),
            contact_data.get('email', ''),
            contact_data.get('company', '')
        )

        if duplicate:
            # Update existing contact
            return update_contact(duplicate['id'], contact_data)

        # Create new contact
        new_contact = {
            "first_name": contact_data.get('first_name', ''),
            "last_name": contact_data.get('last_name', ''),
            "company": contact_data.get('company', ''),
            "email": contact_data.get('email', ''),
            "phone": contact_data.get('phone', ''),
            "type": contact_data.get('type', 'networking'),
            "source": contact_data.get('source', 'mobile_scanner'),
            "source_detail": contact_data.get('source_detail', ''),
            "tags": contact_data.get('tags', ["Mobile Scanner"]),
            "notes": f"Title: {contact_data.get('title', '')}\nScanned via Mobile on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "email_status": "active"
        }

        response = supabase.table("contacts").insert(new_contact).execute()
        return {"success": True, "contact": response.data[0], "updated": False}

    except Exception as e:
        return {"success": False, "error": str(e)}

def upload_card_image(image_base64, contact_id):
    """Upload business card image to Supabase Storage with auto-rotation"""
    try:
        # Decode base64 image
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]

        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))

        # Auto-rotate based on EXIF orientation
        try:
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass  # If no EXIF data, skip rotation

        # Convert to RGB if needed
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        # Save as JPEG
        output = BytesIO()
        image.save(output, format='JPEG', quality=85)
        output.seek(0)

        # Generate unique filename
        filename = f"business-cards/{contact_id}_{uuid.uuid4().hex[:8]}.jpg"

        # Upload to Supabase Storage
        response = supabase.storage.from_("card-images").upload(
            filename,
            output.getvalue(),
            {"content-type": "image/jpeg", "upsert": "true"}
        )

        if response:
            # Get public URL
            public_url = supabase.storage.from_("card-images").get_public_url(filename)
            return public_url

        return None
    except Exception as e:
        print(f"Error uploading card image: {e}")
        return None

def enroll_in_campaign(contact_id, event_name=""):
    """Enroll contact in 6-week networking drip campaign"""
    try:
        # Calculate schedule
        schedule = []
        days = [0, 7, 14, 30, 45]
        purposes = ["thank_you", "value_add", "reconnect", "check_in", "referral_ask"]

        for i, day in enumerate(days):
            scheduled_date = datetime.now() + timedelta(days=day)
            schedule.append({
                "day": day,
                "purpose": purposes[i],
                "scheduled_for": scheduled_date.isoformat()
            })

        enrollment_data = {
            "contact_id": contact_id,
            "campaign_id": "6week_networking_drip",
            "campaign_name": "6-Week Networking Drip",
            "status": "active",
            "current_step": 0,
            "total_steps": 5,
            "step_schedule": json.dumps(schedule),
            "source": "mobile_scanner",
            "source_detail": event_name,
            "emails_sent": 0
        }

        response = supabase.table("campaign_enrollments").insert(enrollment_data).execute()
        return {"success": True, "enrollment": response.data[0]}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def index():
    """Main mobile scanner page"""
    return render_template('mobile_scanner.html')

@app.route('/quick')
def quick():
    """Quick Capture mode - rapid card scanning"""
    return render_template('quick_capture.html')

@app.route('/scan', methods=['POST'])
def scan_card():
    """Show form with card photo - manual entry is faster than OCR"""
    try:
        # Return empty contact data - user types it in while looking at photo
        contact_data = {
            "first_name": "",
            "last_name": "",
            "company": "",
            "title": "",
            "email": "",
            "phone": "",
            "confidence": 1.0
        }

        return jsonify({"success": True, "contact": contact_data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/quick-capture', methods=['POST'])
def quick_capture():
    """Quick Capture mode - just upload card images, process later in CRM"""
    try:
        print("[Quick Capture] Starting quick capture...")
        data = request.json
        front_image = data.get('front_image')
        back_image = data.get('back_image')
        event_name = data.get('event_name', '')

        print(f"[Quick Capture] Event: {event_name}, Has front: {bool(front_image)}, Has back: {bool(back_image)}")

        if not front_image:
            print("[Quick Capture] ERROR: No front image provided")
            return jsonify({"success": False, "error": "Front image required"}), 400

        # Create stub contact with unprocessed status
        print("[Quick Capture] Creating stub contact...")
        stub_contact = {
            "first_name": "[Unprocessed]",
            "last_name": f"Card #{datetime.now().strftime('%H%M%S')}",
            "type": "networking",
            "source": "mobile_scanner_queue",
            "source_detail": event_name,
            "tags": ["Needs Processing", "Mobile Scanner"],
            "notes": f"Quick captured at {datetime.now().strftime('%Y-%m-%d %H:%M')}\nEvent: {event_name}",
            "email_status": "pending"
        }

        response = supabase.table("contacts").insert(stub_contact).execute()
        contact_id = response.data[0]['id']
        print(f"[Quick Capture] Contact created: {contact_id}")

        # Upload card images
        card_image_urls = []
        if front_image:
            print("[Quick Capture] Uploading front image...")
            try:
                front_url = upload_card_image(front_image, contact_id)
                if front_url:
                    card_image_urls.append(front_url)
                    print(f"[Quick Capture] Front uploaded: {front_url}")
                else:
                    print("[Quick Capture] WARNING: Front upload returned None")
            except Exception as img_err:
                print(f"[Quick Capture] ERROR uploading front: {img_err}")
                # Continue anyway - we have the contact

        if back_image:
            print("[Quick Capture] Uploading back image...")
            try:
                back_url = upload_card_image(back_image, contact_id)
                if back_url:
                    card_image_urls.append(back_url)
                    print(f"[Quick Capture] Back uploaded: {back_url}")
                else:
                    print("[Quick Capture] WARNING: Back upload returned None")
            except Exception as img_err:
                print(f"[Quick Capture] ERROR uploading back: {img_err}")
                # Continue anyway

        # Update contact with card image URL
        if card_image_urls:
            print("[Quick Capture] Updating contact with image URL...")
            supabase.table("contacts").update({
                "card_image_url": card_image_urls[0]
            }).eq("id", contact_id).execute()

        print(f"[Quick Capture] SUCCESS - {len(card_image_urls)} images saved")
        return jsonify({
            "success": True,
            "contact_id": contact_id,
            "message": "Card captured! Process later in CRM.",
            "card_images_saved": len(card_image_urls)
        })

    except Exception as e:
        print(f"[Quick Capture] EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/import', methods=['POST'])
def import_contact():
    """Import contact to database with card images"""
    try:
        data = request.json
        contact_data = data.get('contact')
        enroll = data.get('enroll', True)
        event_name = data.get('event_name', '')
        front_image = data.get('front_image')
        back_image = data.get('back_image')

        # Create contact
        result = create_contact(contact_data)

        if not result['success']:
            return jsonify({"success": False, "error": result['error']}), 400

        contact_id = result['contact']['id']

        # Upload card images
        card_image_urls = []
        if front_image:
            front_url = upload_card_image(front_image, contact_id)
            if front_url:
                card_image_urls.append(front_url)

        if back_image:
            back_url = upload_card_image(back_image, contact_id)
            if back_url:
                card_image_urls.append(back_url)

        # Update contact with card image URL (use first image as primary)
        if card_image_urls:
            supabase.table("contacts").update({
                "card_image_url": card_image_urls[0]
            }).eq("id", contact_id).execute()

        # Enroll in campaign if requested
        if enroll:
            enroll_result = enroll_in_campaign(contact_id, event_name)
            if not enroll_result['success']:
                return jsonify({
                    "success": True,
                    "contact_id": contact_id,
                    "warning": f"Contact created but enrollment failed: {enroll_result['error']}"
                })

        return jsonify({
            "success": True,
            "contact_id": contact_id,
            "enrolled": enroll,
            "updated": result.get('updated', False),
            "card_images_saved": len(card_image_urls)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Run on all network interfaces so you can access from phone
    app.run(host='0.0.0.0', port=5000, debug=True)
