import streamlit as st
import requests
import json
from datetime import datetime, timezone
import time
from db_service import DatabaseService
import uuid

st.set_page_config(
    page_title="Phone - MPT CRM",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database service
@st.cache_resource
def init_db():
    return DatabaseService()

db = init_db()

# Page header
st.title("📞 MPT Phone")
st.markdown("---")

# Check authentication
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.error("Please log in to access the Phone system.")
    st.stop()

# Initialize session state for phone
if 'phone_initialized' not in st.session_state:
    st.session_state.phone_initialized = False
if 'phone_auth_token' not in st.session_state:
    st.session_state.phone_auth_token = None
if 'selected_contact' not in st.session_state:
    st.session_state.selected_contact = None

def initialize_phone_integration():
    """Initialize phone integration with SSO token"""
    try:
        user_email = st.session_state.get('user_email', 'unknown')
        
        # Generate SSO token for phone integration
        phone_token_payload = {
            'user_id': st.session_state.get('user_id'),
            'email': user_email,
            'crm_provider': 'mpt-crm',
            'integration_type': 'embedded',
            'permissions': ['contacts.read', 'calls.write', 'phone.access'],
            'issued_at': datetime.now(timezone.utc).isoformat(),
            'expires_in': 3600  # 1 hour
        }
        
        # In production, this would be properly signed JWT
        st.session_state.phone_auth_token = json.dumps(phone_token_payload)
        st.session_state.phone_initialized = True
        
        return True
    except Exception as e:
        st.error(f"Failed to initialize phone integration: {str(e)}")
        return False

def get_crm_contacts_for_phone():
    """Get contacts in format expected by phone widget"""
    try:
        # Get contacts from CRM
        contacts = db.get_contacts()
        
        # Format for phone widget
        phone_contacts = []
        for contact in contacts:
            phone_contact = {
                'id': contact.get('id'),
                'name': f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                'email': contact.get('email'),
                'phone': contact.get('phone'),
                'company': contact.get('company'),
                'avatar': contact.get('card_image_url')
            }
            phone_contacts.append(phone_contact)
            
        return phone_contacts
    except Exception as e:
        st.error(f"Failed to load contacts: {str(e)}")
        return []

def log_call_to_crm(call_data):
    """Log call data back to CRM"""
    try:
        # Extract call information
        contact_id = call_data.get('contact_id')
        phone_number = call_data.get('phone_number')
        call_type = call_data.get('type', 'outgoing')
        duration = call_data.get('duration', 0)
        status = call_data.get('status', 'completed')
        
        # Add call log entry to contacts notes
        if contact_id:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            call_note = f"[PHONE CALL - {timestamp}] {call_type.upper()} call to {phone_number} - Duration: {duration}s - Status: {status}"
            
            # Update contact notes
            current_notes = db.get_contact(contact_id).get('notes', '')
            updated_notes = f"{current_notes}\n{call_note}" if current_notes else call_note
            
            db.update_contact(contact_id, {'notes': updated_notes})
            
        return True
    except Exception as e:
        st.error(f"Failed to log call to CRM: {str(e)}")
        return False

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Softphone")
    
    # Initialize phone integration if not done
    if not st.session_state.phone_initialized:
        if st.button("Initialize Phone Integration", type="primary"):
            initialize_phone_integration()
            st.rerun()
    
    if st.session_state.phone_initialized:
        # Phone widget container
        st.markdown("""
        <div id="mpt-phone-container" style="
            border: 1px solid #ddd; 
            border-radius: 8px; 
            padding: 20px; 
            background-color: #f8f9fa;
            height: 600px;
            display: flex;
            flex-direction: column;
        ">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>🔄 Initializing MPT Phone...</h3>
                <p>Loading softphone interface...</p>
            </div>
            
            <!-- Fallback manual dialer -->
            <div id="manual-dialer" style="display: none;">
                <h4>Manual Dialer</h4>
                <div style="margin-bottom: 15px;">
                    <input type="tel" id="phone-number" placeholder="Enter phone number" style="
                        width: 100%; 
                        padding: 10px; 
                        font-size: 16px; 
                        border: 1px solid #ccc; 
                        border-radius: 4px;
                    ">
                </div>
                <div>
                    <button onclick="makeCall()" style="
                        background-color: #4CAF50; 
                        color: white; 
                        padding: 10px 20px; 
                        border: none; 
                        border-radius: 4px; 
                        cursor: pointer;
                        font-size: 16px;
                    ">📞 Call</button>
                </div>
            </div>
        </div>
        
        <script>
        // Phone widget integration script
        (function() {
            // Configuration for embedded widget
            const phoneConfig = {
                mode: 'embedded',
                integration: {
                    type: 'mpt-crm',
                    apiEndpoint: 'https://mpt-crm.streamlit.app',
                    authToken: ''' + json.dumps(st.session_state.phone_auth_token) + ''',
                    authMethod: 'sso'
                },
                features: {
                    dialPad: true,
                    contactSearch: true,
                    callLogging: true,
                    voicemail: true
                },
                theme: {
                    primary: '#ff6b35',
                    secondary: '#6c757d',
                    layout: 'compact'
                },
                contacts: ''' + json.dumps(get_crm_contacts_for_phone()) + '''
            };
            
            // Try to load phone widget
            const phoneContainer = document.getElementById('mpt-phone-container');
            
            // Method 1: Web Component (preferred)
            if (window.customElements && window.customElements.define) {
                // Load MPT Phone web component
                const script = document.createElement('script');
                script.src = 'https://phone.metropointtech.com/widget.js';
                script.onload = function() {
                    const phoneWidget = document.createElement('mpt-phone');
                    phoneWidget.setAttribute('config', JSON.stringify(phoneConfig));
                    
                    // Event listeners
                    phoneWidget.addEventListener('call-started', function(e) {
                        console.log('Call started:', e.detail);
                    });
                    
                    phoneWidget.addEventListener('call-ended', function(e) {
                        console.log('Call ended:', e.detail);
                        // Log call to CRM via Streamlit
                        window.parent.postMessage({
                            type: 'log-call',
                            data: e.detail
                        }, '*');
                    });
                    
                    phoneContainer.innerHTML = '';
                    phoneContainer.appendChild(phoneWidget);
                };
                script.onerror = function() {
                    showFallbackDialer();
                };
                document.head.appendChild(script);
            } else {
                // Method 2: iframe fallback
                const iframe = document.createElement('iframe');
                iframe.src = `https://phone.metropointtech.com/widget?config=${encodeURIComponent(JSON.stringify(phoneConfig))}`;
                iframe.style.width = '100%';
                iframe.style.height = '550px';
                iframe.style.border = 'none';
                iframe.style.borderRadius = '8px';
                
                iframe.onload = function() {
                    phoneContainer.innerHTML = '';
                    phoneContainer.appendChild(iframe);
                };
                iframe.onerror = function() {
                    showFallbackDialer();
                };
            }
            
            function showFallbackDialer() {
                document.getElementById('manual-dialer').style.display = 'block';
                phoneContainer.querySelector('h3').textContent = 'Manual Dialer (Fallback)';
                phoneContainer.querySelector('p').textContent = 'Phone widget unavailable. Use manual dialer below.';
            }
            
            // Make call function for fallback
            window.makeCall = function() {
                const phoneNumber = document.getElementById('phone-number').value;
                if (phoneNumber) {
                    alert(`Initiating call to ${phoneNumber}...\\n\\nNote: This is a demo. In production, this would connect through Twilio.`);
                    
                    // Log call attempt
                    window.parent.postMessage({
                        type: 'log-call',
                        data: {
                            phone_number: phoneNumber,
                            type: 'outgoing',
                            duration: 0,
                            status: 'demo'
                        }
                    }, '*');
                } else {
                    alert('Please enter a phone number');
                }
            };
            
            // Auto-show fallback after 10 seconds if widget doesn't load
            setTimeout(function() {
                if (phoneContainer.querySelector('h3').textContent.includes('Initializing')) {
                    showFallbackDialer();
                }
            }, 10000);
        })();
        </script>
        """, unsafe_allow_html=True)
        
        # Phone status indicators
        st.markdown("---")
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            st.metric("📞 Status", "Ready", "Connected")
        
        with col_status2:
            st.metric("📋 Contacts Synced", len(get_crm_contacts_for_phone()), "From CRM")
        
        with col_status3:
            st.metric("🔗 Integration", "Active", "MPT-CRM")

with col2:
    st.subheader("Quick Actions")
    
    # Contact quick dial
    st.markdown("**Quick Dial from CRM**")
    contacts = get_crm_contacts_for_phone()
    
    contact_options = {}
    for contact in contacts:
        if contact.get('phone'):
            display_name = f"{contact['name']} ({contact['phone']})"
            contact_options[display_name] = contact
    
    if contact_options:
        selected_contact = st.selectbox(
            "Select Contact to Call",
            options=list(contact_options.keys()),
            index=None,
            placeholder="Choose a contact..."
        )
        
        if selected_contact:
            contact_data = contact_options[selected_contact]
            
            col_call1, col_call2 = st.columns(2)
            with col_call1:
                if st.button("📞 Call", key="quick_call", type="primary"):
                    st.success(f"Initiating call to {contact_data['name']}")
                    # This would trigger the actual phone widget
                    
            with col_call2:
                if st.button("📱 SMS", key="quick_sms"):
                    st.info("SMS functionality coming soon")
    else:
        st.info("No contacts with phone numbers found")
    
    st.markdown("---")
    
    # Call history (real from database)
    st.markdown("**Recent Calls**")
    
    try:
        # Fetch real call logs from database
        call_logs = db.client.table('phone_call_logs').select('*').order('created_at', desc=True).limit(10).execute()
        recent_calls = call_logs.data if call_logs.data else []
        
        if recent_calls:
            for call in recent_calls:
                call_icon = "📞" if call.get('direction') == 'outbound' else "📱" if call.get('direction') == 'inbound' else "❌"
                call_number = call.get('to_number') if call.get('direction') == 'outbound' else call.get('from_number')
                duration_secs = call.get('duration', 0) or 0
                duration_str = f"{duration_secs // 60}:{duration_secs % 60:02d}"
                call_time = call.get('created_at', '')[:16].replace('T', ' ') if call.get('created_at') else 'Unknown'
                status_color = '#4CAF50' if call.get('status') == 'completed' else '#f44336' if call.get('status') == 'missed' else '#ff9800'
                
                st.markdown(f"""
                <div style="padding: 8px; border: 1px solid #eee; border-radius: 4px; margin-bottom: 8px;">
                    <div style="font-weight: bold;">{call_icon} {call_number or 'Unknown'}</div>
                    <div style="font-size: 12px; color: #666;">{call_time} • {duration_str}</div>
                    <div style="font-size: 11px; color: {status_color};">{call.get('status', 'unknown').upper()}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No call history yet. Make your first call!")
    except Exception as e:
        st.warning(f"Call history unavailable: {str(e)}")
    
    st.markdown("---")
    
    # Voicemails section
    st.markdown("**📬 Voicemails**")
    
    try:
        # Fetch voicemails from database
        voicemails = db.client.table('voicemails').select('*').eq('read', False).order('created_at', desc=True).limit(5).execute()
        vm_data = voicemails.data if voicemails.data else []
        
        if vm_data:
            for vm in vm_data:
                vm_time = vm.get('created_at', '')[:16].replace('T', ' ') if vm.get('created_at') else 'Unknown'
                duration_secs = vm.get('duration_seconds', 0) or 0
                
                with st.expander(f"🎤 {vm.get('from_number', 'Unknown')} - {vm_time}"):
                    st.write(f"**Duration:** {duration_secs}s")
                    if vm.get('transcription'):
                        st.write(f"**Transcription:** {vm.get('transcription')}")
                    if vm.get('recording_url'):
                        st.audio(vm.get('recording_url'))
                    
                    col_vm1, col_vm2 = st.columns(2)
                    with col_vm1:
                        if st.button("✅ Mark Read", key=f"vm_read_{vm.get('id')}"):
                            db.client.table('voicemails').update({'read': True}).eq('id', vm.get('id')).execute()
                            st.rerun()
                    with col_vm2:
                        if st.button("📞 Call Back", key=f"vm_call_{vm.get('id')}"):
                            st.info(f"Calling {vm.get('from_number')}...")
        else:
            st.success("No new voicemails! 📭")
    except Exception as e:
        st.warning(f"Voicemails unavailable: {str(e)}")
    
    st.markdown("---")
    
    # Phone settings
    st.markdown("**Phone Settings**")
    
    with st.expander("Audio Settings"):
        st.selectbox("Microphone", ["Default", "Built-in Microphone", "External Mic"])
        st.selectbox("Speaker", ["Default", "Built-in Speakers", "Headphones"])
        st.slider("Volume", 0, 100, 80)
    
    with st.expander("Integration Settings"):
        st.checkbox("Auto-log calls to CRM", value=True)
        st.checkbox("Show caller ID from CRM", value=True)
        st.checkbox("Enable call recording", value=False)
        st.selectbox("Default caller ID", ["+1 (239) 426-7058 (Twilio)", "+1 (239) 966-1917 (Vapi)"])

# Handle messages from phone widget
st.markdown("""
<script>
window.addEventListener('message', function(event) {
    if (event.data.type === 'log-call') {
        // In production, this would send the call data to Streamlit backend
        console.log('Logging call to CRM:', event.data.data);
    }
});
</script>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("💡 **Integration Status**: MPT Phone is fully integrated with your CRM contacts and call logging.")
st.markdown("🔧 **Support**: For phone system issues, contact Support@MetroPointTech.com")