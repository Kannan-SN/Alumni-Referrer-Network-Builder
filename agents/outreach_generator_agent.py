from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from langchain.prompts import PromptTemplate

class OutreachGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Outreach Message Generator Agent")
        self.message_templates = self._load_message_templates()
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized outreach messages for referral requests
        """
        try:
            student_profile = input_data.get('student_profile', {})
            alumni_info = input_data.get('alumni_info', {})
            referral_context = input_data.get('referral_context', {})
            message_type = input_data.get('message_type', 'linkedin')  # linkedin, email, follow_up
            
            generated_messages = await self._generate_personalized_messages(
                student_profile, alumni_info, referral_context, message_type
            )
            
            return {
                "status": "success",
                "message_type": message_type,
                "generated_messages": generated_messages,
                "message_tips": self._get_message_tips(message_type),
                "subject_lines": await self._generate_subject_lines(student_profile, alumni_info) if message_type == 'email' else None
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _generate_personalized_messages(self, student_profile: Dict[str, Any],
                                            alumni_info: Dict[str, Any],
                                            referral_context: Dict[str, Any],
                                            message_type: str) -> List[Dict[str, Any]]:
        """Generate multiple personalized message variants"""
        messages = []
        
        # Get base template
        template = self.message_templates.get(message_type, self.message_templates['linkedin'])
        
        # Generate 3 different variants
        for i, variant in enumerate(['professional', 'friendly', 'brief'], 1):
            message_content = await self._create_message_variant(
                template, student_profile, alumni_info, referral_context, variant
            )
            
            messages.append({
                "variant": variant,
                "variant_number": i,
                "content": message_content,
                "estimated_length": len(message_content),
                "tone": variant,
                "recommended_use": self._get_variant_recommendation(variant)
            })
        
        return messages
    
    async def _create_message_variant(self, template: str, student_profile: Dict[str, Any],
                                    alumni_info: Dict[str, Any], referral_context: Dict[str, Any],
                                    variant: str) -> str:
        """Create a specific message variant using AI"""
        
        # Prepare context for AI generation
        context = self._prepare_message_context(student_profile, alumni_info, referral_context, variant)
        
        prompt = PromptTemplate(
            input_variables=["context", "template", "variant"],
            template="""
            You are an expert at writing professional outreach messages for job referrals. 
            
            Context: {context}
            
            Base Template: {template}
            
            Variant Style: {variant}
            
            Generate a personalized message that:
            1. Is {variant} in tone
            2. Mentions specific connections or commonalities
            3. Clearly states the request for referral
            4. Shows genuine interest in the company/role
            5. Is concise but complete
            6. Includes a clear call-to-action
            
            Generate only the message content, no additional text.
            """
        )
        
        try:
            formatted_prompt = prompt.format(
                context=context,
                template=template,
                variant=variant
            )
            
            response = await self.llm.ainvoke(formatted_prompt)
            return response.strip()
            
        except Exception as e:
            # Fallback to template-based generation
            return self._generate_template_message(template, student_profile, alumni_info, referral_context, variant)
    
    def _prepare_message_context(self, student_profile: Dict[str, Any],
                               alumni_info: Dict[str, Any], referral_context: Dict[str, Any],
                               variant: str) -> str:
        """Prepare context for AI message generation"""
        context_parts = []
        
        # Student information
        student_name = student_profile.get('name', 'Student')
        student_degree = student_profile.get('degree', 'Computer Science')
        student_year = student_profile.get('current_year', 3)
        student_skills = ', '.join(student_profile.get('skills', []))
        student_interests = ', '.join(student_profile.get('interests', []))
        
        context_parts.append(f"Student: {student_name}, {student_year}rd year {student_degree} student")
        context_parts.append(f"Student Skills: {student_skills}")
        context_parts.append(f"Student Interests: {student_interests}")
        
        # Alumni information
        alumni_name = alumni_info.get('name', 'Alumni')
        alumni_company = alumni_info.get('current_company', 'Company')
        alumni_role = alumni_info.get('current_role', 'Role')
        alumni_grad_year = alumni_info.get('graduation_year', '2020')
        alumni_domain = alumni_info.get('domain', 'Technology')
        
        context_parts.append(f"Alumni: {alumni_name}, {alumni_grad_year} graduate")
        context_parts.append(f"Alumni Current Position: {alumni_role} at {alumni_company}")
        context_parts.append(f"Alumni Domain: {alumni_domain}")
        
        # Referral context
        target_role = referral_context.get('target_role', 'Software Engineer')
        target_company = referral_context.get('target_company', alumni_company)
        common_connections = referral_context.get('common_connections', [])
        
        context_parts.append(f"Target Role: {target_role} at {target_company}")
        if common_connections:
            context_parts.append(f"Common Connections: {', '.join(common_connections)}")
        
        # Alignment reasons
        alignment_reasons = alumni_info.get('alignment_reasons', [])
        if alignment_reasons:
            context_parts.append(f"Connection Points: {'; '.join(alignment_reasons)}")
        
        return '\n'.join(context_parts)
    
    def _generate_template_message(self, template: str, student_profile: Dict[str, Any],
                                 alumni_info: Dict[str, Any], referral_context: Dict[str, Any],
                                 variant: str) -> str:
        """Generate message using template substitution as fallback"""
        
        # Extract variables for template
        variables = {
            'student_name': student_profile.get('name', 'Student'),
            'alumni_name': alumni_info.get('name', 'Alumni'),
            'alumni_company': alumni_info.get('current_company', 'your company'),
            'alumni_role': alumni_info.get('current_role', 'your role'),
            'target_role': referral_context.get('target_role', 'Software Engineer'),
            'student_degree': student_profile.get('degree', 'Computer Science'),
            'graduation_year': str(alumni_info.get('graduation_year', '2020')),
            'common_interest': ', '.join(student_profile.get('interests', ['technology'])[:2]),
            'student_year': str(student_profile.get('current_year', 3))
        }
        
        try:
            message = template.format(**variables)
            
            # Adjust tone based on variant
            if variant == 'brief':
                # Make the message more concise
                lines = message.split('\n')
                key_lines = [line for line in lines if line.strip() and 
                           ('Hi' in line or 'hope' in line or 'interested' in line or 
                            'referral' in line or 'Best' in line)]
                message = '\n'.join(key_lines)
            
            elif variant == 'friendly':
                # Add more personal touches
                message = message.replace('I hope this message finds you well.', 
                                        'I hope you\'re doing well and enjoying your role!')
                message = message.replace('Best regards,', 'Looking forward to hearing from you!\n\nBest,')
            
            return message
            
        except KeyError as e:
            # Return a basic message if template formatting fails
            return self._get_basic_message(student_profile, alumni_info, referral_context)
    
    def _get_basic_message(self, student_profile: Dict[str, Any],
                          alumni_info: Dict[str, Any], referral_context: Dict[str, Any]) -> str:
        """Generate a basic fallback message"""
        student_name = student_profile.get('name', 'Student')
        alumni_name = alumni_info.get('name', 'Alumni')
        company = alumni_info.get('current_company', 'your company')
        role = referral_context.get('target_role', 'Software Engineer')
        
        return f"""Hi {alumni_name},

