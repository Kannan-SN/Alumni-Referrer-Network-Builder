import streamlit as st
from ui.components import UIComponents
from agents.alumni_mining_agent import AlumniMiningAgent
from agents.domain_alignment_agent import DomainAlignmentAgent
import asyncio

class AlumniSearchPage:
    @staticmethod
    async def render():
        """Render the alumni search page"""
        st.header("🔍 Alumni Search & Matching")
        
        # Check if student profile exists
        if "student_profile" not in st.session_state:
            st.warning("⚠️ Please create your student profile first to get personalized alumni matches.")
            if st.button("Create Profile Now"):
                st.session_state.navigation = "Student Profile"
                st.rerun()
            return
        
        # Render search interface
        search_params = UIComponents.render_alumni_search_interface()
        
        if search_params['search_clicked']:
            await AlumniSearchPage._perform_search(search_params)
        
        # Display results if available
        if "alumni_search_results" in st.session_state:
            await AlumniSearchPage._display_search_results()
    
    @staticmethod
    async def _perform_search(search_params):
        """Perform alumni search using AI agents"""
        with st.spinner("🔍 Searching for alumni and calculating matches..."):
            try:
                # Initialize agents
                mining_agent = AlumniMiningAgent()
                alignment_agent = DomainAlignmentAgent()
                
                # Step 1: Mine alumni data
                mining_input = {
                    'company': search_params['company'],
                    'role': search_params['role'],
                    'domain': search_params['domain'],
                    'graduation_year': search_params['graduation_year_range'][0]  # Use start of range
                }
                
                mining_results = await mining_agent.execute(mining_input)
                
                if mining_results['status'] == 'success':
                    # Step 2: Calculate domain alignment
                    alignment_input = {
                        'student_profile': st.session_state.student_profile,
                        'alumni_list': mining_results['alumni_data']
                    }
                    
                    alignment_results = await alignment_agent.execute(alignment_input)
                    
                    if alignment_results['status'] == 'success':
                        # Store results in session state
                        st.session_state.alumni_search_results = {
                            'raw_results': mining_results['alumni_data'],
                            'aligned_results': alignment_results['aligned_alumni'],
                            'search_params': search_params,
                            'total_found': mining_results['alumni_found'],
                            'total_aligned': alignment_results['total_matches']
                        }
                        
                        st.success(f"✅ Found {alignment_results['total_matches']} matching alumni!")
                        st.rerun()
                    else:
                        st.error(f"❌ Error in alignment calculation: {alignment_results.get('message', 'Unknown error')}")
                else:
                    st.error(f"❌ Error in alumni search: {mining_results.get('message', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
    
    @staticmethod
    async def _display_search_results():
        """Display search results with alignment scores"""
        results = st.session_state.alumni_search_results
        aligned_alumni = results['aligned_results']
        
        if not aligned_alumni:
            st.info("No well-aligned alumni found. Try adjusting your search criteria.")
            return
        
        st.subheader(f"🎯 Found {len(aligned_alumni)} Well-Matched Alumni")
        
        # Results overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Found", results['total_found'])
        with col2:
            st.metric("Well Aligned", results['total_aligned'])
        with col3:
            alignment_rate = (results['total_aligned'] / results['total_found'] * 100) if results['total_found'] > 0 else 0
            st.metric("Alignment Rate", f"{alignment_rate:.1f}%")
        
        st.divider()
        
        # Display alumni with selection
        selected_alumni = []
        
        for i, alumni in enumerate(aligned_alumni):
            with st.expander(
                f"⭐ {alumni.get('name', 'Unknown')} - {alumni.get('current_company', 'Unknown Company')} "
                f"(Match: {alumni.get('alignment_score', 0):.2f})", 
                expanded=i < 3  # Expand first 3 results
            ):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Role:** {alumni.get('current_role', 'N/A')}")
                    st.write(f"**Domain:** {alumni.get('domain', 'N/A')}")
                    st.write(f"**Graduation:** {alumni.get('graduation_year', 'N/A')}")
                    st.write(f"**Experience:** {alumni.get('experience_years', 0)} years")
                    st.write(f"**Location:** {alumni.get('location', 'N/A')}")
                
                with col2:
                    # Skills
                    skills = alumni.get('skills', [])
                    if skills:
                        st.write(f"**Skills:** {', '.join(skills[:6])}")
                    
                    # Alignment reasons
                    reasons = alumni.get('alignment_reasons', [])
                    if reasons:
                        st.write("**Why this is a good match:**")
                        for reason in reasons[:3]:
                            st.write(f"• {reason}")
                    
                    # Match score visualization
                    score = alumni.get('alignment_score', 0)
                    st.write(f"**Alignment Score:** {score:.2f}")
                    st.progress(score)
                
                with col3:
                    # Action buttons
                    if st.button(f"🎯 Generate Referral Path", key=f"path_{i}"):
                        st.session_state.selected_alumni_for_path = alumni
                        st.session_state.navigation = "Referral Requests"
                        st.rerun()
                    
                    if st.button(f"✉️ Generate Message", key=f"message_{i}"):
                        st.session_state.selected_alumni_for_message = alumni
                        st.session_state.show_message_generator = True
                        st.rerun()
                    
                    if st.button(f"📋 Add to Selected", key=f"select_{i}"):
                        if "selected_alumni_list" not in st.session_state:
                            st.session_state.selected_alumni_list = []
                        
                        if alumni not in st.session_state.selected_alumni_list:
                            st.session_state.selected_alumni_list.append(alumni)
                            st.success("Added!")
                        else:
                            st.info("Already selected")
        
        # Batch actions for selected alumni
        if "selected_alumni_list" in st.session_state and st.session_state.selected_alumni_list:
            st.divider()
            st.subheader(f"📋 Selected Alumni ({len(st.session_state.selected_alumni_list)})")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🛤️ Generate All Paths", use_container_width=True):
                    st.session_state.batch_path_generation = True
                    st.session_state.navigation = "Referral Requests"
                    st.rerun()
            
            with col2:
                if st.button("✉️ Generate All Messages", use_container_width=True):
                    st.session_state.batch_message_generation = True
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Clear Selection", use_container_width=True):
                    st.session_state.selected_alumni_list = []
                    st.rerun()
