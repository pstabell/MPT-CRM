"""
MPT-CRM Help & Manual
Complete workflow documentation and system guide

Database operations are handled by db_service.py — the single source of truth.
"""

import streamlit as st
from sso_auth import require_sso_auth, render_auth_status

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
    "Dashboard": {"icon": "📊", "path": "app.py"},
    "Discovery Call": {"icon": "📞", "path": "pages/01_Discovery.py"},
    "Contacts": {"icon": "👥", "path": "pages/02_Contacts.py"},
    "Sales Pipeline": {"icon": "🎯", "path": "pages/03_Pipeline.py"},
    "Projects": {"icon": "📁", "path": "pages/04_Projects.py"},
    "Service": {"icon": "\U0001f527", "path": "pages/10_Service.py"},
    "Tasks": {"icon": "✅", "path": "pages/05_Tasks.py"},
    "Time & Billing": {"icon": "💰", "path": "pages/06_Time_Billing.py"},
    "Marketing": {"icon": "📧", "path": "pages/07_Marketing.py"},
    "Reports": {"icon": "📈", "path": "pages/08_Reports.py"},
    "Settings": {"icon": "⚙️", "path": "pages/09_Settings.py"},
    "Help": {"icon": "❓", "path": "pages/11_Help.py"},
}

def render_sidebar(current_page="Help"):
    """Render the navigation sidebar"""
    st.markdown(HIDE_STREAMLIT_NAV, unsafe_allow_html=True)

    with st.sidebar:
        st.image("logo.jpg", use_container_width=True)
        st.markdown("---")

        pages = [f"{config['icon']} {name}" for name, config in PAGE_CONFIG.items()]
        current_index = list(PAGE_CONFIG.keys()).index(current_page) if current_page in PAGE_CONFIG else 0

        selected = st.radio("Navigation", pages, index=current_index, label_visibility="collapsed")

        selected_name = selected.split(" ", 1)[1] if " " in selected else selected
        if selected_name != current_page:
            config = PAGE_CONFIG.get(selected_name)
            if config and config['path']:
                st.switch_page(config['path'])

        st.markdown("---")

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="MPT-CRM - Help & Manual",
    page_icon="favicon.jpg",
    layout="wide"
)

require_sso_auth()

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar("Help")

# ============================================
# HELP CONTENT
# ============================================

st.title("❓ MPT-CRM Help & Manual")
st.caption("Complete workflow documentation and system guide")

# Create tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Quick Start", 
    "📁 Projects Workflow", 
    "🎯 Sales Pipeline", 
    "👥 Contact Management",
    "🔧 System Reference"
])

