from db_service import get_db, db_create_change_order
import uuid

# Create a test change order
test_co = {
    'id': str(uuid.uuid4()),
    'project_id': '2eb101eb-0eec-4c50-ba2a-20162ab88125',
    'title': 'TEST Integration Change Order',
    'description': 'Testing CRM to Mission Control integration',
    'status': 'approved',
    'requested_by': 'Metro Bot Test',
    'estimated_hours': 2.0,
    'hourly_rate': 150.0,
    'requested_at': '2026-02-14T09:00:00.000Z'
}

print('Creating test change order...')
result = db_create_change_order(test_co)
if result:
    print(f'Success! Created CO with ID: {result["id"]}')
    mc_card_id = result.get("mission_control_card_id", "Not created")
    print(f'Mission Control card ID: {mc_card_id}')
    
    if mc_card_id and mc_card_id != "Not created":
        print("✅ Integration successful - Mission Control card was created!")
    else:
        print("❌ Integration failed - No Mission Control card created")
else:
    print('Failed to create change order')