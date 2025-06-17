import streamlit as st
from ui.components import UIComponents
from database.mongodb_handler import mongodb_handler
import asyncio

class DashboardPage:
    @staticmethod
    async def render():
        """Render the main dashboard page"""
        st.header("🏠 Dashboard")
        
        # Quick actions
        st.subheader("Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("👤 Create Student Profile", use_container_width=True):
                st.session_state.navigation = "Student Profile"
                st.rerun()
        
        with col2:
            if st.button("🔍 Search Alumni", use_container_width=True):
                st.session_state.navigation = "Alumni Search"
                st.rerun()
        
        with col3:
            if st.button("📬 Generate Messages", use_container_width=True):
                st.session_state.navigation = "Referral Requests"
                st.rerun()
        
        with col4:
            if st.button("📊 View Analytics", use_container_width=True):
                st.session_state.navigation = "Analytics"
                st.rerun()
        
        st.divider()
        
        # Recent activity
        st.subheader("Recent Activity")
        
        # Sample recent activity data
        recent_activities = [
            {"type": "search", "description": "Searched for Google alumni in Software Engineering", "time": "2 hours ago"},
            {"type": "message", "description": "Generated LinkedIn message for John Smith at Microsoft", "time": "4 hours ago"},
            {"type": "profile", "description": "Updated student profile with new skills", "time": "1 day ago"},
            {"type": "referral", "description": "Received response from alumni at Amazon", "time": "2 days ago"}
        ]
        
        for activity in recent_activities:
            icon = {"search": "🔍", "message": "✉️", "profile": "👤", "referral": "🎯"}.get(activity["type"], "📝")
            st.write(f"{icon} {activity['description']} - *{activity['time']}*")
        
        st.divider()
        
        # Analytics preview
        UIComponents.render_analytics_dashboard()