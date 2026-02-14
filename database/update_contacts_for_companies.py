#!/usr/bin/env python3
"""
Update Contacts Page for Companies Integration
Adds company dropdown and role functionality to existing contacts
"""

import re

def update_contacts_page():
    """Update the contacts page to integrate with companies"""
    
    # Read the existing contacts file
    with open('pages/02_Contacts.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add company helper functions after the existing helper functions
    company_functions = '''
# ============================================
# COMPANY INTEGRATION FUNCTIONS
# ============================================
@st.cache_data(ttl=300, show_spinner=False)
def get_companies_for_dropdown(_cache_key=None):
    """Get companies for dropdown selection"""
    if not db_is_connected():
        return []
    
    query = "SELECT id, name FROM companies ORDER BY name"
    try:
        companies = db_fetch_all(query) or []
        return [{"id": None, "name": "Individual/No Company"}] + companies
    except Exception:
        return [{"id": None, "name": "Individual/No Company"}]

def get_company_by_id(company_id):
    """Get company details by ID"""
    if not company_id or not db_is_connected():
        return None
    
    query = "SELECT id, name FROM companies WHERE id = %s"
    try:
        return db_fetch_one(query, (company_id,))
    except Exception:
        return None

ROLE_OPTIONS = ["Owner", "Billing", "Technical", "Project", "General"]

'''
    
    # Find where to insert the company functions (after the image helpers but before navigation)
    insert_point = content.find("# ============================================\n# NAVIGATION SIDEBAR")
    if insert_point == -1:
        insert_point = content.find("HIDE_STREAMLIT_NAV = ")
    
    if insert_point != -1:
        content = content[:insert_point] + company_functions + content[insert_point:]
    
    # Update the contact edit form to include company and role fields
    
    # Find the contact information section
    edit_section_pattern = r'(st\.markdown\("### 📋 Contact Information"\)\s*\n\s*edit_col1, edit_col2 = st\.columns\(2\))(.*?)(# Check if delete confirmation is pending)'
    
    edit_section_replacement = r'''\1
        
        # Company and Role Section (added for companies integration)
        company_col1, company_col2 = st.columns(2)
        with company_col1:
            # Get companies for dropdown
            cache_key = st.session_state.get('companies_cache_version', 0)
            companies = get_companies_for_dropdown(_cache_key=cache_key)
            
            company_options = [f"{c['name']}" for c in companies]
            current_company_id = contact.get('company_id')
            
            # Find current selection
            if current_company_id:
                current_company = get_company_by_id(current_company_id)
                if current_company:
                    current_index = next((i for i, c in enumerate(companies) if c['id'] == current_company_id), 0)
                else:
                    current_index = 0
            else:
                current_index = 0
            
            selected_company = st.selectbox(
                "Company", 
                company_options, 
                index=current_index,
                key="edit_company_selection"
            )
            
            # Store selected company ID
            selected_company_obj = companies[company_options.index(selected_company)]
            new_company_id = selected_company_obj['id']
            
        with company_col2:
            current_role = contact.get('role', '')
            role_index = ROLE_OPTIONS.index(current_role) if current_role in ROLE_OPTIONS else 0
            new_role = st.selectbox("Role", ROLE_OPTIONS, index=role_index, key="edit_role")
        
        # Show link to company if selected
        if new_company_id:
            st.markdown(f"🔗 [View Company Profile →](pages/X_Companies.py?company_id={new_company_id})")
        
\2\3'''
    
    content = re.sub(edit_section_pattern, edit_section_replacement, content, flags=re.DOTALL)
    
    # Update the save button logic to include company_id and role
    save_pattern = r'(update_data = {[^}]*?"company": new_company,)'
    save_replacement = r'''\1
                    "company_id": new_company_id,
                    "role": new_role,'''
    
    content = re.sub(save_pattern, save_replacement, content)
    
    # Update the new contact form to include company and role
    new_contact_pattern = r'(with col2:\s*company = st\.text_input\("Company".*?\)\s*)(type_options = list\(CONTACT_TYPES\.keys\(\)\))'
    
    new_contact_replacement = r'''\1
            # Company selection for new contacts
            cache_key = st.session_state.get('companies_cache_version', 0)
            companies = get_companies_for_dropdown(_cache_key=cache_key)
            company_options = [f"{c['name']}" for c in companies]
            
            selected_company_name = st.selectbox("Company", company_options, index=0, key="new_contact_company")
            selected_company_obj = companies[company_options.index(selected_company_name)]
            new_contact_company_id = selected_company_obj['id']
            
            # Role selection
            new_contact_role = st.selectbox("Role", ROLE_OPTIONS, index=4, key="new_contact_role")  # Default to "General"
            
            \2'''
    
    content = re.sub(new_contact_pattern, new_contact_replacement, content, flags=re.DOTALL)
    
    # Update new contact creation data
    contact_data_pattern = r'(contact_data = {[^}]*?"company": company,)'
    contact_data_replacement = r'''\1
                "company_id": new_contact_company_id,
                "role": new_contact_role if new_contact_company_id else None,'''
    
    content = re.sub(contact_data_pattern, contact_data_replacement, content)
    
    # Remove address fields from contact edit form (move to companies)
    address_section_pattern = r'# Addresses Section - Collapsible.*?st\.rerun\(\)\s*else:\s*st\.warning\("Physical address is empty"\)'
    content = re.sub(address_section_pattern, '', content, flags=re.DOTALL)
    
    # Update contact display to show company link instead of just text
    contact_display_pattern = r'st\.caption\(f"🏢 {contact\.get\(\'company\', \'N/A\'\)}"\)'
    contact_display_replacement = '''company_name = "Individual"
                    if contact.get('company_id'):
                        company = get_company_by_id(contact.get('company_id'))
                        if company:
                            company_name = company['name']
                    elif contact.get('company'):
                        company_name = contact.get('company', 'Individual')
                    
                    role_text = f" ({contact.get('role')})" if contact.get('role') else ""
                    st.caption(f"🏢 {company_name}{role_text}")'''
    
    content = re.sub(contact_display_pattern, contact_display_replacement, content)
    
    # Add second card image display
    card_display_pattern = r'(if card_image_url:\s*try:.*?st\.caption\(f"_Could not load image: {str\(e\)\[:30\]}_"\))'
    
    card_display_replacement = r'''\1
                    
                # Second card image (back side)
                card_image_url_2 = contact.get('card_image_url_2')
                if card_image_url_2:
                    st.markdown("**Back of Card:**")
                    rotation_key_2 = f"rotate_contact_{contact['id']}_card_2"
                    if rotation_key_2 not in st.session_state:
                        st.session_state[rotation_key_2] = 0
                    
                    try:
                        rotation_2 = st.session_state[rotation_key_2]
                        if rotation_2 == 0:
                            st.image(card_image_url_2, use_container_width=True)
                        else:
                            rotated_img_2 = get_rotated_image(card_image_url_2, rotation_2)
                            if rotated_img_2:
                                st.image(rotated_img_2, use_container_width=True)
                            else:
                                st.image(card_image_url_2, use_container_width=True)
                        
                        if st.button("↷ Rotate Back", key="rotate_card_back_only", use_container_width=True):
                            st.session_state[rotation_key_2] = (st.session_state[rotation_key_2] + 90) % 360
                            st.rerun()
                    except Exception as e:
                        st.caption(f"_Could not load back image: {str(e)[:30]}_")'''
    
    content = re.sub(card_display_pattern, card_display_replacement, content, flags=re.DOTALL)
    
    # Write the updated file
    with open('pages/02_Contacts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated contacts page for companies integration")
    return True

if __name__ == '__main__':
    try:
        update_contacts_page()
        print("✅ Contacts page updated successfully!")
        print("Key changes made:")
        print("   - Added company dropdown selection")
        print("   - Added role field")
        print("   - Added company profile links") 
        print("   - Added second card image display")
        print("   - Removed contact-level address fields")
        
    except Exception as e:
        print(f"❌ Update failed: {str(e)}")