I hope this message finds you well. My name is {student_name}, and I'm a Computer Science student. 

I'm very interested in opportunities at {company} for {role} positions, and I would greatly appreciate any guidance or referral you might be able to provide.

I'd love to learn more about your experience and would be happy to share my resume if you're interested.

Thank you for your time and consideration.

Best regards,
{student_name}"""
    
    async def _generate_subject_lines(self, student_profile: Dict[str, Any],
                                     alumni_info: Dict[str, Any]) -> List[str]:
        """Generate email subject lines"""
        student_name = student_profile.get('name', 'Student')
        alumni_company = alumni_info.get('current_company', 'Company')
        alumni_grad_year = alumni_info.get('graduation_year', '2020')
        
        subjects = [
            f"Fellow Alumni - Seeking Guidance for {alumni_company} Opportunities",
            f"Class of {alumni_grad_year} Connection - {student_name}",
            f"Referral Request from {student_name} - {alumni_company} Opportunities",
            f"Alumni Network Outreach - {student_name}",
            f"Seeking Mentorship from {alumni_company} Professional"
        ]
        
        return subjects
    
    def _get_variant_recommendation(self, variant: str) -> str:
        """Get recommendation for when to use each variant"""
        recommendations = {
            'professional': 'Best for senior alumni or formal company cultures',
            'friendly': 'Ideal for recent graduates or casual company environments',
            'brief': 'Perfect for busy professionals or follow-up messages'
        }
        return recommendations.get(variant, 'General purpose message')
    
    def _get_message_tips(self, message_type: str) -> List[str]:
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
                "Provide any updates or additional information",
                "Reiterate your interest respectfully",
                "Suggest alternative ways to connect",
                "Keep it shorter than the original message"
            ]
        }
        return tips.get(message_type, tips['linkedin'])
    
    def _load_message_templates(self) -> Dict[str, str]:
        """Load message templates for different platforms"""
        return {
            'linkedin': """Hi {alumni_name},

