import streamlit as st

class ReferralRequestsPage:
    @staticmethod
    async def render():
        """Render the referral requests page"""
        st.header("📬 Referral Requests & Messages")
        
        # Check prerequisites
        if "student_profile" not in st.session_state:
            st.warning("⚠️ Please create your student profile first.")
            if st.button("Create Profile Now"):
                st.session_state.navigation = "Student Profile"
                st.rerun()
            return
        
        # Check if coming from alumni search
        if st.session_state.get('selected_alumni_for_path'):
            await ReferralRequestsPage._render_single_referral_path()
        elif st.session_state.get('show_message_generator'):
            await ReferralRequestsPage._render_message_generator()
        else:
            await ReferralRequestsPage._render_main_interface()
    
    @staticmethod
    async def _render_main_interface():
        """Render main referral requests interface"""
        st.subheader("Manage Your Referral Requests")
        
        # Quick actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Search Alumni First", use_container_width=True):
                st.session_state.navigation = "Alumni Search"
                st.rerun()
        
        with col2:
            if st.button("📊 View Analytics", use_container_width=True):
                st.session_state.navigation = "Analytics"
                st.rerun()
        
        # Display existing referral requests
        await ReferralRequestsPage._display_existing_requests()
    
    @staticmethod
    async def _render_single_referral_path():
        """Render referral path for single alumni"""
        alumni = st.session_state.selected_alumni_for_path
        
        st.subheader(f"🛤️ Referral Path for {alumni.get('name', 'Alumni')}")
        
        # Display alumni info
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Company:** {alumni.get('current_company', 'N/A')}")
            st.write(f"**Role:** {alumni.get('current_role', 'N/A')}")
            st.write(f"**Domain:** {alumni.get('domain', 'N/A')}")
        
        with col2:
            st.write(f"**Experience:** {alumni.get('experience_years', 0)} years")
            st.write(f"**Location:** {alumni.get('location', 'N/A')}")
            st.write(f"**Graduation:** {alumni.get('graduation_year', 'N/A')}")
        
        # Referral strategy
        st.subheader("📋 Recommended Referral Strategy")
        
        strategy_info = {
            "Connection Strength": "Strong" if alumni.get('final_match_score', 0) > 0.7 else "Moderate",
            "Best Approach": "LinkedIn Message",
            "Success Probability": "High (70-85%)" if alumni.get('final_match_score', 0) > 0.7 else "Medium (50-70%)",
            "Recommended Timing": "Tuesday-Thursday, 10 AM - 2 PM"
        }
        
        for key, value in strategy_info.items():
            st.write(f"**{key}:** {value}")
        
        # Preparation steps
        st.subheader("✅ Preparation Steps")
        prep_steps = [
            f"Research {alumni.get('current_company', 'the company')}'s recent news and developments",
            "Update your LinkedIn profile and resume",
            "Prepare specific questions about the company culture",
            "Review the job requirements for your target role",
            "Prepare a concise elevator pitch about yourself"
        ]
        
        for i, step in enumerate(prep_steps, 1):
            st.write(f"{i}. {step}")
        
        # Generate message option
        st.divider()
        if st.button("✉️ Generate Outreach Message", type="primary"):
            st.session_state.selected_alumni_for_message = alumni
            st.session_state.show_message_generator = True
            st.rerun()
        
        # Back button
        if st.button("🔙 Back to Search"):
            st.session_state.selected_alumni_for_path = None
            st.session_state.navigation = "Alumni Search"
            st.rerun()
    
    @staticmethod
    async def _render_message_generator():
        """Render message generator interface"""
        alumni = st.session_state.get('selected_alumni_for_message')
        student_profile = st.session_state.student_profile
        
        if not alumni:
            st.error("No alumni selected for message generation.")
            return
        
        st.subheader(f"✉️ Generate Message for {alumni.get('name', 'Alumni')}")
        
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
            await ReferralRequestsPage._display_generated_messages(
                student_profile, alumni, target_role, message_type, additional_context
            )
        
        # Back button
        if st.button("🔙 Back"):
            st.session_state.show_message_generator = False
            st.session_state.selected_alumni_for_message = None
            st.rerun()
    
    @staticmethod
    async def _display_generated_messages(student_profile, alumni, target_role, message_type, additional_context):
        """Display generated outreach messages"""
        st.subheader("📝 Generated Messages")
        
        # Generate different message variants
        messages = ReferralRequestsPage._create_message_variants(
            student_profile, alumni, target_role, message_type, additional_context
        )
        
        # Display subject lines for emails
        if message_type == "email":
            st.write("**Suggested Subject Lines:**")
            subject_lines = [
                f"Fellow Alumni - Seeking Guidance for {alumni.get('current_company', 'Company')} Opportunities",
                f"Referral Request from {student_profile.get('name', 'Student')} - {alumni.get('current_company', 'Company')}",
                f"Alumni Network Outreach - {student_profile.get('name', 'Student')}"
            ]
            for i, subject in enumerate(subject_lines, 1):
                st.write(f"{i}. {subject}")
            st.divider()
        
        # Display message variants
        for message in messages:
            variant = message.get('variant', 'Unknown')
            content = message.get('content', '')
            recommended_use = message.get('recommended_use', '')
            
            with st.expander(f"{variant.title()} Version ({len(content)} characters)", expanded=False):
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
                        st.success(f"{variant.title()} message ready to copy!")
                
                with col2:
                    if st.button(f"Save Request", key=f"save_{variant}"):
                        st.success("Referral request saved!")
        
        # Show tips
        st.subheader("💡 Message Tips")
        tips = ReferralRequestsPage._get_message_tips(message_type)
        for tip in tips:
            st.write(f"• {tip}")
    
    @staticmethod
    def _create_message_variants(student_profile, alumni, target_role, message_type, additional_context):
        """Create different message variants"""
        student_name = student_profile.get('name', 'Student')
        alumni_name = alumni.get('name', 'Alumni')
        company = alumni.get('current_company', 'Company')
        student_degree = student_profile.get('degree', 'Computer Science')
        student_year = student_profile.get('current_year', 3)
        
        messages = []
        
        # Professional variant
        if message_type == "linkedin":
            professional_msg = f"""Hi {alumni_name},

I hope this message finds you well. My name is {student_name}, and I'm a {student_year}rd year {student_degree} student.

I'm very interested in {target_role} opportunities at {company} and would greatly appreciate any insights you might share about your experience there. Your background in {alumni.get('domain', 'technology')} aligns well with my career interests.

Would you be open to a brief conversation about your journey and any advice you might have for someone looking to join {company}?

Thank you for your time and consideration.

Best regards,
{student_name}"""
        else:
            professional_msg = f"""Dear {alumni_name},

I hope this email finds you well. My name is {student_name}, and I'm a {student_year}rd year {student_degree} student. I came across your profile and was impressed by your journey at {company}.

I'm currently exploring {target_role} opportunities and am particularly interested in {company}. Given your experience and success in {alumni.get('domain', 'your field')}, I would be incredibly grateful for any guidance you might be able to provide.

I understand you must be very busy, but I would greatly appreciate even a brief conversation about:
• Your experience at {company} and the company culture
• Advice for someone interested in {target_role} positions
• Any insights about growth opportunities

I've attached my resume for your reference and would be happy to work around your schedule for a quick call.

Thank you very much for considering my request.

Best regards,
{student_name}
[Your Contact Information]"""
        
        messages.append({
            "variant": "professional",
            "content": professional_msg,
            "recommended_use": "Best for senior alumni or formal company cultures"
        })
        
        # Friendly variant
        friendly_msg = professional_msg.replace(
            "I hope this message finds you well.", 
            "I hope you're doing well and enjoying your role!"
        ).replace(
            "Best regards,", 
            "Looking forward to hearing from you!\n\nBest,"
        )
        
        messages.append({
            "variant": "friendly",
            "content": friendly_msg,
            "recommended_use": "Ideal for recent graduates or casual company environments"
        })
        
        # Brief variant
        if message_type == "linkedin":
            brief_msg = f"""Hi {alumni_name},

I'm {student_name}, a {student_year}rd year {student_degree} student interested in {target_role} opportunities at {company}.

Would you be open to sharing any insights about your experience there? I'd really appreciate any guidance you might have.

Thanks!
{student_name}"""
        else:
            brief_msg = f"""Hi {alumni_name},

I'm {student_name}, a {student_degree} student interested in {target_role} positions at {company}.

Could you spare a few minutes to share insights about your experience? Any guidance would be invaluable.

Best,
{student_name}"""
        
        messages.append({
            "variant": "brief",
            "content": brief_msg,
            "recommended_use": "Perfect for busy professionals or follow-up messages"
        })
        
        return messages
    
    @staticmethod
    def _get_message_tips(message_type):
        """Get tips for the specific message type"""
        tips = {
            'linkedin': [
                "Keep initial message under 300 characters for better response rates",
                "Mention mutual connections or common experiences",
                "Send connection request with a personalized note",
                "Follow up after 1 week if no response",
                "Be genuine and specific about your interests"
            ],
            'email': [
                "Use a clear, professional subject line",
                "Keep the email concise but informative",
                "Include your resume as an attachment",
                "Use a professional email signature",
                "Follow up after 5-7 business days"
            ],
            'follow_up': [
                "Reference your previous message briefly",
                "Provide any updates since last contact",
                "Reiterate your interest respectfully",
                "Suggest alternative ways to connect",
                "Keep it shorter than the original message"
            ]
        }
        return tips.get(message_type, tips['linkedin'])
    
    @staticmethod
    async def _display_existing_requests():
        """Display existing referral requests"""
        st.subheader("📋 Your Referral Requests")
        
        # Sample data for demonstration
        sample_requests = [
            {
                "alumni_name": "Rajesh Kumar",
                "company": "Google",
                "role": "Software Engineer",
                "status": "sent",
                "sent_date": "2025-06-15",
                "message_type": "LinkedIn"
            },
            {
                "alumni_name": "Priya Sharma",
                "company": "Microsoft",
                "role": "Data Scientist",
                "status": "pending",
                "sent_date": "2025-06-14",
                "message_type": "Email"
            }
        ]
        
        if sample_requests:
            for i, request in enumerate(sample_requests):
                with st.expander(f"{request['alumni_name']} - {request['company']}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Role:** {request['role']}")
                        st.write(f"**Status:** {request['status']}")
                    
                    with col2:
                        st.write(f"**Sent:** {request['sent_date']}")
                        st.write(f"**Method:** {request['message_type']}")
                    
                    with col3:
                        if st.button(f"Follow Up", key=f"followup_{i}"):
                            st.info("Follow-up message generator would open here")
        else:
            st.info("No referral requests yet. Start by searching for alumni!")