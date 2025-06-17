import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
import pandas as pd

class UIComponents:
    @staticmethod
    def render_header():
        """Render application header"""
        st.set_page_config(
            page_title="Alumni Referrer Network",
            page_icon="🎓",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🎓 Alumni Referrer Network Builder")
        st.markdown("*Connect with alumni for job referrals using AI-powered matching*")
        st.divider()
    
    @staticmethod
    def render_sidebar_navigation():
        """Render sidebar navigation"""
        with st.sidebar:
            st.header("Navigation")
            
            page = st.radio(
                "Go to:",
                ["Dashboard", "Student Profile", "Alumni Search", "Referral Requests", "Analytics"],
                key="navigation"
            )
            
            st.divider()
            
            # Quick stats
            st.subheader("Quick Stats")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Alumni", "1,234", "+23")
            with col2:
                st.metric("Referrals", "456", "+12")
            
            return page
    
    @staticmethod
    def render_student_profile_form():
        """Render student profile creation/editing form"""
        st.subheader("Student Profile")
        
        with st.form("student_profile_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name*", placeholder="John Doe")
                email = st.text_input("Email*", placeholder="john.doe@university.edu")
                current_year = st.selectbox("Current Year*", [1, 2, 3, 4, 5, 6])
                degree = st.text_input("Degree Program*", placeholder="Computer Science")
                gpa = st.number_input("GPA", min_value=0.0, max_value=10.0, step=0.1)
            
            with col2:
                interests = st.text_area(
                    "Interests (one per line)",
                    placeholder="Machine Learning\nWeb Development\nData Science"
                ).split('\n')
                
                skills = st.text_area(
                    "Skills (one per line)",
                    placeholder="Python\nJavaScript\nSQL\nReact"
                ).split('\n')
                
                target_companies = st.text_area(
                    "Target Companies (one per line)",
                    placeholder="Google\nMicrosoft\nAmazon"
                ).split('\n')
                
                target_roles = st.text_area(
                    "Target Roles (one per line)",
                    placeholder="Software Engineer\nData Scientist\nProduct Manager"
                ).split('\n')
            
            submitted = st.form_submit_button("Save Profile", type="primary")
            
            if submitted:
                profile_data = {
                    'name': name.strip(),
                    'email': email.strip(),
                    'current_year': current_year,
                    'degree': degree.strip(),
                    'gpa': gpa if gpa > 0 else None,
                    'interests': [i.strip() for i in interests if i.strip()],
                    'skills': [s.strip() for s in skills if s.strip()],
                    'target_companies': [c.strip() for c in target_companies if c.strip()],
                    'target_roles': [r.strip() for r in target_roles if r.strip()]
                }
                return profile_data
        
        return None
    
    @staticmethod
    def render_alumni_search_interface():
        """Render alumni search interface"""
        st.subheader("🔍 Find Alumni")
        
        # Search filters
        with st.expander("Search Filters", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                company = st.text_input("Company", placeholder="Google, Microsoft, etc.")
                domain = st.selectbox(
                    "Domain",
                    ["All", "Software Engineering", "Data Science", "Product Management", 
                     "Business", "Design", "Marketing", "Finance"]
                )
            
            with col2:
                role = st.text_input("Role", placeholder="Software Engineer, etc.")
                graduation_year = st.slider("Graduation Year Range", 2010, 2024, (2018, 2024))
            
            with col3:
                location = st.text_input("Location", placeholder="San Francisco, Remote, etc.")
                experience_range = st.slider("Experience Years", 0, 20, (2, 10))
        
        search_clicked = st.button("🔍 Search Alumni", type="primary")
        
        return {
            'company': company,
            'domain': domain if domain != "All" else "",
            'role': role,
            'graduation_year_range': graduation_year,
            'location': location,
            'experience_range': experience_range,
            'search_clicked': search_clicked
        }
    
    @staticmethod
    def render_alumni_results(alumni_results: List[Dict[str, Any]]):
        """Render alumni search results"""
        if not alumni_results:
            st.info("No alumni found matching your criteria. Try adjusting your search filters.")
            return []
        
        st.subheader(f"Found {len(alumni_results)} Alumni")
        
        selected_alumni = []
        
        for i, alumni in enumerate(alumni_results):
            with st.expander(f"{alumni.get('name', 'Unknown')} - {alumni.get('current_company', 'Unknown Company')}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Role:** {alumni.get('current_role', 'N/A')}")
                    st.write(f"**Domain:** {alumni.get('domain', 'N/A')}")
                    st.write(f"**Graduation:** {alumni.get('graduation_year', 'N/A')}")
                    st.write(f"**Experience:** {alumni.get('experience_years', 0)} years")
                
                with col2:
                    st.write(f"**Location:** {alumni.get('location', 'N/A')}")
                    skills = alumni.get('skills', [])
                    if skills:
                        st.write(f"**Skills:** {', '.join(skills[:5])}")
                    
                    # Show alignment score if available
                    if 'alignment_score' in alumni:
                        score = alumni['alignment_score']
                        st.write(f"**Match Score:** {score:.2f}")
                        st.progress(score)
                
                with col3:
                    if st.button(f"Select", key=f"select_{i}"):
                        selected_alumni.append(alumni)
                        st.success("Selected!")
        
        return selected_alumni
    
    @staticmethod
    def render_referral_path_display(referral_paths: List[Dict[str, Any]]):
        """Display referral paths and recommendations"""
        if not referral_paths:
            st.info("No referral paths generated yet.")
            return
        
        st.subheader("🛤️ Recommended Referral Paths")
        
        for i, path in enumerate(referral_paths):
            with st.expander(f"Path {i+1}: {path.get('alumni_name', 'Unknown Alumni')}", expanded=i==0):
                
                # Path description
                st.write("**Path Description:**")
                st.info(path.get('path_description', 'No description available'))
                
                # Key metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Connection Strength", path.get('connection_strength', 'Unknown'))
                with col2:
                    st.metric("Success Probability", path.get('success_probability', 'Unknown'))
                with col3:
                    st.metric("Recommendation Score", path.get('recommendation_score', 0))
                
                # Recommended approach
                st.write("**Recommended Approach:**")
                approach = path.get('recommended_approach', {})
                for key, value in approach.items():
                    st.write(f"• **{key.replace('_', ' ').title()}:** {value}")
                
                # Preparation steps
                st.write("**Preparation Steps:**")
                prep_steps = path.get('preparation_steps', [])
                for step in prep_steps:
                    st.write(f"• {step}")
                
                # Timeline
                st.write("**Expected Timeline:**")
                timeline = path.get('timeline', {})
                for phase, duration in timeline.items():
                    st.write(f"• **{phase.replace('_', ' ').title()}:** {duration}")
    
    @staticmethod
    def render_message_generator(student_profile: Dict[str, Any], alumni_info: Dict[str, Any]):
        """Render outreach message generator interface"""
        st.subheader("✉️ Generate Outreach Messages")
        
        # Message configuration
        col1, col2 = st.columns(2)
        with col1:
            message_type = st.selectbox(
                "Message Type",
                ["linkedin", "email", "follow_up"],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        with col2:
            target_role = st.text_input(
                "Target Role",
                value="Software Engineer",
                placeholder="Enter the role you're applying for"
            )
        
        # Additional context
        additional_context = st.text_area(
            "Additional Context (Optional)",
            placeholder="Any specific information you'd like to include in the message..."
        )
        
        if st.button("🎯 Generate Messages", type="primary"):
            referral_context = {
                'target_role': target_role,
                'target_company': alumni_info.get('current_company', 'the company'),
                'additional_context': additional_context
            }
            
            return {
                'student_profile': student_profile,
                'alumni_info': alumni_info,
                'referral_context': referral_context,
                'message_type': message_type
            }
        
        return None
    
    @staticmethod
    def render_generated_messages(message_results: Dict[str, Any]):
        """Display generated outreach messages"""
        if not message_results or message_results.get('status') != 'success':
            st.error("Failed to generate messages. Please try again.")
            return
        
        messages = message_results.get('generated_messages', [])
        message_tips = message_results.get('message_tips', [])
        subject_lines = message_results.get('subject_lines', [])
        
        st.subheader("📝 Generated Messages")
        
        # Show subject lines for emails
        if subject_lines:
            st.write("**Suggested Subject Lines:**")
            for i, subject in enumerate(subject_lines, 1):
                st.write(f"{i}. {subject}")
            st.divider()
        
        # Display message variants
        for message in messages:
            variant = message.get('variant', 'Unknown')
            content = message.get('content', '')
            length = message.get('estimated_length', 0)
            recommended_use = message.get('recommended_use', '')
            
            with st.expander(f"{variant.title()} Version ({length} characters)", expanded=False):
                st.write(f"**Recommended for:** {recommended_use}")
                st.text_area(
                    "Message Content",
                    value=content,
                    height=200,
                    key=f"message_{variant}",
                    help="Click to select all text and copy"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Copy {variant.title()}", key=f"copy_{variant}"):
                        st.success(f"{variant.title()} message copied to clipboard!")
                
                with col2:
                    if st.button(f"Edit {variant.title()}", key=f"edit_{variant}"):
                        st.info("You can edit the message in the text area above")
        
        # Show tips
        if message_tips:
            st.subheader("💡 Message Tips")
            for tip in message_tips:
                st.write(f"• {tip}")
    
    @staticmethod
    def render_analytics_dashboard():
        """Render analytics and insights dashboard"""
        st.subheader("📊 Analytics Dashboard")
        
        # Sample data for demonstration
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Alumni", "1,234", "+12%")
        with col2:
            st.metric("Active Students", "567", "+8%")
        with col3:
            st.metric("Referrals Made", "89", "+15%")
        with col4:
            st.metric("Success Rate", "67%", "+3%")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Alumni by company chart
            st.subheader("Top Companies (Alumni)")
            companies_data = {
                'Company': ['Google', 'Microsoft', 'Amazon', 'Apple', 'Meta'],
                'Count': [145, 132, 98, 87, 76]
            }
            fig = px.bar(companies_data, x='Company', y='Count', 
                        title="Alumni Distribution by Company")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Referral success rate by domain
            st.subheader("Success Rate by Domain")
            domain_data = {
                'Domain': ['Software Engineering', 'Data Science', 'Product', 'Business', 'Design'],
                'Success Rate': [72, 68, 65, 58, 61]
            }
            fig = px.pie(domain_data, values='Success Rate', names='Domain',
                        title="Referral Success Rate by Domain")
            st.plotly_chart(fig, use_container_width=True)
        
        # Timeline chart
        st.subheader("Referral Activity Over Time")
        timeline_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Referrals': [12, 18, 25, 22, 31, 28],
            'Successful': [8, 12, 17, 15, 21, 19]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timeline_data['Month'], y=timeline_data['Referrals'],
                                mode='lines+markers', name='Total Referrals'))
        fig.add_trace(go.Scatter(x=timeline_data['Month'], y=timeline_data['Successful'],
                                mode='lines+markers', name='Successful'))
        fig.update_layout(title="Referral Trends", xaxis_title="Month", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)