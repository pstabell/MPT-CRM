"""
Populate drip campaign templates in the database
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_service import get_db

def populate_drip_templates():
    print("Populating drip campaign templates...")
    
    db = get_db()
    if not db:
        print("ERROR: Database connection failed")
        return False
    
    # Template data from v11 schema
    templates = [
        {
            "campaign_id": "networking-drip-6week",
            "name": "Networking Follow-Up (6 Week)",
            "description": "Automated 8-email follow-up sequence for networking contacts.",
            "email_sequence": [
                {"day": 0, "purpose": "thank_you", "subject": "Great meeting you!"},
                {"day": 3, "purpose": "value_add", "subject": "Quick resource I thought you'd find useful"},
                {"day": 7, "purpose": "coffee_invite", "subject": "Let's grab coffee"},
                {"day": 14, "purpose": "check_in", "subject": "Quick check-in"},
                {"day": 21, "purpose": "expertise_share", "subject": "Something I've been working on"},
                {"day": 28, "purpose": "reconnect", "subject": "Checking in - how's business?"},
                {"day": 35, "purpose": "referral_soft", "subject": "Quick thought"},
                {"day": 42, "purpose": "referral_ask", "subject": "One last thing"}
            ],
            "auto_enroll_contact_types": ["networking"]
        },
        {
            "campaign_id": "lead-drip",
            "name": "Lead Nurture (4 Week)",
            "description": "Automated 6-email nurture sequence for inbound leads from the website.",
            "email_sequence": [
                {"day": 0, "purpose": "introduction", "subject": "How we help local businesses save time & grow"},
                {"day": 2, "purpose": "pain_point_awareness", "subject": "Is this eating up your time?"},
                {"day": 5, "purpose": "case_study", "subject": "How a local business cut admin time by 60%"},
                {"day": 10, "purpose": "consultation_offer", "subject": "Free 30-minute strategy call — no strings attached"},
                {"day": 18, "purpose": "overcome_objections", "subject": "The #1 concern I hear from business owners"},
                {"day": 28, "purpose": "final_push", "subject": "Quick offer before the month wraps up"}
            ],
            "auto_enroll_contact_types": ["lead"]
        },
        {
            "campaign_id": "prospect-drip",
            "name": "Prospect Conversion (5 Week)",
            "description": "Automated 6-email conversion sequence for prospects.",
            "email_sequence": [
                {"day": 0, "purpose": "personalized_followup", "subject": "Following up on our conversation"},
                {"day": 3, "purpose": "relevant_case_study", "subject": "A project that reminded me of your situation"},
                {"day": 7, "purpose": "roi_breakdown", "subject": "The numbers behind automation (they're pretty compelling)"},
                {"day": 14, "purpose": "proposal_offer", "subject": "Ready to put something concrete together for you"},
                {"day": 21, "purpose": "social_proof_urgency", "subject": "Our schedule is filling up — wanted to let you know"},
                {"day": 35, "purpose": "last_chance", "subject": "The door is always open"}
            ],
            "auto_enroll_contact_types": ["prospect"]
        },
        {
            "campaign_id": "client-drip",
            "name": "Client Success (8 Week)",
            "description": "Automated 6-email success sequence for new clients.",
            "email_sequence": [
                {"day": 0, "purpose": "welcome_onboarding", "subject": "Welcome aboard — here's what to expect!"},
                {"day": 7, "purpose": "check_in", "subject": "Quick check-in — how's everything going?"},
                {"day": 14, "purpose": "tips_best_practices", "subject": "Tips to get the most out of your new solution"},
                {"day": 28, "purpose": "satisfaction_review", "subject": "How are we doing? (+ a quick favor)"},
                {"day": 42, "purpose": "upsell_awareness", "subject": "Have you thought about this?"},
                {"day": 56, "purpose": "referral_ask", "subject": "Know anyone who could use our help?"}
            ],
            "auto_enroll_contact_types": ["client"]
        }
    ]
    
    inserted_count = 0
    for template in templates:
        try:
            # Use upsert to handle conflicts
            result = db.table("drip_campaign_templates").upsert(template, on_conflict="campaign_id").execute()
            if result.data:
                inserted_count += 1
                print(f"  [OK] {template['campaign_id']}")
            else:
                print(f"  [ERROR] {template['campaign_id']}: No data returned")
        except Exception as e:
            print(f"  [ERROR] {template['campaign_id']}: {e}")
    
    print(f"\nInserted/updated {inserted_count}/{len(templates)} templates")
    
    # Verify the templates are now available
    print("\nVerifying templates...")
    try:
        all_templates = db.table("drip_campaign_templates").select("campaign_id, name").execute()
        if all_templates.data:
            print("Available templates:")
            for template in all_templates.data:
                print(f"  - {template['campaign_id']}: {template['name']}")
        return len(all_templates.data) == len(templates)
    except Exception as e:
        print(f"ERROR verifying templates: {e}")
        return False

if __name__ == "__main__":
    success = populate_drip_templates()
    if success:
        print("\n[SUCCESS] All drip campaign templates are now available!")
    else:
        print("\n[ERROR] Some templates failed to insert")