with tab1:
    st.markdown("## 🚀 Quick Start Guide")
    
    st.markdown("### Welcome to MPT-CRM!")
    st.info("MPT-CRM is Metro Point Technology's comprehensive customer relationship management system, designed specifically for insurance agency workflows and project management.")
    
    st.markdown("### Your First Steps:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **1. 📞 Capture Leads**
        - Use the **Discovery Call** page to intake new prospects
        - Scan business cards with mobile scanner
        - Import contacts manually in **Contacts** page
        
        **2. 🎯 Manage Your Pipeline**
        - Move deals through sales stages: Lead → Won
        - Track deal values and close dates
        - Use drag-and-drop Kanban board
        
        **3. 📁 Create Projects**
        - **WORKFLOW RULE:** Projects MUST link to Won deals
        - No orphan projects allowed
        - Automatic proposal integration
        """)
    
    with col2:
        st.markdown("""
        **4. ⏱️ Track Time & Bill Clients**
        - Log hours against projects
        - Generate invoices automatically
        - Track revenue and profitability
        
        **5. 📧 Market to Your Base**
        - Send targeted email campaigns
        - Use templates for common scenarios
        - Track open rates and engagement
        
        **6. 📊 Monitor Performance**
        - View dashboard metrics
        - Generate reports
        - Analyze pipeline health
        """)
    
    st.markdown("---")
    
    st.markdown("### 🔄 Typical Workflow:")
    st.markdown("""
    1. **📞 Discovery Call** → Capture prospect details and project requirements
    2. **👥 Add to Contacts** → Create contact record (automatically done from Discovery)
    3. **🎯 Create Deal** → Add to sales pipeline with estimated value
    4. **🏆 Win the Deal** → Move deal to "Won" stage when client says yes
    5. **📁 Create Project** → Link project to the Won deal (REQUIRED)
    6. **⏱️ Track Time** → Log work hours against the project
    7. **💰 Generate Invoice** → Bill client based on time logged
    8. **🔄 Repeat** → Continue cycle for additional projects
    """)

with tab2:
    st.markdown("## 📁 Projects Workflow")
    
    st.error("🔒 **CRITICAL WORKFLOW RULE: Every project MUST link to a Won deal. No orphan projects.**")
    
    st.markdown("### Why This Rule Exists:")
    st.markdown("""
    - **Sales Discipline:** Ensures you've sold the work before starting it
    - **Revenue Tracking:** Connects project costs to sales performance
    - **Client Clarity:** Each project has a clear scope and agreed value
    - **Business Intelligence:** Complete view of deal → project → revenue flow
    """)
    
    st.markdown("---")
    
    st.markdown("### Step-by-Step Project Creation:")
    
    with st.expander("📋 **Step 1: Win a Deal First**"):
        st.markdown("""
        Before creating any project, you must have a Won deal:
        
        1. Go to **🎯 Sales Pipeline**
        2. Create a deal with estimated value
        3. Move it through stages: Lead → Qualified → Proposal → Negotiation → Contract → **Won**
        4. Only **Won** deals can be linked to projects
        
        💡 **Tip:** The deal value should represent the total project value you've agreed with the client.
        """)
    
    with st.expander("🏗️ **Step 2: Create Project from Won Deal**"):
        st.markdown("""
        Once you have a Won deal:
        
        1. Go to **📁 Projects** page
        2. Click **➕ New Project**
        3. **Select Company:** Choose the company/contact (only those with Won deals appear)
        4. **Select Won Deal:** Pick the specific won deal to link to
        5. **Project Details:** Name, type, scope, timeline
        6. **Pricing:** Hours estimate and rate (auto-calculated from deal value)
        
        ✅ **Validation:** System prevents creating projects without valid Won deals
        """)
    
    with st.expander("📊 **Step 3: Track Progress & Bill Time**"):
        st.markdown("""
        With your project created and linked:
        
        1. **Log Time:** Record hours worked in project detail view
        2. **Track Progress:** Monitor hours vs estimate and budget burn
        3. **SharePoint Integration:** Link project folder for proposals/documents
        4. **Invoice Generation:** Create bills based on time logged
        5. **Mission Control:** Future integration with task cards
        
        📈 **Analytics:** View portfolio value, revenue earned, and remaining work
        """)
    
    st.markdown("---")
    
    st.markdown("### Project Types & Status:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Project Types:**
        - 🏷️ **Product:** Software products (AMS-APP, CRM-APP)
        - 🔧 **Project:** One-time implementations or services
        - 🌐 **Website:** Web development projects
        """)
    
    with col2:
        st.markdown("""
        **Project Status:**
        - 📋 **Planning:** Project approved, planning phase
        - 🚀 **Active:** Work in progress
        - ⏸️ **On Hold:** Temporarily paused
        - ✅ **Completed:** Work finished
        - 🛠️ **Maintenance:** Ongoing support
        - ❌ **Cancelled:** Project terminated
        """)
    
    st.markdown("---")
    
    st.markdown("### SharePoint Integration:")
    st.info("""
    📁 **Project Folders:** Each project can link to a SharePoint folder containing:
    - Proposals and contracts
    - Project documentation
    - Client communications
    - Deliverables and assets
    
    Access via the project detail view's "📁 Project Proposals" link.
    """)

