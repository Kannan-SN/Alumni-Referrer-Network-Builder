```python
import streamlit as st
from ui.components import UIComponents
from agents.referral_path_agent import ReferralPathAgent
from agents.outreach_generator_agent import OutreachGeneratorAgent
import asyncio

class ReferralRequestsPage:
    @staticmethod
    async def render():
        """Render the referral requests page"""
        st.header("📬 Referral Requests & Messages")
        
        # Check prerequisites
        if "student_profile" not in st.session_state:
            st.warning("⚠️ Please create your student profile first.")
            return
        
        # Check if coming from alumni search with selected alumni
        if st.session_state.get('selected_alumni_for_path'):
            await ReferralRequestsPage._render_single_referral_path()
        elif st.session_state.get('batch_path_generation'):
            await ReferralRequestsPage._render_batch_referral_paths()
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
        student_profile = st.session_state.student_profile
        
        st.subheader(f"🛤️ Referral Path for {alumni.get('name', 'Alumni')}")
        
        with st.spinner("Generating optimal referral path..."):
            try:
                path_agent = ReferralPathAgent()
                
                path_input = {
                    'student_profile': student_profile,
                    'alumni_matches': [alumni]
                }
                
                path_results = await path_agent.execute(path_input)
                
                if path_results['status'] == 'success':
                    paths = path_results['referral_paths']
                    if paths:
                        UIComponents.render_referral_path_display(paths)
                        
                        # Option to generate message
                        st.divider()
                        if st.button("✉️ Generate Outreach Message", type="primary"):
                            st.session_state.selected_alumni_for_message = alumni
                            st.session_state.selected_path = paths[0]
                            st.session_state.show_message_generator = True
                            st.rerun()
                    else:
                        st.error("No referral paths could be generated.")
                else:
                    st.error(f"Error generating path: {path_results.get('message', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Failed to generate referral path: {str(e)}")
        
        # Clear the selection
        if st.button("🔙 Back to Search"):
            st.session_state.selected_alumni_for_path = None
            st.session_state.navigation = "Alumni Search"
            st.rerun()
    
    @staticmethod
    async def _render_batch_referral_paths():
        """Render referral paths for multiple alumni"""
        selected_alumni = st.session_state.get('selected_alumni_list', [])
        
        if not selected_alumni:
            st.warning("No alumni selected for batch processing.")
            return
        
        st.subheader(f"🛤️ Generating Paths for {len(selected_alumni)} Alumni")
        
        with st.spinner("Generating referral paths for all selected alumni..."):
            try:
                path_agent = ReferralPathAgent()
                student_profile = st.session_state.student_profile
                
                path_input = {
                    'student_profile': student_profile,
                    'alumni_matches': selected_alumni
                }
                
                path_results = await path_agent.execute(path_input)
                
                if path_results['status'] == 'success':
                    all_paths = path_results['referral_paths']
                    ranked_paths = path_results['path_recommendations']
                    
                    st.session_state.batch_generated_paths = all_paths
                    UIComponents.render_referral_path_display(ranked_paths)
                    
                    # Batch message generation option
                    st.divider()
                    if st.button("✉️ Generate Messages for All", type="primary"):
                        st.session_state.batch_message_generation = True
                        st.rerun()
                    
                else:
                    st.error(f"Error generating paths: {path_results.get('message', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Failed to generate referral paths: {str(e)}")
        
        # Clear batch processing flag
        if st.button("🔙 Back to Search"):
            st.session_state.batch_path_generation = False
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
        
        # Message generator interface
        message_input = UIComponents.render_message_generator(student_profile, alumni)
        
        if message_input:
            with st.spinner("Generating personalized messages..."):
                try:
                    outreach_agent = OutreachGeneratorAgent()
                    message_results = await outreach_agent.execute(message_input)
                    
                    if message_results['status'] == 'success':
                        UIComponents.render_generated_messages(message_results)
                        
                        # Save option
                        st.divider()
                        if st.button("💾 Save to Referral Requests"):
                            # Save to database logic here
                            st.success("✅ Referral request saved!")
                    else:
                        st.error(f"Error generating messages: {message_results.get('message', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Failed to generate messages: {str(e)}")
        
        # Clear the selection
        if st.button("🔙 Back"):
            st.session_state.show_message_generator = False
            st.session_state.selected_alumni_for_message = None
            st.rerun()
    
    @staticmethod
    async def _display_existing_requests():
        """Display existing referral requests"""
        st.subheader("📋 Your Referral Requests")
        
        # Sample data - replace with actual database queries
        sample_requests = [
            {
                "alumni_name": "John Smith",
                "company": "Google",
                "role": "Software Engineer",
                "status": "sent",
                "sent_date": "2025-06-15",
                "message_type": "LinkedIn"
            },
            {
                "alumni_name": "Sarah Johnson",
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
