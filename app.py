import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
from typing import Dict, List, Any

# Import our modules
from config import Config
from backend.database import db_manager
from backend.vector_store import VectorStore
from backend.rag_engine import RAGEngine
from models.alumni import Alumni
from models.student import Student
from utils.data_loader import DataLoader
from frontend.ui_components import UIComponents

# Page config
st.set_page_config(
    page_title="Alumni Referrer Network Builder",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize all components"""
    config = Config()
    vector_store = VectorStore()
    rag_engine = RAGEngine()
    ui_components = UIComponents()
    data_loader = DataLoader()
    
    return config, vector_store, rag_engine, ui_components, data_loader

config, vector_store, rag_engine, ui_components, data_loader = initialize_components()

# Session state initialization
if 'current_student' not in st.session_state:
    st.session_state.current_student = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'selected_alumni' not in st.session_state:
    st.session_state.selected_alumni = None

def main():
    """Main application"""
    
    # App header
    st.title("🎓 Alumni Referrer Network Builder")
    st.markdown("Find the perfect alumni connections for job referrals using AI-powered matching")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page:",
            [
                "🏠 Home",
                "👤 Student Profile", 
                "🔍 Find Alumni",
                "📊 Referral Analysis",
                "✉️ Generate Email",
                "📈 Analytics",
                "⚙️ Admin"
            ]
        )
    
    # Route to appropriate page
    if page == "🏠 Home":
        show_home_page()
    elif page == "👤 Student Profile":
        show_student_profile_page()
    elif page == "🔍 Find Alumni":
        show_alumni_search_page()
    elif page == "📊 Referral Analysis":
        show_referral_analysis_page()
    elif page == "✉️ Generate Email":
        show_email_generation_page()
    elif page == "📈 Analytics":
        show_analytics_page()
    elif page == "⚙️ Admin":
        show_admin_page()

def show_home_page():
    """Home page with overview and quick actions"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Welcome to Alumni Referrer Network")
        
        st.markdown("""
        ### 🎯 What This Tool Does
        
        **Find Perfect Alumni Matches**: Uses AI to match students with alumni based on:
        - Skills and interests alignment
        - Target companies and roles
        - Career trajectories and experience
        - Response likelihood and referral success rates
        
        **Intelligent Referral Paths**: Analyzes connection strength and suggests:
        - Optimal outreach strategies
        - Best timing for contact
        - Key talking points and common ground
        - Success probability assessments
        
        **AI-Generated Outreach**: Creates personalized emails that:
        - Highlight relevant connections
        - Show genuine interest and research
        - Make clear, respectful asks
        - Maximize response probability
        """)
        
        # Quick stats
        stats = db_manager.get_database_stats()
        
        st.subheader("📊 Network Overview")
        col1a, col1b, col1c, col1d = st.columns(4)
        
        with col1a:
            st.metric("Total Alumni", stats.get('total_alumni', 0))
        with col1b:
            st.metric("Active Students", stats.get('total_students', 0))
        with col1c:
            st.metric("Successful Referrals", stats.get('total_referrals', 0))
        with col1d:
            st.metric("Companies Covered", len(stats.get('top_companies', [])))
    
    with col2:
        st.header("🚀 Quick Start")
        
        # Quick actions
        if st.button("👤 Create Student Profile", use_container_width=True):
            st.session_state.page = "👤 Student Profile"
            st.rerun()
        
        if st.button("🔍 Search Alumni Network", use_container_width=True):
            st.session_state.page = "🔍 Find Alumni"
            st.rerun()
        
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = "📈 Analytics"
            st.rerun()
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        
        # Top companies chart
        if stats.get('top_companies'):
            companies_df = pd.DataFrame(stats['top_companies'])
            if not companies_df.empty and '_id' in companies_df.columns:
                fig = px.bar(
                    companies_df.head(5), 
                    x='count', 
                    y='_id',
                    orientation='h',
                    title="Top Alumni Companies"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

def show_student_profile_page():
    """Student profile creation and management page"""
    
    st.header("👤 Student Profile Management")
    
    # Profile selection/creation
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Load Existing Profile")
        
        # Get existing students
        existing_students = []  # You'd load this from database
        
        selected_email = st.selectbox(
            "Select existing student:",
            ["Create New Profile"] + [s.get('email', '') for s in existing_students],
            key="student_selector"
        )
        
        if selected_email != "Create New Profile":
            student = db_manager.get_student_by_email(selected_email)
            if student:
                st.session_state.current_student = student
                st.success(f"Loaded profile for {student.name}")
    
    with col2:
        st.subheader("Quick Profile Creation")
        
        if st.button("Load Sample Profile", use_container_width=True):
            # Load a sample student profile for demo
            sample_student = create_sample_student()
            st.session_state.current_student = sample_student
            st.success("Sample profile loaded!")
    
    # Profile form
    st.subheader("Student Information")
    
    with st.form("student_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name", value=st.session_state.current_student.name if st.session_state.current_student else "")
            email = st.text_input("Email", value=st.session_state.current_student.email if st.session_state.current_student else "")
            current_year = st.selectbox("Current Year", [1, 2, 3, 4, 5], 
                                      index=2 if not st.session_state.current_student else st.session_state.current_student.current_year - 1)
            degree = st.text_input("Degree", value=st.session_state.current_student.degree if st.session_state.current_student else "")
            department = st.selectbox("Department", 
                                    ["Computer Science", "Electrical Engineering", "Mechanical Engineering", 
                                     "Business Administration", "Data Science", "Information Technology", "Other"],
                                    index=0 if not st.session_state.current_student else 0)
            cgpa = st.number_input("CGPA", min_value=0.0, max_value=10.0, value=8.0, step=0.1)
        
        with col2:
            linkedin_url = st.text_input("LinkedIn URL", value=st.session_state.current_student.linkedin_url if st.session_state.current_student else "")
            github_url = st.text_input("GitHub URL", value=st.session_state.current_student.github_url if st.session_state.current_student else "")
            phone = st.text_input("Phone", value=st.session_state.current_student.phone if st.session_state.current_student else "")
            graduation_date = st.date_input("Expected Graduation", value=datetime(2025, 6, 1))
            job_search_status = st.selectbox("Job Search Status", ["active", "passive", "not_looking"])
        
        # Skills and interests
        st.subheader("Skills & Interests")
        
        col3, col4 = st.columns(2)
        with col3:
            skills_input = st.text_area("Skills (one per line)", 
                                      value="\n".join(st.session_state.current_student.skills) if st.session_state.current_student else "",
                                      height=100)
            interests_input = st.text_area("Interests (one per line)", 
                                         value="\n".join(st.session_state.current_student.interests) if st.session_state.current_student else "",
                                         height=100)
        
        with col4:
            target_companies_input = st.text_area("Target Companies (one per line)", 
                                                value="\n".join(st.session_state.current_student.target_companies) if st.session_state.current_student else "",
                                                height=100)
            target_roles_input = st.text_area("Target Roles (one per line)", 
                                            value="\n".join(st.session_state.current_student.target_roles) if st.session_state.current_student else "",
                                            height=100)
        
        # Bio
        bio = st.text_area("Bio/Summary", 
                          value=st.session_state.current_student.bio if st.session_state.current_student else "",
                          height=100)
        
        # Submit button
        submitted = st.form_submit_button("Save Profile", use_container_width=True)
        
        if submitted and name and email:
            # Create student object
            student = Student(
                id=email.replace("@", "_").replace(".", "_"),
                name=name,
                current_year=current_year,
                degree=degree,
                department=department,
                cgpa=cgpa,
                email=email,
                linkedin_url=linkedin_url,
                github_url=github_url,
                phone=phone,
                skills=[s.strip() for s in skills_input.split('\n') if s.strip()],
                interests=[i.strip() for i in interests_input.split('\n') if i.strip()],
                target_companies=[c.strip() for c in target_companies_input.split('\n') if c.strip()],
                target_roles=[r.strip() for r in target_roles_input.split('\n') if r.strip()],
                bio=bio,
                graduation_date=datetime.combine(graduation_date, datetime.min.time()),
                job_search_status=job_search_status
            )
            
            # Save to database
            try:
                db_manager.insert_student(student)
                st.session_state.current_student = student
                st.success("✅ Profile saved successfully!")
            except Exception as e:
                st.error(f"Error saving profile: {e}")

def show_alumni_search_page():
    """Alumni search and matching page"""
    
    st.header("🔍 Find Alumni Connections")
    
    # Check if student profile exists
    if not st.session_state.current_student:
        st.warning("⚠️ Please create a student profile first to get personalized recommendations.")
        if st.button("Create Profile"):
            st.session_state.page = "👤 Student Profile"
            st.rerun()
        return
    
    student = st.session_state.current_student
    
    # Search interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Search Parameters")
        
        # Search query
        search_query = st.text_input(
            "Search Query", 
            value=" ".join(student.skills[:3] + student.target_companies[:2]),
            help="Enter skills, companies, or roles you're interested in"
        )
        
        # Filters
        with st.expander("Advanced Filters"):
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                filter_companies = st.multiselect(
                    "Filter by Companies",
                    options=["Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla", "Zoho", "TCS", "Infosys"],
                    default=student.target_companies[:3] if student.target_companies else []
                )
                
                filter_departments = st.selectbox(
                    "Filter by Department", 
                    ["All", "Computer Science", "Electrical Engineering", "Mechanical Engineering", "Business", "Data Science"]
                )
            
            with col_f2:
                min_grad_year = st.number_input("Min Graduation Year", min_value=2010, max_value=2025, value=2015)
                max_grad_year = st.number_input("Max Graduation Year", min_value=2010, max_value=2025, value=2024)
                
                min_response_rate = st.slider("Min Response Rate", 0.0, 1.0, 0.3, 0.1)
                hiring_authority = st.checkbox("Has Hiring Authority")
        
        # Search button
        if st.button("🔍 Search Alumni Network", use_container_width=True):
            with st.spinner("Searching alumni network..."):
                # Build filters
                filters = {}
                if filter_companies:
                    filters['companies'] = filter_companies
                if filter_departments != "All":
                    filters['department'] = filter_departments
                filters['min_graduation_year'] = min_grad_year
                filters['max_graduation_year'] = max_grad_year
                filters['min_response_rate'] = min_response_rate
                if hiring_authority:
                    filters['hiring_authority'] = True
                
                # Perform search
                results = rag_engine.find_best_alumni_matches(
                    student=student,
                    query=search_query,
                    filters=filters
                )
                
                st.session_state.search_results = results
                st.success(f"Found {len(results['alumni_matches'])} potential matches!")
    
    with col2:
        st.subheader("Your Profile Summary")
        
        st.info(f"""
        **Name:** {student.name}  
        **Department:** {student.department}  
        **Year:** {student.current_year}  
        **CGPA:** {student.cgpa}
        
        **Top Skills:** {', '.join(student.skills[:3])}  
        **Target Companies:** {', '.join(student.target_companies[:3])}  
        **Target Roles:** {', '.join(student.target_roles[:2])}
        """)
    
    # Display search results
    if st.session_state.search_results:
        display_search_results(st.session_state.search_results)

def display_search_results(results: Dict[str, Any]):
    """Display alumni search results"""
    
    st.subheader("🎯 Alumni Matches")
    
    # AI Analysis
    if results.get('llm_analysis'):
        with st.expander("🤖 AI Analysis & Recommendations", expanded=True):
            st.markdown(results['llm_analysis'])
    
    # Results table
    alumni_matches = results['alumni_matches']
    
    if not alumni_matches:
        st.warning("No matches found. Try adjusting your search criteria.")
        return
    
    # Create DataFrame for display
    display_data = []
    for i, match in enumerate(alumni_matches):
        metadata = match['metadata']
        scores = match.get('enhanced_scores', {})
        
        display_data.append({
            'Rank': i + 1,
            'Name': metadata.get('name', 'Unknown'),
            'Company': metadata.get('current_company', 'Unknown'),
            'Position': metadata.get('current_position', 'Unknown'),
            'Department': metadata.get('department', 'Unknown'),
            'Grad Year': metadata.get('graduation_year', 'Unknown'),
            'Match Score': f"{match.get('composite_score', 0):.2f}",
            'Response Rate': f"{metadata.get('response_rate', 0):.1%}",
            'Hiring Authority': '✅' if metadata.get('hiring_authority', False) else '❌',
            'Skills': ', '.join(metadata.get('skills', [])[:3]),
        })
    
    df = pd.DataFrame(display_data)
    
    # Display interactive table
    st.dataframe(
        df,
        use_container_width=True,
        height=400,
        column_config={
            "Match Score": st.column_config.ProgressColumn(
                "Match Score",
                help="Overall compatibility score",
                min_value=0,
                max_value=1,
            ),
            "Response Rate": st.column_config.ProgressColumn(
                "Response Rate",
                help="Historical response rate",
                min_value=0,
                max_value=1,
            ),
        }
    )
    
    # Detailed cards for top matches
    st.subheader("📋 Detailed Profiles")
    
    for i, match in enumerate(alumni_matches[:3]):  # Show top 3
        with st.expander(f"#{i+1}: {match['metadata']['name']} - {match['metadata']['current_company']}", expanded=i==0):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                metadata = match['metadata']
                st.markdown(f"""
                **Position:** {metadata.get('current_position', 'Unknown')}  
                **Department:** {metadata.get('department', 'Unknown')}  
                **Graduation Year:** {metadata.get('graduation_year', 'Unknown')}  
                **Location:** {metadata.get('location', 'Unknown')}  
                **Seniority:** {metadata.get('seniority_level', 'Unknown')}
                """)
            
            with col2:
                st.markdown("**Skills:**")
                skills = metadata.get('skills', [])
                for skill in skills[:6]:
                    st.markdown(f"• {skill}")
                
                if metadata.get('linkedin_url'):
                    st.markdown(f"🔗 [LinkedIn Profile]({metadata['linkedin_url']})")
            
            with col3:
                scores = match.get('enhanced_scores', {})
                st.metric("Match Score", f"{match.get('composite_score', 0):.2f}")
                st.metric("Response Rate", f"{metadata.get('response_rate', 0):.1%}")
                
                if st.button(f"Analyze Path #{i+1}", key=f"analyze_{i}"):
                    st.session_state.selected_alumni = match
                    st.session_state.page = "📊 Referral Analysis"
                    st.rerun()
                
                if st.button(f"Generate Email #{i+1}", key=f"email_{i}"):
                    st.session_state.selected_alumni = match
                    st.session_state.page = "✉️ Generate Email"
                    st.rerun()

def show_referral_analysis_page():
    """Referral path analysis page"""
    
    st.header("📊 Referral Path Analysis")
    
    if not st.session_state.current_student:
        st.warning("Please create a student profile first.")
        return
    
    if not st.session_state.selected_alumni:
        st.warning("Please select an alumni from the search results first.")
        return
    
    student = st.session_state.current_student
    alumni = st.session_state.selected_alumni
    
    # Alumni overview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Analysis for {alumni['metadata']['name']}")
        st.info(f"""
        **Company:** {alumni['metadata']['current_company']}  
        **Position:** {alumni['metadata']['current_position']}  
        **Department:** {alumni['metadata']['department']}  
        **Match Score:** {alumni.get('composite_score', 0):.2f}
        """)
    
    with col2:
        if st.button("🔄 Run Fresh Analysis"):
            with st.spinner("Analyzing referral path..."):
                analysis = rag_engine.analyze_referral_path(
                    student=student,
                    alumni=alumni,
                    context="Detailed referral path analysis requested by user"
                )
                st.session_state.referral_analysis = analysis
    
    # Analysis results
    if 'referral_analysis' in st.session_state:
        analysis = st.session_state.referral_analysis
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Connection Strength", f"{analysis['connection_strength']:.2f}")
        with col2:
            st.metric("Success Probability", f"{analysis['success_probability']:.2f}")
        with col3:
            response_rate = alumni['metadata'].get('response_rate', 0)
            st.metric("Response Rate", f"{response_rate:.1%}")
        with col4:
            hiring_auth = alumni['metadata'].get('hiring_authority', False)
            st.metric("Hiring Authority", "Yes" if hiring_auth else "No")
        
        # Detailed analysis
        st.subheader("🤖 AI Analysis")
        st.markdown(analysis['detailed_analysis'])
        
        # Timeline and talking points
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⏰ Recommended Timeline")
            timeline = analysis['recommended_timeline']
            for phase, timing in timeline.items():
                st.markdown(f"**{phase.replace('_', ' ').title()}:** {timing}")
        
        with col2:
            st.subheader("💬 Key Talking Points")
            talking_points = analysis['key_talking_points']
            for point in talking_points:
                st.markdown(f"• {point}")
    
    else:
        # Run initial analysis
        with st.spinner("Analyzing referral path..."):
            analysis = rag_engine.analyze_referral_path(
                student=student,
                alumni=alumni,
                context="Initial referral path analysis"
            )
            st.session_state.referral_analysis = analysis
            st.rerun()

def show_email_generation_page():
    """Email generation page"""
    
    st.header("✉️ Generate Referral Email")
    
    if not st.session_state.current_student:
        st.warning("Please create a student profile first.")
        return
    
    if not st.session_state.selected_alumni:
        st.warning("Please select an alumni from the search results first.")
        return
    
    student = st.session_state.current_student
    alumni = st.session_state.selected_alumni
    
    # Email configuration
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Email Configuration")
        
        target_company = st.text_input(
            "Target Company", 
            value=alumni['metadata']['current_company']
        )
        
        target_role = st.text_input(
            "Target Role", 
            value=student.target_roles[0] if student.target_roles else "Software Engineer"
        )
        
        email_type = st.selectbox(
            "Email Style",
            ["initial_outreach", "formal", "casual", "story_driven"],
            help="Choose the tone and style of the email"
        )
        
        additional_context = st.text_area(
            "Additional Context",
            help="Any specific information you want to include",
            height=100
        )
        
        if st.button("✨ Generate Email", use_container_width=True):
            with st.spinner("Generating personalized email..."):
                email_result = rag_engine.generate_referral_email(
                    student=student,
                    alumni=alumni,
                    target_company=target_company,
                    target_role=target_role,
                    email_type=email_type,
                    context=additional_context
                )
                st.session_state.email_result = email_result
    
    with col2:
        st.subheader("Alumni Summary")
        metadata = alumni['metadata']
        st.info(f"""
        **Name:** {metadata['name']}  
        **Company:** {metadata['current_company']}  
        **Position:** {metadata['current_position']}  
        **Response Rate:** {metadata.get('response_rate', 0):.1%}  
        **LinkedIn:** {'Available' if metadata.get('linkedin_url') else 'Not available'}
        """)
    
    # Display generated email
    if 'email_result' in st.session_state:
        email_result = st.session_state.email_result
        
        st.subheader("📧 Generated Email")
        
        # Email metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Personalization Score", f"{email_result['personalization_score']:.2f}")
        with col2:
            recommendations = email_result['send_recommendations']
            st.metric("Best Platform", recommendations['platform'])
        with col3:
            st.metric("Best Time", recommendations['best_time'])
        
        # Email content
        st.markdown("### Email Content")
        email_content = email_result['email_content']
        
        # Make it copyable
        st.text_area(
            "Copy this email:",
            value=email_content,
            height=400,
            help="Select all and copy to use in your email client"
        )
        
        # Send recommendations
        st.subheader("📋 Sending Recommendations")
        recommendations = email_result['send_recommendations']
        
        for tip in recommendations['tips']:
            st.markdown(f"• {tip}")
        
        st.markdown(f"**Follow-up Strategy:** {recommendations['follow_up_strategy']}")
        
        # Generate variations
        if st.button("🔄 Generate Alternative Versions"):
            with st.spinner("Generating email variations..."):
                variations = rag_engine.generate_multiple_email_variations(
                    student=student,
                    alumni=alumni,
                    target_company=target_company,
                    target_role=target_role,
                    num_variations=3
                )
                st.session_state.email_variations = variations
        
        # Display variations
        if 'email_variations' in st.session_state:
            st.subheader("📝 Alternative Versions")
            
            for i, variation in enumerate(st.session_state.email_variations):
                with st.expander(f"Version {i+1}: {variation['variation_type'].title()}", expanded=False):
                    st.text_area(
                        f"Email Version {i+1}:",
                        value=variation['email_content'],
                        height=300,
                        key=f"variation_{i}"
                    )

def show_analytics_page():
    """Analytics and insights page"""
    
    st.header("📈 Network Analytics")
    
    # Get database stats
    stats = db_manager.get_database_stats()
    vector_stats = vector_store.get_collection_stats()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Alumni", stats.get('total_alumni', 0))
    with col2:
        st.metric("Active Students", stats.get('total_students', 0))
    with col3:
        st.metric("Total Referrals", stats.get('total_referrals', 0))
    with col4:
        st.metric("Success Rate", "67%")  # This would be calculated from actual data
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Company distribution
        if stats.get('top_companies'):
            st.subheader("Top Alumni Companies")
            companies_df = pd.DataFrame(stats['top_companies'])
            if not companies_df.empty:
                fig = px.bar(
                    companies_df.head(10),
                    x='count',
                    y='_id',
                    orientation='h',
                    title="Alumni by Company"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Graduation year distribution
        if stats.get('graduation_years'):
            st.subheader("Alumni by Graduation Year")
            years_df = pd.DataFrame(stats['graduation_years'])
            if not years_df.empty:
                fig = px.bar(
                    years_df,
                    x='_id',
                    y='count',
                    title="Alumni Distribution by Year"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

def show_admin_page():
    """Admin page for data management"""
    
    st.header("⚙️ Admin Panel")
    
    # Data management
    st.subheader("📊 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Alumni Data")
        
        # Upload alumni data
        uploaded_file = st.file_uploader(
            "Upload Alumni CSV",
            type=['csv'],
            help="Upload a CSV file with alumni information"
        )
        
        if uploaded_file and st.button("Process Alumni Data"):
            try:
                df = pd.read_csv(uploaded_file)
                
                # Convert to Alumni objects and insert
                alumni_list = []
                for _, row in df.iterrows():
                    alumni = Alumni(
                        id=str(row.get('id', f"alumni_{len(alumni_list)}")),
                        name=str(row.get('name', '')),
                        graduation_year=int(row.get('graduation_year', 2020)),
                        degree=str(row.get('degree', '')),
                        department=str(row.get('department', '')),
                        current_company=str(row.get('current_company', '')),
                        current_position=str(row.get('current_position', '')),
                        skills=str(row.get('skills', '')).split(',') if row.get('skills') else [],
                        location=str(row.get('location', '')),
                        industry=str(row.get('industry', '')),
                        response_rate=float(row.get('response_rate', 0.5))
                    )
                    alumni_list.append(alumni)
                
                # Bulk insert
                success = vector_store.bulk_add_alumni(alumni_list)
                
                if success:
                    st.success(f"✅ Successfully added {len(alumni_list)} alumni profiles!")
                else:
                    st.error("❌ Error adding alumni profiles")
                    
            except Exception as e:
                st.error(f"Error processing file: {e}")
    
    with col2:
        st.markdown("### System Status")
        
        # Database stats
        db_stats = db_manager.get_database_stats()
        
        st.json(db_stats)
        
        # System controls
        if st.button("🔄 Rebuild Vector Index"):
            with st.spinner("Rebuilding vector index..."):
                vector_store._rebuild_index()
                st.success("Vector index rebuilt!")
        
        if st.button("⚠️ Reset All Data", type="secondary"):
            if st.checkbox("I understand this will delete all data"):
                vector_store.reset_collection()
                st.warning("All data has been reset!")

def create_sample_student():
    """Create a sample student for demo purposes"""
    return Student(
        id="john_doe_example",
        name="John Doe",
        current_year=3,
        degree="Bachelor of Technology",
        department="Computer Science",
        cgpa=8.5,
        email="john.doe@example.com",
        linkedin_url="https://linkedin.com/in/johndoe",
        github_url="https://github.com/johndoe",
        skills=["Python", "Machine Learning", "React", "Node.js", "SQL", "Docker"],
        interests=["AI/ML", "Web Development", "Data Science", "Cloud Computing"],
        target_companies=["Google", "Microsoft", "Amazon", "Meta", "Netflix"],
        target_roles=["Software Engineer", "ML Engineer", "Full Stack Developer"],
        preferred_locations=["Bangalore", "San Francisco", "Remote"],
        bio="Passionate computer science student with experience in full-stack development and machine learning. Looking for opportunities to work on impactful products.",
        graduation_date=datetime(2025, 6, 1),
        job_search_status="active"
    )

if __name__ == "__main__":
    main()