with tab3:
    st.markdown("## 🎯 Sales Pipeline")
    
    st.markdown("### Pipeline Stages:")
    
    stages = [
        {"name": "Lead", "icon": "🔍", "desc": "Initial contact or inquiry"},
        {"name": "Qualified", "icon": "✅", "desc": "Confirmed fit and budget"},
        {"name": "Proposal", "icon": "📄", "desc": "Formal proposal submitted"},
        {"name": "Negotiation", "icon": "🤝", "desc": "Terms being discussed"},
        {"name": "Contract", "icon": "📝", "desc": "Contract being finalized"},
        {"name": "Won", "icon": "🏆", "desc": "Deal closed successfully - Ready for projects!"},
    ]
    
    for stage in stages:
        with st.container(border=True):
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"### {stage['icon']} {stage['name']}")
            with col2:
                st.markdown(f"**{stage['desc']}**")
                if stage['name'] == 'Won':
                    st.success("🔗 Projects can ONLY be created from Won deals!")
    
    st.markdown("---")
    
    st.markdown("### Deal Management Tips:")
    st.markdown("""
    - **Set Realistic Values:** Deal value should match expected project revenue
    - **Track Progress:** Move deals promptly to reflect actual status
    - **Add Context:** Use description field for important deal notes
    - **Set Priorities:** High/Medium/Low to focus on important opportunities
    - **Expected Close:** Target dates help with forecasting and follow-up
    """)
    
    st.markdown("### Won Deal Requirements:")
    st.warning("""
    🎯 **For Project Creation:**
    - Deal must be in "Won" stage
    - Deal cannot already be linked to another project
    - Contact/Company must exist and be linked to the deal
    - Deal should have a realistic value estimate
    """)