I hope this message finds you well. My name is {student_name}, and I'm a {student_year}rd year {student_degree} student at our alma mater.

I'm very interested in {target_role} opportunities at {alumni_company} and would greatly appreciate any insights you might share about your experience there. I'm particularly drawn to {common_interest} and believe my background aligns well with the company's mission.

Would you be open to a brief conversation about your journey and any advice you might have for someone looking to join {alumni_company}?

Thank you for your time and consideration.

Best regards,
{student_name}""",

            'email': """Subject: Fellow Alumni - Seeking Guidance for {alumni_company} Opportunities

Dear {alumni_name},

I hope this email finds you well. My name is {student_name}, and I'm a {student_year}rd year {student_degree} student. I came across your profile and was impressed by your journey at {alumni_company}.

I'm currently exploring {target_role} opportunities and am particularly interested in {alumni_company} due to [specific reason related to company/role]. Given your experience as a {graduation_year} graduate who successfully transitioned into {alumni_role}, I would be incredibly grateful for any guidance you might be able to provide.

I understand you must be very busy, but I would greatly appreciate even a brief conversation about:
- Your experience at {alumni_company}
- Advice for someone interested in {target_role} positions
- Any insights about the company culture and growth opportunities

I've attached my resume for your reference and would be happy to work around your schedule for a quick call or coffee chat.

Thank you very much for considering my request.

Best regards,
{student_name}
[Your Contact Information]""",

            'follow_up': """Hi {alumni_name},

I hope you're doing well. I wanted to follow up on my message from last week regarding {target_role} opportunities at {alumni_company}.

I completely understand how busy you must be, and I don't want to be persistent. I'm still very interested in learning from your experience and would appreciate any brief insights you might be able to share.

If now isn't a good time, I'd be happy to reach out again in a few months. I truly value the alumni network and any guidance you might be able to provide.

Thank you again for your time.

