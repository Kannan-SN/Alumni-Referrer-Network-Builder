import streamlit as st
import asyncio
from streamlit_option_menu import option_menu
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import all components
from config.settings import settings
from ui.components import UIComponents
from ui.pages.dashboard import DashboardPage
from ui.pages.student_profile import StudentProfilePage
from ui.pages.alumni_search import AlumniSearchPage
from ui.pages.referral_requests import ReferralRequestsPage
from utils.data_initialization import data_initializer

# Page configuration
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

async def initialize_app():
    """Initialize the application with data checks"""
    if "app_initialized" not in st.session_state:
        with st.spinner("Initializing Alumni Referrer Network..."):
            try:
                # Check if data exists
                data_status = await data_initializer.check_data_exists()
                
                if not data_status['data_exists']:
                    st.info("Setting up the system for first time use...")
                    
                    # Initialize sample data
                    init_success = await data_initializer.initialize_sample_data()
                    
                    if init_success:
                        st.success("✅ System initialized successfully!")
                    else:
                        st.warning("⚠️ System initialization completed with some issues. You can still use the app.")
                
                st.session_state.app_initialized = True
                st.session_state.data_status = data_status
                
            except Exception as e:
                st.error(f"❌ Failed to initialize app: {str(e)}")
                st.session_state.app_initialized = False

def render_sidebar():
    """Render enhanced sidebar with navigation and stats"""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/white?text=Alumni+Network", width=200)
        st.markdown("---")
        
        # Navigation menu
        selected = option_menu(
            menu_title="Navigation",
            options=["Dashboard", "Student Profile", "Alumni Search", "Referral Requests", "Analytics"],
            icons=["house", "person", "search", "envelope", "graph-up"],
            menu_icon="compass",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#1f77b4", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#1f77b4"},
            }
        )
        
        st.markdown("---")
        
        # Quick stats
        if st.session_state.get("app_initialized"):
            st.subheader("📊 Quick Stats")
            data_status = st.session_state.get("data_status", {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Alumni", data_status.get('mongodb_count', 0))
            with col2:
                st.metric("Vector DB", data_status.get('vector_store_count', 0))
            
            # Student profile status
            profile_exists = "student_profile" in st.session_state
            status_icon = "✅" if profile_exists else "❌"
            st.write(f"{status_icon} Profile: {'Complete' if profile_exists else 'Missing'}")
        
        st.markdown("---")
        
        # Help section
        with st.expander("ℹ️ How to Use"):
            st.markdown("""
            **Getting Started:**
            1. Create your student profile
            2. Search for alumni by company/domain
            3. Generate referral paths
            4. Create personalized messages
            
            **Tips:**
            - Be specific in your search criteria
            - Complete your profile for better matches
            - Personalize messages before sending
            """)
        
        # System status
        with st.expander("🔧 System Status"):
            if st.session_state.get("app_initialized"):
                st.success("✅ System Online")
                st.write("• MongoDB: Connected")
                st.write("• Vector Store: Ready")
                st.write("• AI Agents: Active")
            else:
                st.error("❌ System Issues")
        
        return selected

async def main():
    """Main application function"""
    # Initialize app
    await initialize_app()
    
    if not st.session_state.get("app_initialized"):
        st.error("Failed to initialize the application. Please refresh the page.")
        return
    
    # Render header
    st.title("🎓 Alumni Referrer Network Builder")
    st.markdown("*AI-powered platform to connect students with alumni for job referrals*")
    st.markdown("---")
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Route to appropriate page
    try:
        if selected_page == "Dashboard":
            await DashboardPage.render()
        elif selected_page == "Student Profile":
            await StudentProfilePage.render()
        elif selected_page == "Alumni Search":
            await AlumniSearchPage.render()
        elif selected_page == "Referral Requests":
            await ReferralRequestsPage.render()
        elif selected_page == "Analytics":
            UIComponents.render_analytics_dashboard()
    
    except Exception as e:
        st.error(f"❌ Error rendering page: {str(e)}")
        if settings.DEBUG:
            st.exception(e)

# Custom CSS for better styling
def load_custom_css():
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stAlert > div {
        border-radius: 10px;
    }
    
    .stButton > button {
        border-radius: 20px;
        border: none;
        background: linear-gradient(45deg, #1f77b4, #ff7f0e);
        color: white;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .stExpander > div > div {
        border-radius: 10px;
    }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .stSelectbox > div > div {
        border-radius: 10px;
    }
    
    .stTextInput > div > div {
        border-radius: 10px;
    }
    
    .stTextArea > div > div {
        border-radius: 10px;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(45deg, #1f77b4, #ff7f0e);
        border-radius: 10px;
    }
    
    /* Success message styling */
    .element-container:has(.stSuccess) {
        animation: slideIn 0.5s ease-in;
    }
    
    @keyframes slideIn {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Hide Streamlit style */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# Run the application
if __name__ == "__main__":
    load_custom_css()
    
    # Create event loop for async functions
    try:
        asyncio.run(main())
    except Exception as e:
        st.error(f"Application failed to start: {str(e)}")
        if settings.DEBUG:
            st.exception(e)