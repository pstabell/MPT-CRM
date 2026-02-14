"""
Mobile-responsive CSS styles for MPT-CRM
Provides comprehensive mobile UI improvements
"""

import streamlit as st

def inject_mobile_styles():
    """Inject mobile-friendly CSS styles for better responsive design"""
    st.markdown("""
    <style>
    /* Mobile-first responsive design */
    
    /* Base mobile styles */
    @media (max-width: 768px) {
        /* Hide the default Streamlit sidebar on mobile */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        
        /* Main content should use full width on mobile */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Improve button spacing and touch targets */
        .stButton button {
            min-height: 44px !important;
            padding: 12px 20px !important;
            font-size: 16px !important;
            width: 100% !important;
        }
        
        /* Mobile-friendly metrics display */
        [data-testid="metric-container"] {
            border: 1px solid rgba(255,255,255,0.1) !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            margin-bottom: 1rem !important;
        }
        
        /* Stack columns vertically on mobile */
        .stColumns > div {
            min-width: 100% !important;
            margin-bottom: 1rem !important;
        }
        
        /* Mobile-friendly forms */
        .stSelectbox, .stTextInput, .stTextArea, .stNumberInput {
            margin-bottom: 1rem !important;
        }
        
        .stSelectbox > div > div, 
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {
            min-height: 44px !important;
            font-size: 16px !important;
            padding: 12px !important;
        }
        
        /* Mobile-friendly containers */
        div[data-testid="stContainer"] {
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 8px !important;
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }
        
        /* Mobile-friendly expanders */
        .streamlit-expanderHeader {
            font-size: 18px !important;
            padding: 1rem !important;
        }
        
        /* Mobile table improvements */
        .dataframe {
            font-size: 12px !important;
        }
        
        .dataframe th, .dataframe td {
            padding: 8px 4px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        
        /* Mobile-friendly navigation replacement */
        .mobile-nav-header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            padding: 1rem;
            margin: -1rem -1rem 1rem -1rem;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .mobile-nav-title {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .mobile-nav-subtitle {
            color: rgba(255,255,255,0.7);
            font-size: 0.9rem;
        }
        
        /* Mobile menu button */
        .mobile-menu-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: #1a1a2e;
            color: white;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 10px;
            font-size: 18px;
            cursor: pointer;
        }
    }
    
    /* Tablet styles */
    @media (min-width: 769px) and (max-width: 1024px) {
        section[data-testid="stSidebar"] {
            width: 280px !important;
        }
        
        .main .block-container {
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
    }
    
    /* Desktop styles */
    @media (min-width: 1025px) {
        section[data-testid="stSidebar"] {
            width: 320px !important;
        }
    }
    
    /* Responsive images */
    @media (max-width: 768px) {
        img {
            max-width: 100% !important;
            height: auto !important;
        }
    }
    
    /* Mobile-friendly data tables */
    @media (max-width: 768px) {
        .stDataFrame {
            overflow-x: auto !important;
            display: block !important;
            white-space: nowrap !important;
        }
        
        .stDataFrame table {
            min-width: 600px !important;
        }
    }
    
    /* Touch-friendly elements */
    @media (max-width: 768px) {
        .stRadio > div {
            flex-direction: column !important;
        }
        
        .stRadio > div > label {
            margin-bottom: 0.5rem !important;
            padding: 0.75rem !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 6px !important;
        }
        
        .stCheckbox > label {
            padding: 0.75rem !important;
        }
        
        .stSelectbox label, .stTextInput label {
            font-size: 16px !important;
            font-weight: 500 !important;
            margin-bottom: 0.5rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_mobile_navigation(current_page="Dashboard"):
    """Render mobile-friendly navigation header"""
    
    # Page configuration for navigation
    PAGE_CONFIG = {
        "Dashboard": {"icon": "📊", "description": "Overview and quick stats"},
        "Discovery Call": {"icon": "📞", "description": "Discovery calls and intake"},  
        "Companies": {"icon": "🏢", "description": "Company management"},
        "Contacts": {"icon": "👥", "description": "Contact management"},
        "Sales Pipeline": {"icon": "📈", "description": "Deal tracking"},
        "Projects": {"icon": "📁", "description": "Project management"},
        "Service": {"icon": "🔧", "description": "Service requests"},
        "Tasks": {"icon": "✅", "description": "Task management"},
        "Time & Billing": {"icon": "💰", "description": "Time tracking"},
        "Marketing": {"icon": "📧", "description": "Email campaigns"},
        "Reports": {"icon": "📊", "description": "Analytics and reports"},
        "Settings": {"icon": "⚙️", "description": "App settings"},
        "Help": {"icon": "❓", "description": "Help and support"},
    }
    
    config = PAGE_CONFIG.get(current_page, {"icon": "📊", "description": "MPT-CRM"})
    
    # Mobile navigation header
    st.markdown(f"""
    <div class="mobile-nav-header">
        <div class="mobile-nav-title">
            {config['icon']} {current_page}
        </div>
        <div class="mobile-nav-subtitle">
            {config['description']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mobile navigation menu in expander
    with st.expander("🧭 Navigation Menu", expanded=False):
        st.markdown("**Quick Navigation:**")
        
        cols = st.columns(2)
        pages = list(PAGE_CONFIG.items())
        
        for i, (page_name, page_config) in enumerate(pages):
            col = cols[i % 2]
            with col:
                if page_name == current_page:
                    st.success(f"{page_config['icon']} **{page_name}** (current)")
                else:
                    if st.button(f"{page_config['icon']} {page_name}", key=f"nav_{page_name}", use_container_width=True):
                        # Navigation logic would go here
                        st.info(f"Navigate to {page_name}")

def mobile_container(title, content_func, **kwargs):
    """Create a mobile-friendly container with consistent styling"""
    with st.container():
        st.markdown(f"### {title}")
        content_func(**kwargs)
        
def mobile_metrics_grid(metrics_data):
    """Display metrics in a mobile-friendly grid"""
    # On mobile, show metrics in a single column
    # On desktop, show in rows
    
    for label, value in metrics_data.items():
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"**{label}:**")
        with col2:
            st.markdown(f"**{value}**")

def mobile_data_table(df, title=None, searchable=True, **kwargs):
    """Display data table with mobile-friendly options"""
    if title:
        st.markdown(f"### {title}")
    
    if searchable and not df.empty:
        # Add search functionality
        search_term = st.text_input("🔍 Search", placeholder="Type to filter...", key=f"search_{title}")
        if search_term:
            # Simple text search across all columns
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            df = df[mask]
    
    if df.empty:
        st.info("No data to display")
    else:
        # Use responsive table display
        with st.expander(f"📋 View Data ({len(df)} items)", expanded=True):
            st.dataframe(df, use_container_width=True, **kwargs)

def mobile_form_section(title, fields_func, submit_text="Submit"):
    """Create a mobile-friendly form section"""
    with st.expander(f"📝 {title}", expanded=False):
        with st.form(f"form_{title.lower().replace(' ', '_')}"):
            fields_func()
            submitted = st.form_submit_button(submit_text, use_container_width=True)
            return submitted