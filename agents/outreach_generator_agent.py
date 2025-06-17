from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from langchain.prompts import PromptTemplate
import logging

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
            logging.error(f"Outreach generation failed: {e}")
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
            logging.error(f"AI message generation failed: {e}")
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
            logging.error(f"Template formatting failed: {e}")
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
        student_degree = student_profile.get('degree', 'Computer Science')
        
        subjects = [
            f"Fellow {student_degree} Alumnus - Seeking Guidance for {alumni_company} Opportunities",
            f"Class of {alumni_grad_year} Connection - {student_name}",
            f"Referral Request from {student_name} - {alumni_company} Opportunities",
            f"Alumni Network Outreach - {student_name}",
            f"Seeking Mentorship from {alumni_company} Professional - {student_name}",
            f"{student_degree} Student Seeking {alumni_company} Referral Guidance"
        ]
        
        return subjects
    
    def _get_variant_recommendation(self, variant: str) -> str:
        """Get recommendation for when to use each variant"""
        recommendations = {
            'professional': 'Best for senior alumni (10+ years experience) or formal company cultures like banks, consulting firms, or government organizations',
            'friendly': 'Ideal for recent graduates (2-5 years experience) or casual company environments like startups, tech companies, or creative agencies',
            'brief': 'Perfect for busy professionals, C-level executives, or follow-up messages when you haven\'t received a response'
        }
        return recommendations.get(variant, 'General purpose message')
    
    def _get_message_tips(self, message_type: str) -> List[str]:
        """Get tips for the specific message type"""
        tips = {
            'linkedin': [
                "Keep initial message under 300 characters for better response rates",
                "Mention mutual connections or common experiences in your message",
                "Send connection request with a personalized note first",
                "Follow up after 1 week if no response, but don't be pushy",
                "Be genuine and specific about your interests and goals",
                "Check their recent posts and comment before reaching out",
                "Avoid generic copy-paste messages - personalization is key"
            ],
            'email': [
                "Use a clear, professional subject line that mentions your purpose",
                "Keep the email concise but informative (200-300 words max)",
                "Include your resume as a PDF attachment",
                "Use a professional email signature with contact information",
                "Follow up after 5-7 business days if no response",
                "Proofread carefully for grammar and spelling errors",
                "Send during business hours (Tuesday-Thursday, 10 AM - 2 PM)"
            ],
            'follow_up': [
                "Reference your previous message briefly but don't repeat everything",
                "Provide any updates or additional information since last contact",
                "Reiterate your interest respectfully without being demanding",
                "Suggest alternative ways to connect (phone call, coffee chat)",
                "Keep it shorter than the original message",
                "Wait at least one week before following up",
                "If no response after 2 follow-ups, move on respectfully"
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

I'm currently exploring {target_role} opportunities and am particularly interested in {alumni_company} due to their innovative work in the field. Given your experience as a {graduation_year} graduate who successfully transitioned into {alumni_role}, I would be incredibly grateful for any guidance you might be able to provide.

I understand you must be very busy, but I would greatly appreciate even a brief conversation about:
• Your experience at {alumni_company} and the company culture
• Advice for someone interested in {target_role} positions
• Any insights about growth opportunities in your domain

I've attached my resume for your reference and would be happy to work around your schedule for a quick call or coffee chat if you're in the area.

Thank you very much for considering my request. I truly value the alumni network and any guidance you might be able to share.

Best regards,
{student_name}
[Your Phone Number]
[Your Email Address]""",

            'follow_up': """Hi {alumni_name},

I hope you're doing well. I wanted to follow up on my message from last week regarding {target_role} opportunities at {alumni_company}.

I completely understand how busy you must be, and I don't want to be persistent. I'm still very interested in learning from your experience and would appreciate any brief insights you might be able to share when your schedule allows.

Since reaching out, I've [mention any updates - completed a relevant project, learned a new skill, etc.], which has further strengthened my interest in pursuing opportunities in this field.

If now isn't a good time, I'd be happy to reach out again in a few months. I truly value the alumni network and any guidance you might be able to provide.

Thank you again for your time and consideration.

Best regards,
{student_name}"""
        }
    
    def get_message_statistics(self, message_content: str) -> Dict[str, Any]:
        """Get statistics about the generated message"""
        import re
        
        stats = {
            'character_count': len(message_content),
            'word_count': len(message_content.split()),
            'sentence_count': len(re.findall(r'[.!?]+', message_content)),
            'paragraph_count': len([p for p in message_content.split('\n\n') if p.strip()]),
            'estimated_reading_time': f"{max(1, len(message_content.split()) // 200)} minute(s)",
            'formality_score': self._calculate_formality_score(message_content),
            'personalization_elements': self._count_personalization_elements(message_content)
        }
        
        return stats
    
    def _calculate_formality_score(self, message: str) -> str:
        """Calculate formality score of the message"""
        formal_indicators = ['Dear', 'Sincerely', 'Respectfully', 'grateful', 'appreciate', 'consideration']
        casual_indicators = ['Hi', 'Hey', 'Thanks', 'awesome', 'cool', 'great']
        
        formal_count = sum(1 for indicator in formal_indicators if indicator.lower() in message.lower())
        casual_count = sum(1 for indicator in casual_indicators if indicator.lower() in message.lower())
        
        if formal_count > casual_count:
            return "Formal"
        elif casual_count > formal_count:
            return "Casual"
        else:
            return "Neutral"
    
    def _count_personalization_elements(self, message: str) -> int:
        """Count personalization elements in the message"""
        elements = 0
        
        # Check for name mentions
        if '{alumni_name}' in message or any(name in message for name in ['John', 'Jane', 'Mr.', 'Ms.']):
            elements += 1
        
        # Check for company mentions
        if '{alumni_company}' in message or any(company in message for company in ['Google', 'Microsoft', 'Amazon']):
            elements += 1
        
        # Check for role mentions
        if '{target_role}' in message or 'role' in message.lower():
            elements += 1
        
        # Check for shared experiences
        if any(word in message.lower() for word in ['alumni', 'graduate', 'alma mater', 'fellow']):
            elements += 1
        
        return elements