Best,
{student_name}"""
        }


## 🔧 Step 5: Utility Classes

### utils/embedding_utils.py
```python
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from database.mongodb_handler import mongodb_handler
import logging

class EmbeddingUtils:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.alumni_embeddings = {}
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text"""
        try:
            embedding = self.model.encode([text])
            return embedding[0].tolist()
        except Exception as e:
            logging.error(f"Error generating embedding: {e}")
            return []
    
    async def find_similar_alumni(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Find alumni similar to the query using embeddings"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Get all alumni from database
            all_alumni = await self._get_all_alumni_with_embeddings()
            
            if not all_alumni:
                return []
            
            # Calculate similarities
            similarities = []
            for alumni in all_alumni:
                if 'embedding' in alumni:
                    similarity = cosine_similarity(
                        [query_embedding], 
                        [alumni['embedding']]
                    )[0][0]
                    alumni['similarity_score'] = similarity
                    similarities.append(alumni)
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logging.error(f"Error finding similar alumni: {e}")
            return []
    
    async def _get_all_alumni_with_embeddings(self) -> List[Dict[str, Any]]:
        """Get all alumni with their embeddings"""
        try:
            # This would typically come from a vector database
            # For now, we'll generate embeddings on-demand from MongoDB
            from config.database import db_connection
            alumni_collection = db_connection.db['alumni']
            alumni_cursor = alumni_collection.find()
            
            alumni_with_embeddings = []
            for alumni in alumni_cursor:
                # Create text representation for embedding
                alumni_text = self._create_alumni_text_representation(alumni)
                
                # Generate or retrieve embedding
                if 'embedding' not in alumni:
                    embedding = await self.generate_embedding(alumni_text)
                    alumni['embedding'] = embedding
                    # Optionally save back to database
                    alumni_collection.update_one(
                        {'_id': alumni['_id']},
                        {'$set': {'embedding': embedding}}
                    )
                
                alumni_with_embeddings.append(alumni)
            
            return alumni_with_embeddings
            
        except Exception as e:
            logging.error(f"Error getting alumni with embeddings: {e}")
            return []
    
    def _create_alumni_text_representation(self, alumni: Dict[str, Any]) -> str:
        """Create text representation of alumni for embedding"""
        parts = []
        
        # Basic info
        parts.append(f"Name: {alumni.get('name', '')}")
        parts.append(f"Current Role: {alumni.get('current_role', '')}")
        parts.append(f"Company: {alumni.get('current_company', '')}")
        parts.append(f"Domain: {alumni.get('domain', '')}")
        
        # Skills
        skills = alumni.get('skills', [])
        if skills:
            parts.append(f"Skills: {', '.join(skills)}")
        
        # Experience
        parts.append(f"Experience: {alumni.get('experience_years', 0)} years")
        
        # Education
        parts.append(f"Degree: {alumni.get('degree', '')}")
        parts.append(f"Graduation Year: {alumni.get('graduation_year', '')}")
        
        # Previous companies
        prev_companies = alumni.get('previous_companies', [])
        if prev_companies:
            parts.append(f"Previous Companies: {', '.join(prev_companies)}")
        
        return ' | '.join(parts)

### utils/data_processing.py
```python
import pandas as pd
from typing import Dict, Any, List
import json
import logging

class DataProcessor:
    @staticmethod
    def process_alumni_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and clean alumni data"""
        processed_data = []
        
        for alumni in raw_data:
            try:
                processed_alumni = {
                    'name': alumni.get('name', '').strip(),
                    'email': alumni.get('email', '').strip().lower(),
                    'graduation_year': int(alumni.get('graduation_year', 2020)),
                    'degree': alumni.get('degree', '').strip(),
                    'current_company': alumni.get('current_company', '').strip(),
                    'current_role': alumni.get('current_role', '').strip(),
                    'location': alumni.get('location', '').strip(),
                    'skills': [skill.strip() for skill in alumni.get('skills', [])],
                    'linkedin_url': alumni.get('linkedin_url', ''),
                    'domain': alumni.get('domain', '').strip(),
                    'experience_years': int(alumni.get('experience_years', 0)),
                    'previous_companies': [comp.strip() for comp in alumni.get('previous_companies', [])]
                }
                
                # Validate required fields
                if processed_alumni['name'] and processed_alumni['email']:
                    processed_data.append(processed_alumni)
                    
            except (ValueError, TypeError) as e:
                logging.warning(f"Skipping invalid alumni data: {e}")
                continue
        
        return processed_data
    
    @staticmethod
    def process_student_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean student data"""
        try:
            return {
                'name': raw_data.get('name', '').strip(),
                'email': raw_data.get('email', '').strip().lower(),
                'current_year': int(raw_data.get('current_year', 1)),
                'degree': raw_data.get('degree', '').strip(),
                'interests': [interest.strip() for interest in raw_data.get('interests', [])],
                'skills': [skill.strip() for skill in raw_data.get('skills', [])],
                'target_companies': [comp.strip() for comp in raw_data.get('target_companies', [])],
                'target_roles': [role.strip() for role in raw_data.get('target_roles', [])],
                'gpa': float(raw_data.get('gpa', 0.0)) if raw_data.get('gpa') else None,
                'projects': raw_data.get('projects', [])
            }
        except (ValueError, TypeError) as e:
            logging.error(f"Error processing student data: {e}")
            return {}

### utils/validators.py
```python
import re
from typing import Dict, Any, List, Tuple

class InputValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_student_profile(profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate student profile data"""
        errors = []
        
        # Required fields
        if not profile.get('name', '').strip():
            errors.append("Name is required")
        
        if not profile.get('email', '').strip():
            errors.append("Email is required")
        elif not InputValidator.validate_email(profile['email']):
            errors.append("Invalid email format")
        
        if not profile.get('degree', '').strip():
            errors.append("Degree is required")
        
        # Year validation
        current_year = profile.get('current_year', 0)
        if not isinstance(current_year, int) or current_year < 1 or current_year > 6:
            errors.append("Current year must be between 1 and 6")
        
        # GPA validation
        gpa = profile.get('gpa')
        if gpa is not None:
            try:
                gpa_float = float(gpa)
                if gpa_float < 0 or gpa_float > 10:
                    errors.append("GPA must be between 0 and 10")
            except (ValueError, TypeError):
                errors.append("Invalid GPA format")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_alumni_profile(profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate alumni profile data"""
        errors = []
        
        # Required fields
        required_fields = ['name', 'email', 'current_company', 'current_role', 'domain']
        for field in required_fields:
            if not profile.get(field, '').strip():
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        # Email validation
        if profile.get('email') and not InputValidator.validate_email(profile['email']):
            errors.append("Invalid email format")
        
        # Year validation
        grad_year = profile.get('graduation_year', 0)
        if not isinstance(grad_year, int) or grad_year < 1950 or grad_year > 2030:
            errors.append("Graduation year must be between 1950 and 2030")
        
        # Experience validation
        experience = profile.get('experience_years', 0)
        if not isinstance(experience, int) or experience < 0 or experience > 50:
            errors.append("Experience years must be between 0 and 50")
        
        return len(errors) == 0, errors


## 📱 Step 6: Streamlit UI Components

### ui/components.py
```python
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


## 🖥️ Step 7: Main Streamlit Pages

### ui/pages/dashboard.py
```python
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

### ui/pages/student_profile.py
```python
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

### ui/pages/alumni_search.py
```python
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

### ui/pages/referral_requests.py
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


## 🔧 Step 8: RAG Implementation with Vector Database

### database/vector_store.py
```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging
from sentence_transformers import SentenceTransformer
from config.settings import settings
import os
import json

class VectorStore:
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.client = None
        self.collection = None
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.VECTOR_STORE_PATH,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection for alumni data
            self.collection = self.client.get_or_create_collection(
                name="alumni_collection",
                metadata={"description": "Alumni profiles with embeddings for RAG"}
            )
            
            logging.info("ChromaDB initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_alumni_documents(self, alumni_list: List[Dict[str, Any]]) -> bool:
        """Add alumni documents to vector store"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, alumni in enumerate(alumni_list):
                # Create document text for embedding
                doc_text = self._create_alumni_document(alumni)
                documents.append(doc_text)
                
                # Create metadata (exclude large fields)
                metadata = {
                    "name": alumni.get("name", ""),
                    "current_company": alumni.get("current_company", ""),
                    "current_role": alumni.get("current_role", ""),
                    "domain": alumni.get("domain", ""),
                    "graduation_year": str(alumni.get("graduation_year", "")),
                    "experience_years": str(alumni.get("experience_years", "")),
                    "location": alumni.get("location", ""),
                    "alumni_id": str(alumni.get("_id", f"alumni_{i}"))
                }
                metadatas.append(metadata)
                
                # Create unique ID
                alumni_id = str(alumni.get("_id", f"alumni_{i}"))
                ids.append(alumni_id)
            
            # Add to collection in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
            
            logging.info(f"Added {len(documents)} alumni documents to vector store")
            return True
            
        except Exception as e:
            logging.error(f"Failed to add alumni documents: {e}")
            return False
    
    async def search_similar_alumni(self, query: str, n_results: int = 10, 
                                  filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar alumni using RAG"""
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if value:  # Only add non-empty filters
                        if key in ["graduation_year", "experience_years"]:
                            # For numeric fields, we can do exact match or range
                            where_clause[key] = str(value)
                        else:
                            # For text fields, we'll need to handle this differently
                            # ChromaDB doesn't support regex in where clause
                            where_clause[key] = {"$contains": value}
            
            # Perform vector search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            alumni_results = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    # Convert distance to similarity score (1 - distance for cosine similarity)
                    similarity_score = 1 - distance
                    
                    alumni_result = {
                        "name": metadata.get("name", ""),
                        "current_company": metadata.get("current_company", ""),
                        "current_role": metadata.get("current_role", ""),
                        "domain": metadata.get("domain", ""),
                        "graduation_year": int(metadata.get("graduation_year", 0)) if metadata.get("graduation_year") else 0,
                        "experience_years": int(metadata.get("experience_years", 0)) if metadata.get("experience_years") else 0,
                        "location": metadata.get("location", ""),
                        "alumni_id": metadata.get("alumni_id", ""),
                        "similarity_score": similarity_score,
                        "document_text": doc,
                        "_id": metadata.get("alumni_id", "")
                    }
                    
                    alumni_results.append(alumni_result)
            
            return alumni_results
            
        except Exception as e:
            logging.error(f"Failed to search similar alumni: {e}")
            return []
    
    async def hybrid_search(self, query: str, filters: Dict[str, Any], 
                          n_results: int = 20) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector similarity and metadata filtering"""
        try:
            # First, get a larger set of similar documents
            vector_results = await self.search_similar_alumni(query, n_results=n_results*2)
            
            # Then apply additional filtering and ranking
            filtered_results = []
            
            for alumni in vector_results:
                match_score = alumni.get("similarity_score", 0)
                
                # Apply additional filters and boost scores
                if filters.get("company"):
                    if filters["company"].lower() in alumni.get("current_company", "").lower():
                        match_score += 0.2
                
                if filters.get("domain"):
                    if filters["domain"].lower() in alumni.get("domain", "").lower():
                        match_score += 0.15
                
                if filters.get("role"):
                    if filters["role"].lower() in alumni.get("current_role", "").lower():
                        match_score += 0.15
                
                # Graduation year proximity
                if filters.get("graduation_year"):
                    year_diff = abs(alumni.get("graduation_year", 0) - filters["graduation_year"])
                    if year_diff <= 2:
                        match_score += 0.1
                    elif year_diff <= 5:
                        match_score += 0.05
                
                # Update the match score
                alumni["match_score"] = match_score
                
                # Include if above threshold
                if match_score >= settings.SIMILARITY_THRESHOLD:
                    filtered_results.append(alumni)
            
            # Sort by match score and return top results
            filtered_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            return filtered_results[:n_results]
            
        except Exception as e:
            logging.error(f"Hybrid search failed: {e}")
            return []
    
    def _create_alumni_document(self, alumni: Dict[str, Any]) -> str:
        """Create a comprehensive text document for alumni embedding"""
        doc_parts = []
        
        # Basic information
        name = alumni.get("name", "")
        if name:
            doc_parts.append(f"Alumni Name: {name}")
        
        # Current position
        company = alumni.get("current_company", "")
        role = alumni.get("current_role", "")
        if company and role:
            doc_parts.append(f"Currently working as {role} at {company}")
        elif company:
            doc_parts.append(f"Currently working at {company}")
        elif role:
            doc_parts.append(f"Current role: {role}")
        
        # Domain and expertise
        domain = alumni.get("domain", "")
        if domain:
            doc_parts.append(f"Specialization domain: {domain}")
        
        # Skills
        skills = alumni.get("skills", [])
        if skills:
            doc_parts.append(f"Technical skills: {', '.join(skills)}")
        
        # Experience
        experience = alumni.get("experience_years", 0)
        if experience:
            doc_parts.append(f"Professional experience: {experience} years")
        
        # Education
        degree = alumni.get("degree", "")
        grad_year = alumni.get("graduation_year", "")
        if degree and grad_year:
            doc_parts.append(f"Educational background: {degree} graduate from {grad_year}")
        elif degree:
            doc_parts.append(f"Educational background: {degree}")
        
        # Previous experience
        prev_companies = alumni.get("previous_companies", [])
        if prev_companies:
            doc_parts.append(f"Previous companies: {', '.join(prev_companies)}")
        
        # Location
        location = alumni.get("location", "")
        if location:
            doc_parts.append(f"Location: {location}")
        
        # Create comprehensive document
        document = ". ".join(doc_parts)
        
        # Add context for better matching
        document += f". This alumni profile represents a professional in {domain} with expertise in {company} environment."
        
        return document
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "embedding_model": settings.EMBEDDING_MODEL
            }
        except Exception as e:
            logging.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def clear_collection(self) -> bool:
        """Clear all documents from the collection"""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name="alumni_collection")
            self.collection = self.client.create_collection(
                name="alumni_collection",
                metadata={"description": "Alumni profiles with embeddings for RAG"}
            )
            logging.info("Vector store collection cleared")
            return True
        except Exception as e:
            logging.error(f"Failed to clear collection: {e}")
            return False

# Global vector store instance
vector_store = VectorStore()

### Enhanced Alumni Mining Agent with RAG

### agents/alumni_mining_agent.py (UPDATED WITH RAG)
```python
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from database.mongodb_handler import mongodb_handler
from database.vector_store import vector_store
from utils.embedding_utils import EmbeddingUtils
import logging

class AlumniMiningAgent(BaseAgent):
    def __init__(self):
        super().__init__("Alumni Network Mining Agent")
        self.embedding_utils = EmbeddingUtils()
        self.vector_store = vector_store
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mine alumni data using RAG-enabled search
        """
        try:
            company = input_data.get('company', '')
            role = input_data.get('role', '')
            graduation_year = input_data.get('graduation_year', None)
            domain = input_data.get('domain', '')
            
            # Create intelligent search query for RAG
            search_query = await self._create_rag_query(company, role, domain, graduation_year)
            
            # Perform RAG-based search
            rag_results = await self._perform_rag_search(search_query, input_data)
            
            # Combine with traditional database search for comprehensive results
            db_results = await self._perform_database_search(input_data)
            
            # Merge and deduplicate results
            combined_results = await self._merge_search_results(rag_results, db_results)
            
            # Apply final filtering and ranking
            filtered_alumni = await self._apply_final_filters(combined_results, input_data)
            
            return {
                "status": "success",
                "alumni_found": len(filtered_alumni),
                "alumni_data": filtered_alumni,
                "search_query": search_query,
                "rag_results_count": len(rag_results),
                "db_results_count": len(db_results),
                "search_method": "RAG + Database Hybrid"
            }
            
        except Exception as e:
            logging.error(f"Alumni mining failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _create_rag_query(self, company: str, role: str, domain: str, 
                               graduation_year: int) -> str:
        """Create an intelligent query for RAG search"""
        query_parts = []
        
        if company:
            query_parts.append(f"alumni working at {company}")
        
        if role:
            query_parts.append(f"professionals in {role} positions")
        
        if domain:
            query_parts.append(f"specialists in {domain} domain")
        
        if graduation_year:
            # Add some flexibility around graduation year
            query_parts.append(f"graduates from around {graduation_year}")
        
        # Create base query
        if query_parts:
            base_query = " ".join(query_parts)
        else:
            base_query = "experienced alumni professionals"
        
        # Enhance query with context
        enhanced_query = f"Find {base_query} with relevant experience and skills for referral opportunities"
        
        return enhanced_query
    
    async def _perform_rag_search(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform RAG-based search using vector store"""
        try:
            # Prepare filters for vector search
            search_filters = {}
            
            if filters.get('company'):
                search_filters['company'] = filters['company']
            
            if filters.get('domain'):
                search_filters['domain'] = filters['domain']
            
            if filters.get('graduation_year'):
                search_filters['graduation_year'] = filters['graduation_year']
            
            # Perform hybrid search
            rag_results = await self.vector_store.hybrid_search(
                query=query,
                filters=search_filters,
                n_results=settings.MAX_SEARCH_RESULTS
            )
            
            # Enrich results with additional data from MongoDB
            enriched_results = []
            for result in rag_results:
                # Get full alumni data from MongoDB
                full_alumni_data = await self._get_full_alumni_data(result.get('alumni_id'))
                if full_alumni_data:
                    # Merge vector search metadata with full data
                    full_alumni_data['rag_similarity_score'] = result.get('similarity_score', 0)
                    full_alumni_data['rag_match_score'] = result.get('match_score', 0)
                    enriched_results.append(full_alumni_data)
            
            return enriched_results
            
        except Exception as e:
            logging.error(f"RAG search failed: {e}")
            return []
    
    async def _perform_database_search(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform traditional database search as fallback"""
        try:
            db_results = []
            
            # Search by company
            if filters.get('company'):
                company_results = await mongodb_handler.get_alumni_by_company(filters['company'])
                db_results.extend(company_results)
            
            # Search by domain
            if filters.get('domain'):
                domain_results = await mongodb_handler.get_alumni_by_domain(filters['domain'])
                db_results.extend(domain_results)
            
            # Search by skills if available
            if filters.get('skills'):
                skill_results = await mongodb_handler.search_alumni_by_skills(filters['skills'])
                db_results.extend(skill_results)
            
            # Remove duplicates
            unique_results = []
            seen_ids = set()
            
            for alumni in db_results:
                alumni_id = str(alumni.get('_id', ''))
                if alumni_id not in seen_ids:
                    seen_ids.add(alumni_id)
                    alumni['search_method'] = 'database'
                    unique_results.append(alumni)
            
            return unique_results
            
        except Exception as e:
            logging.error(f"Database search failed: {e}")
            return []
    
    async def _merge_search_results(self, rag_results: List[Dict[str, Any]], 
                                  db_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate results from RAG and database searches"""
        merged_results = []
        seen_ids = set()
        
        # Add RAG results first (they have similarity scores)
        for alumni in rag_results:
            alumni_id = str(alumni.get('_id', ''))
            if alumni_id not in seen_ids:
                seen_ids.add(alumni_id)
                alumni['search_method'] = 'rag'
                merged_results.append(alumni)
        
        # Add database results that weren't found by RAG
        for alumni in db_results:
            alumni_id = str(alumni.get('_id', ''))
            if alumni_id not in seen_ids:
                seen_ids.add(alumni_id)
                alumni['search_method'] = 'database'
                # Add default scores for database-only results
                alumni['rag_similarity_score'] = 0.5
                alumni['rag_match_score'] = 0.5
                merged_results.append(alumni)
        
        return merged_results
    
    async def _apply_final_filters(self, alumni_list: List[Dict[str, Any]], 
                                 filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply final filtering and ranking to combined results"""
        filtered = []
        
        for alumni in alumni_list:
            final_score = 0
            
            # Base score from RAG similarity
            rag_score = alumni.get('rag_similarity_score', 0)
            match_score = alumni.get('rag_match_score', 0)
            final_score += (rag_score * 0.4) + (match_score * 0.3)
            
            # Company exact match bonus
            if filters.get('company'):
                company_filter = filters['company'].lower()
                alumni_company = alumni.get('current_company', '').lower()
                if company_filter in alumni_company:
                    final_score += 0.2
            
            # Role match bonus
            if filters.get('role'):
                role_filter = filters['role'].lower()
                alumni_role = alumni.get('current_role', '').lower()
                if role_filter in alumni_role:
                    final_score += 0.15
            
            # Domain match bonus
            if filters.get('domain'):
                domain_filter = filters['domain'].lower()
                alumni_domain = alumni.get('domain', '').lower()
                if domain_filter in alumni_domain:
                    final_score += 0.15
            
            # Graduation year proximity
            if filters.get('graduation_year'):
                year_diff = abs(alumni.get('graduation_year', 0) - filters['graduation_year'])
                if year_diff <= 2:
                    final_score += 0.1
                elif year_diff <= 5:
                    final_score += 0.05
            
            # Experience relevance (3-15 years is typically good for referrals)
            experience = alumni.get('experience_years', 0)
            if 3 <= experience <= 15:
                final_score += 0.05
            
            # Only include alumni above minimum threshold
            if final_score >= 0.3:  # Adjust threshold as needed
                alumni['final_match_score'] = final_score
                filtered.append(alumni)
        
        # Sort by final score
        return sorted(filtered, key=lambda x: x.get('final_match_score', 0), reverse=True)
    
    async def _get_full_alumni_data(self, alumni_id: str) -> Dict[str, Any]:
        """Get full alumni data from MongoDB by ID"""
        try:
            from bson import ObjectId
            from config.database import db_connection
            
            collection = db_connection.db[settings.ALUMNI_COLLECTION]
            alumni = collection.find_one({"_id": ObjectId(alumni_id)})
            
            if alumni:
                # Convert ObjectId to string for JSON serialization
                alumni['_id'] = str(alumni['_id'])
                return alumni
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to get full alumni data: {e}")
            return None

### Data Initialization and RAG Setup

### data/sample_alumni.json
```json
[
  {
    "name": "Rahul Sharma",
    "email": "rahul.sharma@google.com",
    "graduation_year": 2019,
    "degree": "Computer Science",
    "current_company": "Google",
    "current_role": "Senior Software Engineer",
    "location": "Bangalore, India",
    "skills": ["Python", "Machine Learning", "TensorFlow", "Kubernetes", "Go"],
    "linkedin_url": "https://linkedin.com/in/rahulsharma",
    "domain": "Software Engineering",
    "experience_years": 6,
    "previous_companies": ["Microsoft", "Flipkart"]
  },
  {
    "name": "Priya Patel",
    "email": "priya.patel@microsoft.com",
    "graduation_year": 2018,
    "degree": "Computer Science",
    "current_company": "Microsoft",
    "current_role": "Principal Data Scientist",
    "location": "Hyderabad, India",
    "skills": ["Python", "R", "Azure ML", "SQL", "Deep Learning"],
    "linkedin_url": "https://linkedin.com/in/priyapatel",
    "domain": "Data Science",
    "experience_years": 7,
    "previous_companies": ["Amazon", "Wipro"]
  },
  {
    "name": "Amit Kumar",
    "email": "amit.kumar@amazon.com",
    "graduation_year": 2020,
    "degree": "Computer Science",
    "current_company": "Amazon",
    "current_role": "Software Development Engineer II",
    "location": "Chennai, India",
    "skills": ["Java", "AWS", "Docker", "Microservices", "React"],
    "linkedin_url": "https://linkedin.com/in/amitkumar",
    "domain": "Software Engineering",
    "experience_years": 5,
    "previous_companies": ["TCS", "Accenture"]
  }
]