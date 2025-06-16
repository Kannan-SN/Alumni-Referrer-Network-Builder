import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any, Optional
import networkx as nx

class UIComponents:
    """Reusable UI components for the Alumni Network app"""
    
    def __init__(self):
        pass
    
    def create_metric_card(self, title: str, value: str, delta: str = None, help_text: str = None):
        """Create a styled metric card"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.metric(
                label=title,
                value=value,
                delta=delta,
                help=help_text
            )
    
    def create_alumni_card(self, alumni_data: Dict[str, Any], show_actions: bool = True):
        """Create an alumni profile card"""
        
        metadata = alumni_data.get('metadata', alumni_data)
        
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"### {metadata.get('name', 'Unknown')}")
                st.markdown(f"**{metadata.get('current_position', 'Position not specified')}**")
                st.markdown(f"📍 {metadata.get('current_company', 'Company not specified')}")
                st.markdown(f"🎓 {metadata.get('department', 'Unknown')} • Class of {metadata.get('graduation_year', 'Unknown')}")
                
                # Skills tags
                skills = metadata.get('skills', [])
                if skills:
                    st.markdown("**Skills:**")
                    skill_text = " • ".join([f"`{skill}`" for skill in skills[:5]])
                    st.markdown(skill_text)
            
            with col2:
                # Metrics
                if 'composite_score' in alumni_data:
                    st.metric("Match Score", f"{alumni_data['composite_score']:.2f}")
                
                response_rate = metadata.get('response_rate', 0)
                st.metric("Response Rate", f"{response_rate:.1%}")
                
                if metadata.get('hiring_authority', False):
                    st.success("✅ Hiring Authority")
                
                if metadata.get('linkedin_url'):
                    st.markdown(f"[LinkedIn Profile]({metadata['linkedin_url']})")
            
            with col3:
                if show_actions:
                    if st.button("Analyze", key=f"analyze_{metadata.get('id', 'unknown')}"):
                        return "analyze"
                    
                    if st.button("Email", key=f"email_{metadata.get('id', 'unknown')}"):
                        return "email"
        
        st.divider()
        return None
    
    def create_skill_cloud(self, skills_data: List[str], title: str = "Skills Overview"):
        """Create a word cloud-style visualization for skills"""
        
        if not skills_data:
            st.info("No skills data available")
            return
        
        # Count skill frequency
        skill_counts = {}
        for skill in skills_data:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Create DataFrame
        df = pd.DataFrame(list(skill_counts.items()), columns=['Skill', 'Count'])
        df = df.sort_values('Count', ascending=False).head(20)
        
        # Create bar chart
        fig = px.bar(
            df,
            x='Count',
            y='Skill',
            orientation='h',
            title=title,
            color='Count',
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_company_distribution_chart(self, company_data: List[Dict[str, Any]]):
        """Create company distribution chart"""
        
        if not company_data:
            st.info("No company data available")
            return
        
        df = pd.DataFrame(company_data)
        
        # Pie chart for company distribution
        fig = px.pie(
            df.head(10),
            values='count',
            names='_id',
            title="Alumni Distribution by Company"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_graduation_timeline(self, graduation_data: List[Dict[str, Any]]):
        """Create graduation year timeline chart"""
        
        if not graduation_data:
            st.info("No graduation data available")
            return
        
        df = pd.DataFrame(graduation_data)
        df['_id'] = pd.to_numeric(df['_id'], errors='coerce')
        df = df.dropna().sort_values('_id')
        
        fig = px.line(
            df,
            x='_id',
            y='count',
            title="Alumni Count by Graduation Year",
            markers=True
        )
        fig.update_xaxis(title="Graduation Year")
        fig.update_yaxis(title="Number of Alumni")
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_network_graph(self, connections_data: List[Dict[str, Any]], center_node: str = None):
        """Create a network graph visualization"""
        
        try:
            # Create networkx graph
            G = nx.Graph()
            
            # Add nodes and edges
            for connection in connections_data:
                source = connection.get('source')
                target = connection.get('target')
                weight = connection.get('weight', 1)
                
                if source and target:
                    G.add_edge(source, target, weight=weight)
            
            if len(G.nodes()) == 0:
                st.info("No network connections available")
                return
            
            # Calculate layout
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Extract coordinates
            x_coords = [pos[node][0] for node in G.nodes()]
            y_coords = [pos[node][1] for node in G.nodes()]
            
            # Create edge traces
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            # Create figure
            fig = go.Figure()
            
            # Add edges
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines'
            ))
            
            # Add nodes
            node_colors = ['red' if node == center_node else 'lightblue' for node in G.nodes()]
            
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                mode='markers+text',
                hoverinfo='text',
                text=list(G.nodes()),
                textposition="middle center",
                marker=dict(
                    size=20,
                    color=node_colors,
                    line=dict(width=2, color='black')
                )
            ))
            
            fig.update_layout(
                title="Alumni Network Connections",
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="Network visualization of alumni connections",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(color='gray', size=12)
                )],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating network graph: {e}")
    
    def create_progress_indicator(self, current_step: int, total_steps: int, step_names: List[str]):
        """Create a progress indicator for multi-step processes"""
        
        progress = current_step / total_steps
        
        st.progress(progress)
        
        # Step indicators
        cols = st.columns(total_steps)
        
        for i, (col, step_name) in enumerate(zip(cols, step_names)):
            with col:
                if i < current_step:
                    st.success(f"✅ {step_name}")
                elif i == current_step:
                    st.info(f"🔄 {step_name}")
                else:
                    st.text(f"⏳ {step_name}")
    
    def create_filter_sidebar(self):
        """Create a comprehensive filter sidebar"""
        
        with st.sidebar:
            st.header("🔍 Filters")
            
            # Company filter
            companies = st.multiselect(
                "Companies",
                options=["Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Adobe", "Salesforce", "Tesla", "Zoho"],
                help="Filter alumni by current company"
            )
            
            # Department filter
            department = st.selectbox(
                "Department",
                options=["All", "Computer Science", "Electrical Engineering", "Mechanical Engineering", 
                        "Business Administration", "Data Science", "Information Technology"],
                help="Filter by graduation department"
            )
            
            # Graduation year range
            st.subheader("Graduation Year")
            year_range = st.slider(
                "Year Range",
                min_value=2010,
                max_value=2025,
                value=(2018, 2024),
                help="Select graduation year range"
            )
            
            # Experience level
            experience_levels = st.multiselect(
                "Experience Level",
                options=["junior", "mid", "senior", "executive", "director"],
                default=["mid", "senior"],
                help="Filter by seniority level"
            )
            
            # Skills filter
            common_skills = [
                "Python", "Java", "JavaScript", "React", "Node.js", "SQL", "Machine Learning",
                "Data Science", "Cloud Computing", "DevOps", "Mobile Development", "UI/UX"
            ]
            
            selected_skills = st.multiselect(
                "Skills",
                options=common_skills,
                help="Filter by specific skills"
            )
            
            # Response rate filter
            min_response_rate = st.slider(
                "Minimum Response Rate",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Filter by historical response rate"
            )
            
            # Other filters
            hiring_authority = st.checkbox("Has Hiring Authority")
            mentorship_available = st.checkbox("Offers Mentorship")
            
            # Return filter dictionary
            filters = {
                'companies': companies,
                'department': department if department != "All" else None,
                'min_graduation_year': year_range[0],
                'max_graduation_year': year_range[1],
                'experience_levels': experience_levels,
                'skills': selected_skills,
                'min_response_rate': min_response_rate,
                'hiring_authority': hiring_authority,
                'mentorship_available': mentorship_available
            }
            
            # Clear filters button
            if st.button("Clear All Filters"):
                st.rerun()
            
            return filters
    
    def create_search_results_table(self, results: List[Dict[str, Any]], selectable: bool = False):
        """Create an interactive table for search results"""
        
        if not results:
            st.info("No results to display")
            return None
        
        # Prepare data for display
        display_data = []
        for i, result in enumerate(results):
            metadata = result.get('metadata', result)
            
            row = {
                'Select': False if selectable else None,
                'Rank': i + 1,
                'Name': metadata.get('name', 'Unknown'),
                'Company': metadata.get('current_company', 'Unknown'),
                'Position': metadata.get('current_position', 'Unknown'),
                'Department': metadata.get('department', 'Unknown'),
                'Grad Year': metadata.get('graduation_year', 'Unknown'),
                'Match Score': result.get('composite_score', 0),
                'Response Rate': metadata.get('response_rate', 0),
                'Hiring Authority': metadata.get('hiring_authority', False),
                'Skills': ', '.join(metadata.get('skills', [])[:3]),
                'id': metadata.get('id')
            }
            
            if not selectable:
                row.pop('Select')
            
            display_data.append(row)
        
        df = pd.DataFrame(display_data)
        
        # Configure columns
        column_config = {
            "Match Score": st.column_config.ProgressColumn(
                "Match Score",
                help="Overall compatibility score",
                min_value=0,
                max_value=1,
                format="%.2f"
            ),
            "Response Rate": st.column_config.ProgressColumn(
                "Response Rate",
                help="Historical response rate",
                min_value=0,
                max_value=1,
                format="%.1%"
            ),
            "Hiring Authority": st.column_config.CheckboxColumn(
                "Hiring Authority",
                help="Has hiring decision-making authority"
            )
        }
        
        if selectable:
            column_config["Select"] = st.column_config.CheckboxColumn(
                "Select",
                help="Select for batch operations"
            )
        
        # Display table
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            use_container_width=True,
            height=400,
            hide_index=True,
            disabled=["Rank", "Name", "Company", "Position", "Department", "Grad Year", "Match Score", "Response Rate", "Hiring Authority", "Skills", "id"] if selectable else True
        )
        
        if selectable:
            # Return selected items
            selected_items = edited_df[edited_df['Select'] == True]
            return selected_items['id'].tolist() if not selected_items.empty else []
        
        return None
    
    def create_email_preview(self, email_content: str, editable: bool = True):
        """Create an email preview component"""
        
        st.subheader("📧 Email Preview")
        
        # Parse email components
        lines = email_content.split('\n')
        subject_line = ""
        body = email_content
        
        for line in lines:
            if line.startswith('Subject:'):
                subject_line = line.replace('Subject:', '').strip()
                break
        
        # Subject line
        if subject_line:
            st.markdown(f"**Subject:** {subject_line}")
            st.divider()
        
        # Email body
        if editable:
            edited_content = st.text_area(
                "Email Content (editable):",
                value=body,
                height=300,
                help="You can edit the email content here before copying"
            )
            
            # Copy button
            if st.button("📋 Copy to Clipboard"):
                st.code(edited_content, language=None)
                st.success("Email copied! Use Ctrl+A, Ctrl+C to copy from the code block above.")
            
            return edited_content
        else:
            st.markdown(body)
            return email_content
    
    def create_analytics_dashboard(self, stats: Dict[str, Any]):
        """Create a comprehensive analytics dashboard"""
        
        st.header("📊 Analytics Dashboard")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Alumni",
                stats.get('total_alumni', 0),
                delta="+12 this month"
            )
        
        with col2:
            st.metric(
                "Active Students", 
                stats.get('total_students', 0),
                delta="+5 this week"
            )
        
        with col3:
            st.metric(
                "Successful Referrals",
                stats.get('total_referrals', 0),
                delta="+3 this month"
            )
        
        with col4:
            success_rate = 0.67  # This would be calculated from actual data
            st.metric(
                "Success Rate",
                f"{success_rate:.1%}",
                delta="+5.2%"
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            if stats.get('top_companies'):
                self.create_company_distribution_chart(stats['top_companies'])
        
        with col2:
            if stats.get('graduation_years'):
                self.create_graduation_timeline(stats['graduation_years'])
        
        # Skills analysis
        if stats.get('top_skills'):
            self.create_skill_cloud(stats['top_skills'], "Most Common Skills")
    
    def create_status_indicator(self, status: str, message: str = ""):
        """Create a status indicator with different styles"""
        
        status_configs = {
            'success': {'icon': '✅', 'color': 'green'},
            'warning': {'icon': '⚠️', 'color': 'orange'},
            'error': {'icon': '❌', 'color': 'red'},
            'info': {'icon': 'ℹ️', 'color': 'blue'},
            'loading': {'icon': '🔄', 'color': 'gray'}
        }
        
        config = status_configs.get(status, status_configs['info'])
        
        if status == 'success':
            st.success(f"{config['icon']} {message}")
        elif status == 'warning':
            st.warning(f"{config['icon']} {message}")
        elif status == 'error':
            st.error(f"{config['icon']} {message}")
        else:
            st.info(f"{config['icon']} {message}")
    
    def create_action_buttons(self, actions: List[Dict[str, Any]], key_prefix: str = ""):
        """Create a row of action buttons"""
        
        if not actions:
            return {}
        
        cols = st.columns(len(actions))
        results = {}
        
        for i, (col, action) in enumerate(zip(cols, actions)):
            with col:
                button_key = f"{key_prefix}_{action['key']}_{i}"
                
                if st.button(
                    action['label'],
                    key=button_key,
                    help=action.get('help', ''),
                    type=action.get('type', 'secondary'),
                    use_container_width=True
                ):
                    results[action['key']] = True
        
        return results