with tab4:
    st.markdown("## 👥 Contact Management")
    
    st.markdown("### Contact Types:")
    
    contact_types = [
        {"type": "Networking", "icon": "🤝", "desc": "Professional connections and referral sources"},
        {"type": "Prospect", "icon": "🎯", "desc": "Potential clients, early in sales process"},
        {"type": "Lead", "icon": "🔥", "desc": "Qualified prospects with active interest"},
        {"type": "Client", "icon": "👑", "desc": "Active paying customers"},
        {"type": "Former Client", "icon": "📋", "desc": "Past clients, potential for future work"},
        {"type": "Partner", "icon": "🤝", "desc": "Business partners and collaborators"},
        {"type": "Vendor", "icon": "🏢", "desc": "Service providers and suppliers"},
    ]
    
    for ctype in contact_types:
        with st.container(border=True):
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"### {ctype['icon']} {ctype['type']}")
            with col2:
                st.markdown(f"**{ctype['desc']}**")
    
    st.markdown("---")
    
    st.markdown("### Contact Detail Features:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📋 Contact Information**
        - Name, company, email, phone
        - Source tracking and tags
        - Notes and activity history
        
        **🎯 Related Deals**
        - View all deals for this contact
        - Create new deals directly
        - Quick access to pipeline
        """)
    
    with col2:
        st.markdown("""
        **📁 Related Projects**
        - View all projects for this contact
        - Create new projects from Won deals
        - Track project progress and value
        
        **📞 Discovery Forms**
        - View completed intake forms
        - Start new discovery calls
        - Track project requirements
        """)
    
    st.markdown("### Business Card Scanning:")
    st.info("""
    📱 **Mobile Scanner:** Use the mobile business card scanner to:
    - Automatically extract contact information
    - Capture and store card images
    - Create contacts with minimal manual entry
    - Perfect for networking events and meetings
    """)

with tab5:
    st.markdown("## 🔧 System Reference")
    
    st.markdown("### Database Schema Overview:")
    
    with st.expander("📊 **Core Tables**"):
        st.markdown("""
        **contacts** - Customer and prospect information
        **deals** - Sales pipeline tracking  
        **projects** - Client projects with deal linkage
        **time_entries** - Billable hours and time tracking
        **invoices** - Client billing and payments
        **activities** - Contact interaction history
        **email_templates** - Marketing message templates
        **email_campaigns** - Bulk email operations
        """)
    
    with st.expander("🔗 **Key Relationships**"):
        st.markdown("""
        **Contact → Deals** (One-to-Many)
        - Each contact can have multiple deals
        - Deals track sales opportunities
        
        **Deals → Projects** (One-to-One, Won deals only)
        - Each Won deal can become ONE project
        - Projects cannot exist without a Won deal
        
        **Projects → Time Entries** (One-to-Many)
        - Time tracking against specific projects
        - Billable hour calculations
        
        **Contacts → Activities** (One-to-Many)
        - Interaction history and notes
        - Email sends and call logs
        """)
    
    st.markdown("---")
    
    st.markdown("### System Requirements:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Database:** 
        - Supabase PostgreSQL
        - Real-time updates
        - UUID primary keys
        - Row-level security
        
        **Frontend:**
        - Streamlit web application
        - Mobile-responsive design
        - Session state management
        - Caching for performance
        """)
    
    with col2:
        st.markdown("""
        **Integration:**
        - SendGrid for email marketing
        - SharePoint for document storage
        - Mobile scanner for business cards
        - Mission Control for task management
        
        **Security:**
        - Authentication required
        - Database connection validation
        - Input sanitization
        - Error handling and logging
        """)
    
    st.markdown("---")
    
    st.markdown("### Troubleshooting:")
    
    with st.expander("❗ **Common Issues**"):
        st.markdown("""
        **"Cannot create project" error:**
        - Ensure you have Won deals available
        - Check that deal isn't already linked to another project
        - Verify contact has associated Won deals
        
        **Database connection issues:**
        - Check Supabase configuration
        - Verify environment variables
        - Test connection in Settings page
        
        **Missing projects in contact view:**
        - Refresh the page
        - Check project is linked to correct contact
        - Verify deal linkage is intact
        """)
    
    with st.expander("🔄 **Data Recovery**"):
        st.markdown("""
        **If projects appear missing:**
        1. Check the Projects page directly
        2. Verify deal linkages in Sales Pipeline
        3. Contact support for database queries
        
        **If deals are missing:**
        1. Check if they were moved to Lost status
        2. Verify they weren't accidentally deleted
        3. Check contact associations
        """)
    
    st.markdown("---")
    
    st.markdown("### Support & Updates:")
    
    st.info("""
    🛠️ **System Maintained By:** Metro Point Technology
    
    📧 **Support Email:** support@metropointtech.com
    
    📞 **Phone:** (239) 600-8159
    
    🌐 **Website:** MetroPointTech.com
    """)
    
    st.success("""
    ✅ **Current Version:** MPT-CRM v11 with Pipeline Integrity
    
    🔄 **Last Updated:** February 2026
    
    🆕 **Latest Features:**
    - Enforced project-to-deal linking
    - SharePoint proposal integration  
    - Enhanced contact project views
    - Improved workflow validation
    """)

# ============================================
# QUICK REFERENCE SECTION
# ============================================

st.markdown("---")
st.markdown("## 🔖 Quick Reference")

ref_col1, ref_col2, ref_col3 = st.columns(3)

with ref_col1:
    st.markdown("### 🎯 Sales Process")
    st.markdown("""
    1. Discovery → Contact
    2. Contact → Deal  
    3. Deal → Won
    4. Won → Project
    5. Project → Time
    6. Time → Invoice
    """)

with ref_col2:
    st.markdown("### 📁 Project Rules")
    st.markdown("""
    ✅ Must link to Won deal
    ❌ No orphan projects
    🔗 One deal = One project
    ⏱️ Track time against projects
    💰 Bill from time entries
    """)

with ref_col3:
    st.markdown("### 🚀 Quick Actions")
    st.markdown("""
    📞 New prospect → Discovery
    🎯 Active opportunity → Pipeline  
    📁 Won deal → New Project
    ⏱️ Working → Log Time
    💰 Month end → Generate Invoice
    """)

st.markdown("---")
st.markdown("### 💡 **Remember: The system enforces business discipline. Win the deal first, then create the project. This ensures every hour you track has been sold and has clear business value.**")