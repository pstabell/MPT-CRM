"""
Shared navigation component for MPT-CRM
Provides consistent sidebar across all pages
"""
import streamlit as st
from pathlib import Path

# CSS to hide Streamlit's default multi-page navigation
HIDE_STREAMLIT_NAV = """
<style>
    /* Hide the default Streamlit page navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Sidebar styling */
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

    /* Make metric labels white */
    section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: rgba(255,255,255,0.7) !important;
    }

    section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: white !important;
    }
</style>
"""

def render_sidebar(current_page: str = "Dashboard"):
    """Render the consistent sidebar navigation with logo"""

    # Inject CSS to hide default nav
    st.markdown(HIDE_STREAMLIT_NAV, unsafe_allow_html=True)

    # Page mapping with paths
    PAGE_CONFIG = {
        "Dashboard": {"icon": "📊", "path": "app.py"},
        "Contacts": {"icon": "👥", "path": "pages/02_Contacts.py"},
        "Sales Pipeline": {"icon": "🎯", "path": "pages/03_Pipeline.py"},
        "Projects": {"icon": "📁", "path": "pages/04_Projects.py"},
        "Tasks": {"icon": "✅", "path": "pages/05_Tasks.py"},
        "Time & Billing": {"icon": "💰", "path": "pages/06_Time_Billing.py"},
        "Marketing": {"icon": "📧", "path": "pages/07_Marketing.py"},
        "Reports": {"icon": "📈", "path": "pages/08_Reports.py"},
        "Settings": {"icon": "⚙️", "path": "pages/09_Settings.py"},
    }

    with st.sidebar:
        # Logo at the top
        logo_path = Path(__file__).parent.parent / "assets" / "MetroPointTechnology-Logo.jpg"
        if logo_path.exists():
            st.image(str(logo_path))
        else:
            st.markdown("""
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <div style="color: white; font-size: 18px; font-weight: 600;">Metro Point</div>
                <div style="color: rgba(255,255,255,0.6); font-size: 12px;">Technology</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Build page list with icons
        pages = [f"{config['icon']} {name}" for name, config in PAGE_CONFIG.items()]

        # Find current index
        current_index = 0
        for i, (name, config) in enumerate(PAGE_CONFIG.items()):
            if name == current_page:
                current_index = i
                break

        selected = st.radio("Navigation", pages, index=current_index, label_visibility="collapsed")

        # Handle navigation
        selected_name = selected.split(" ", 1)[1] if " " in selected else selected
        if selected_name != current_page:
            config = PAGE_CONFIG.get(selected_name)
            if config and config['path']:
                st.switch_page(config['path'])
            elif config and config['path'] is None:
                st.info(f"{selected_name} coming soon!")

        st.markdown("---")

        return selected_name


def render_sidebar_stats(stats: dict = None):
    """Render quick stats in sidebar"""
    with st.sidebar:
        st.markdown("#### Quick Stats")

        if stats:
            for label, value in stats.items():
                st.metric(label, value)
        else:
            st.caption("No stats available")
