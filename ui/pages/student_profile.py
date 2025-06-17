import streamlit as st
from ui.components import UIComponents
from database.mongodb_handler import mongodb_handler
from utils.validators import InputValidator
import asyncio

class StudentProfilePage:
    @staticmethod
    async def render():
        """Render the student profile page"""
        st.header("👤 Student Profile Management")
        
        # Check if profile exists
        profile_exists = "student_profile" in st.session_state and st.session_state.student_profile
        
        if profile_exists:
            StudentProfilePage._render_existing_profile()
        else:
            StudentProfilePage._render_profile_creation()
    
    @staticmethod
    def _render_existing_profile():
        """Render existing profile with edit option"""
        profile = st.session_state.student_profile
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Current Profile")
        with col2:
            if st.button("✏️ Edit Profile"):
                st.session_state.edit_mode = True
                st.rerun()
        
        # Display current profile
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {profile.get('name', 'N/A')}")
            st.write(f"**Email:** {profile.get('email', 'N/A')}")
            st.write(f"**Current Year:** {profile.get('current_year', 'N/A')}")
            st.write(f"**Degree:** {profile.get('degree', 'N/A')}")
            st.write(f"**GPA:** {profile.get('gpa', 'N/A')}")
        
        with col2:
            interests = profile.get('interests', [])
            skills = profile.get('skills', [])
            target_companies = profile.get('target_companies', [])
            target_roles = profile.get('target_roles', [])
            
            if interests:
                st.write("**Interests:**")
                for interest in interests:
                    st.write(f"• {interest}")
            
            if skills:
                st.write("**Skills:**")
                for skill in skills:
                    st.write(f"• {skill}")
        
        # Show targets in separate section
        if target_companies or target_roles:
            st.subheader("Career Targets")
            col1, col2 = st.columns(2)
            
            with col1:
                if target_companies:
                    st.write("**Target Companies:**")
                    for company in target_companies:
                        st.write(f"• {company}")
            
            with col2:
                if target_roles:
                    st.write("**Target Roles:**")
                    for role in target_roles:
                        st.write(f"• {role}")
        
        # Edit mode
        if st.session_state.get('edit_mode', False):
            st.divider()
            StudentProfilePage._render_profile_form(edit_mode=True, existing_profile=profile)
    
    @staticmethod
    def _render_profile_creation():
        """Render profile creation form"""
        st.info("👋 Welcome! Let's create your student profile to get started with finding alumni referrals.")
        StudentProfilePage._render_profile_form(edit_mode=False)
    
    @staticmethod
    def _render_profile_form(edit_mode=False, existing_profile=None):
        """Render the profile creation/editing form"""
        form_title = "Edit Profile" if edit_mode else "Create Your Profile"
        st.subheader(form_title)
        
        # Pre-fill values if editing
        default_values = existing_profile if existing_profile else {}
        
        with st.form("student_profile_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input(
                    "Full Name*", 
                    value=default_values.get('name', ''),
                    placeholder="John Doe"
                )
                email = st.text_input(
                    "Email*", 
                    value=default_values.get('email', ''),
                    placeholder="john.doe@university.edu"
                )
                current_year = st.selectbox(
                    "Current Year*", 
                    [1, 2, 3, 4, 5, 6],
                    index=(default_values.get('current_year', 1) - 1)
                )
                degree = st.text_input(
                    "Degree Program*", 
                    value=default_values.get('degree', ''),
                    placeholder="Computer Science"
                )
                gpa = st.number_input(
                    "GPA", 
                    min_value=0.0, 
                    max_value=10.0, 
                    step=0.1,
                    value=float(default_values.get('gpa', 0.0)) if default_values.get('gpa') else 0.0
                )
            
            with col2:
                interests_text = '\n'.join(default_values.get('interests', []))
                interests = st.text_area(
                    "Interests (one per line)",
                    value=interests_text,
                    placeholder="Machine Learning\nWeb Development\nData Science"
                )
                
                skills_text = '\n'.join(default_values.get('skills', []))
                skills = st.text_area(
                    "Skills (one per line)",
                    value=skills_text,
                    placeholder="Python\nJavaScript\nSQL\nReact"
                )
                
                companies_text = '\n'.join(default_values.get('target_companies', []))
                target_companies = st.text_area(
                    "Target Companies (one per line)",
                    value=companies_text,
                    placeholder="Google\nMicrosoft\nAmazon"
                )
                
                roles_text = '\n'.join(default_values.get('target_roles', []))
                target_roles = st.text_area(
                    "Target Roles (one per line)",
                    value=roles_text,
                    placeholder="Software Engineer\nData Scientist\nProduct Manager"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button(
                    "Update Profile" if edit_mode else "Create Profile", 
                    type="primary",
                    use_container_width=True
                )
            with col2:
                if edit_mode and st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()
            
            if submitted:
                # Process form data
                profile_data = {
                    'name': name.strip(),
                    'email': email.strip().lower(),
                    'current_year': current_year,
                    'degree': degree.strip(),
                    'gpa': gpa if gpa > 0 else None,
                    'interests': [i.strip() for i in interests.split('\n') if i.strip()],
                    'skills': [s.strip() for s in skills.split('\n') if s.strip()],
                    'target_companies': [c.strip() for c in target_companies.split('\n') if c.strip()],
                    'target_roles': [r.strip() for r in target_roles.split('\n') if r.strip()]
                }
                
                # Validate profile data
                is_valid, errors = InputValidator.validate_student_profile(profile_data)
                
                if is_valid:
                    # Save to session state
                    st.session_state.student_profile = profile_data
                    if edit_mode:
                        st.session_state.edit_mode = False
                    
                    # Save to database (async operation)
                    try:
                        if edit_mode:
                            st.success("✅ Profile updated successfully!")
                        else:
                            st.success("✅ Profile created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving profile: {str(e)}")
                else:
                    # Show validation errors
                    for error in errors:
                        st.error(f"❌ {error}")