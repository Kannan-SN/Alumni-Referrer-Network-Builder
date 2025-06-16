from typing import List, Dict, Any, Optional, Tuple
import json
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from datetime import datetime

from config import Config
from backend.vector_store import VectorStore
from backend.database import db_manager
from models.alumni import Alumni
from models.student import Student
from utils.similarity_calculator import SimilarityCalculator

class RAGEngine:
    """RAG Engine for Alumni Referrer Network using Google Gemini"""
    
    def __init__(self):
        self.config = Config()
        self.vector_store = VectorStore()
        self.db = db_manager
        self.similarity_calculator = SimilarityCalculator()
        
        # Configure Google AI
        genai.configure(api_key=self.config.GOOGLE_API_KEY)
        
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.config.GEMINI_MODEL,
            temperature=self.config.TEMPERATURE,
            google_api_key=self.config.GOOGLE_API_KEY
        )
        
        # Initialize prompts
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup prompt templates for different tasks"""
        
        # Alumni recommendation prompt
        self.alumni_recommendation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
You are an AI assistant helping students find the best alumni for job referrals. 
Analyze the student profile and alumni search results to provide personalized recommendations.

Your task is to:
1. Identify the most relevant alumni based on skills, company, and career alignment
2. Explain why each alumni is a good match
3. Suggest the best approach for reaching out
4. Rank alumni by potential referral success

Be specific, actionable, and encouraging in your recommendations.
Focus on creating meaningful connections that benefit both the student and alumni.
            """),
            HumanMessage(content="""
Student Profile:
{student_profile}

Alumni Search Results:
{alumni_results}

Query Context: {query}

Please provide detailed recommendations for the top alumni matches, including:
- Why each alumni is relevant (specific skills, company, experience alignment)
- Suggested approach for outreach (common interests, shared experiences)
- Potential referral path and timeline
- Success probability assessment (1-10 scale with reasoning)
- Key talking points for initial contact

Format your response with clear sections for each recommended alumni.
            """)
        ])
        
        # Referral path analysis prompt
        self.referral_path_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
You are an expert at analyzing professional networks and referral paths.
Create a clear, actionable referral strategy based on alumni connections.

Focus on:
- Connection strength analysis
- Optimal outreach sequence
- Timing recommendations
- Success probability factors
- Relationship building strategies
            """),
            HumanMessage(content="""
Student Profile: {student_profile}
Target Alumni: {target_alumni}
Additional Context: {context}

Create a detailed referral path analysis with:
1. Connection strength assessment (consider shared experiences, department, graduation timeline)
2. Recommended outreach sequence (initial contact → relationship building → referral ask)
3. Key talking points and conversation starters
4. Timeline suggestions (when to send initial message, follow-ups, referral request)
5. Success probability score (1-10) with detailed reasoning
6. Risk mitigation strategies (how to handle potential challenges)
7. Alternative approaches if primary path doesn't work

Provide actionable, step-by-step guidance.
            """)
        ])
        
        # Email generation prompt
        self.email_generation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
You are an expert at writing professional, personalized outreach emails for job referrals.
Create emails that are:
- Professional yet warm and authentic
- Specific and personalized to both the student and alumni
- Clear about the ask without being pushy
- Respectful of the alumni's time
- Likely to get a positive response

Email best practices:
- Start with a genuine personal connection
- Be specific about why you're reaching out to them
- Clearly state your ask
- Make it easy for them to help
- Show gratitude and respect
- Include relevant student qualifications
- Provide clear next steps
            """),
            HumanMessage(content="""
Student Profile: {student_profile}
Alumni Profile: {alumni_profile}
Target Company: {target_company}
Target Role: {target_role}
Email Type: {email_type}
Additional Context: {context}

Generate a professional referral email that:
1. Has an engaging subject line
2. Opens with a genuine personal connection
3. Briefly introduces the student and their background
4. Clearly states the request
5. Highlights relevant qualifications and fit
6. Makes it easy for the alumni to help
7. Ends with appropriate gratitude and next steps

Provide the complete email with subject line.
Make it feel personal and authentic, not templated.
            """)
        ])
    
    def find_best_alumni_matches(
        self, 
        student: Student, 
        query: str = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Find the best alumni matches for a student"""
        
        # Build search query
        if not query:
            query = self._build_student_query(student)
        
        # Search vector store
        alumni_results = self.vector_store.search_alumni(
            query=query,
            student_profile=student,
            filters=filters,
            top_k=self.config.TOP_K_RESULTS * 2  # Get more results for better analysis
        )
        
        # Enhance results with similarity scores
        enhanced_results = self._enhance_alumni_results(student, alumni_results)
        
        # Get Gemini analysis
        analysis = self._get_llm_alumni_analysis(student, enhanced_results, query)
        
        return {
            'student_id': student.id,
            'query': query,
            'total_matches': len(enhanced_results),
            'alumni_matches': enhanced_results,
            'llm_analysis': analysis,
            'filters_applied': filters or {},
            'search_metadata': {
                'timestamp': str(datetime.now()),
                'model_used': self.config.GEMINI_MODEL
            }
        }
    
    def analyze_referral_path(
        self, 
        student: Student, 
        alumni: Dict[str, Any],
        context: str = ""
    ) -> Dict[str, Any]:
        """Analyze the referral path for a specific student-alumni pair"""
        
        # Get detailed analysis from Gemini
        analysis_result = self._get_referral_path_analysis(student, alumni, context)
        
        # Calculate additional metrics
        connection_strength = self._calculate_connection_strength(student, alumni)
        success_probability = self._estimate_success_probability(student, alumni)
        
        return {
            'student_id': student.id,
            'alumni_id': alumni.get('id'),
            'connection_strength': connection_strength,
            'success_probability': success_probability,
            'detailed_analysis': analysis_result,
            'recommended_timeline': self._suggest_timeline(alumni),
            'key_talking_points': self._extract_talking_points(student, alumni),
            'analysis_metadata': {
                'timestamp': str(datetime.now()),
                'model_used': self.config.GEMINI_MODEL
            }
        }
    
    def generate_referral_email(
        self,
        student: Student,
        alumni: Dict[str, Any],
        target_company: str,
        target_role: str,
        email_type: str = "initial_outreach",
        context: str = ""
    ) -> Dict[str, Any]:
        """Generate personalized referral email using Gemini"""
        
        # Generate email using Gemini
        email_content = self._generate_email_content(
            student, alumni, target_company, target_role, email_type, context
        )
        
        # Extract email components
        email_components = self._parse_email_content(email_content)
        
        return {
            'student_id': student.id,
            'alumni_id': alumni.get('id'),
            'target_company': target_company,
            'target_role': target_role,
            'email_type': email_type,
            'email_content': email_content,
            'email_components': email_components,
            'personalization_score': self._calculate_personalization_score(student, alumni),
            'send_recommendations': self._get_send_recommendations(alumni),
            'generation_metadata': {
                'timestamp': str(datetime.now()),
                'model_used': self.config.GEMINI_MODEL
            }
        }
    
    def _build_student_query(self, student: Student) -> str:
        """Build search query from student profile"""
        query_parts = []
        
        # Add skills (prioritize top skills)
        if student.skills:
            query_parts.extend(student.skills[:5])  # Top 5 skills
        
        # Add interests
        if student.interests:
            query_parts.extend(student.interests[:3])  # Top 3 interests
        
        # Add target companies
        if student.target_companies:
            query_parts.extend(student.target_companies[:3])
        
        # Add target roles
        if student.target_roles:
            query_parts.extend(student.target_roles[:2])
        
        # Add department context
        if student.department:
            query_parts.append(student.department)
        
        return " ".join(query_parts)
    
    def _enhance_alumni_results(
        self, 
        student: Student, 
        alumni_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhance alumni results with additional scoring"""
        
        enhanced_results = []
        
        for result in alumni_results:
            # Calculate custom similarity score
            custom_similarity = self.similarity_calculator.calculate_comprehensive_similarity(
                student, result['metadata']
            )
            
            # Add enhanced scoring
            result['enhanced_scores'] = {
                'vector_similarity': result['similarity_score'],
                'custom_similarity': custom_similarity,
                'company_match': self._calculate_company_match_score(student, result['metadata']),
                'skill_overlap': self._calculate_skill_overlap_score(student, result['metadata']),
                'seniority_fit': self._calculate_seniority_fit_score(result['metadata']),
                'response_likelihood': self._calculate_response_likelihood(result['metadata']),
                'department_alignment': self._calculate_department_alignment(student, result['metadata']),
                'graduation_proximity': self._calculate_graduation_proximity(student, result['metadata'])
            }
            
            # Calculate composite score
            result['composite_score'] = self._calculate_composite_score(result['enhanced_scores'])
            
            enhanced_results.append(result)
        
        # Sort by composite score
        enhanced_results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        return enhanced_results[:self.config.TOP_K_RESULTS]
    
    def _get_llm_alumni_analysis(
        self, 
        student: Student, 
        alumni_results: List[Dict[str, Any]], 
        query: str
    ) -> str:
        """Get Gemini analysis of alumni matches"""
        
        # Prepare input for LLM
        student_profile = student.get_full_profile()
        alumni_summary = self._format_alumni_results_for_llm(alumni_results)
        
        # Generate analysis
        chain = LLMChain(llm=self.llm, prompt=self.alumni_recommendation_prompt)
        
        try:
            result = chain.run(
                student_profile=student_profile,
                alumni_results=alumni_summary,
                query=query
            )
            return result
        except Exception as e:
            return f"Error generating analysis with Gemini: {str(e)}"
    
    def _get_referral_path_analysis(
        self, 
        student: Student, 
        alumni: Dict[str, Any], 
        context: str
    ) -> str:
        """Get detailed referral path analysis from Gemini"""
        
        student_profile = student.get_full_profile()
        alumni_profile = self._format_single_alumni_for_llm(alumni)
        
        chain = LLMChain(llm=self.llm, prompt=self.referral_path_prompt)
        
        try:
            result = chain.run(
                student_profile=student_profile,
                target_alumni=alumni_profile,
                context=context
            )
            return result
        except Exception as e:
            return f"Error generating referral path analysis with Gemini: {str(e)}"
    
    def _generate_email_content(
        self,
        student: Student,
        alumni: Dict[str, Any],
        target_company: str,
        target_role: str,
        email_type: str,
        context: str
    ) -> str:
        """Generate email content using Gemini"""
        
        student_profile = student.get_full_profile()
        alumni_profile = self._format_single_alumni_for_llm(alumni)
        
        chain = LLMChain(llm=self.llm, prompt=self.email_generation_prompt)
        
        try:
            result = chain.run(
                student_profile=student_profile,
                alumni_profile=alumni_profile,
                target_company=target_company,
                target_role=target_role,
                email_type=email_type,
                context=context
            )
            return result
        except Exception as e:
            return f"Error generating email with Gemini: {str(e)}"
    
    def _format_alumni_results_for_llm(self, alumni_results: List[Dict[str, Any]]) -> str:
        """Format alumni results for LLM input"""
        formatted_results = []
        
        for i, result in enumerate(alumni_results[:5]):  # Top 5 for LLM analysis
            metadata = result['metadata']
            scores = result.get('enhanced_scores', {})
            
            formatted_result = f"""
Alumni {i+1}:
- Name: {metadata.get('name', 'Unknown')}
- Company: {metadata.get('current_company', 'Unknown')}
- Position: {metadata.get('current_position', 'Unknown')}
- Department: {metadata.get('department', 'Unknown')}
- Graduation Year: {metadata.get('graduation_year', 'Unknown')}
- Skills: {', '.join(metadata.get('skills', []))}
- Industry: {metadata.get('industry', 'Unknown')}
- Seniority Level: {metadata.get('seniority_level', 'Unknown')}
- Composite Match Score: {result.get('composite_score', 0):.2f}
- Response Rate: {metadata.get('response_rate', 0):.2f}
- Hiring Authority: {metadata.get('hiring_authority', False)}
- Email: {metadata.get('email', 'Not available')}
- LinkedIn: {metadata.get('linkedin_url', 'Not available')}
            """
            formatted_results.append(formatted_result)
        
        return "\n".join(formatted_results)
    
    def _format_single_alumni_for_llm(self, alumni: Dict[str, Any]) -> str:
        """Format single alumni profile for LLM"""
        metadata = alumni['metadata'] if 'metadata' in alumni else alumni
        
        return f"""
Alumni Profile:
- Name: {metadata.get('name', 'Unknown')}
- Company: {metadata.get('current_company', 'Unknown')}
- Position: {metadata.get('current_position', 'Unknown')}
- Department: {metadata.get('department', 'Unknown')}
- Graduation Year: {metadata.get('graduation_year', 'Unknown')}
- Skills: {', '.join(metadata.get('skills', []))}
- Industry: {metadata.get('industry', 'Unknown')}
- Seniority Level: {metadata.get('seniority_level', 'Unknown')}
- Location: {metadata.get('location', 'Unknown')}
- Hiring Authority: {metadata.get('hiring_authority', False)}
- Response Rate: {metadata.get('response_rate', 0):.2f}
- Referral Success Rate: {metadata.get('referral_success_rate', 0):.2f}
- Email: {metadata.get('email', 'Not available')}
- LinkedIn: {metadata.get('linkedin_url', 'Not available')}
        """
    
    def _calculate_company_match_score(self, student: Student, alumni_metadata: Dict[str, Any]) -> float:
        """Calculate how well alumni's company matches student's targets"""
        alumni_company = alumni_metadata.get('current_company', '').lower()
        target_companies = [company.lower() for company in student.target_companies]
        
        if alumni_company in target_companies:
            return 1.0
        
        # Check for partial matches
        for target in target_companies:
            if target in alumni_company or alumni_company in target:
                return 0.7
        
        return 0.0
    
    def _calculate_skill_overlap_score(self, student: Student, alumni_metadata: Dict[str, Any]) -> float:
        """Calculate skill overlap between student and alumni"""
        student_skills = set(skill.lower() for skill in student.skills)
        alumni_skills = set(skill.lower() for skill in alumni_metadata.get('skills', []))
        
        if not student_skills or not alumni_skills:
            return 0.0
        
        overlap = len(student_skills.intersection(alumni_skills))
        total_unique = len(student_skills.union(alumni_skills))
        
        return overlap / total_unique if total_unique > 0 else 0.0
    
    def _calculate_seniority_fit_score(self, alumni_metadata: Dict[str, Any]) -> float:
        """Calculate seniority fit score (higher seniority = better for referrals)"""
        seniority = alumni_metadata.get('seniority_level', 'junior').lower()
        
        seniority_scores = {
            'junior': 0.3,
            'mid': 0.6,
            'senior': 0.9,
            'executive': 1.0,
            'director': 1.0,
            'manager': 0.8,
            'lead': 0.7,
            'principal': 0.9
        }
        
        return seniority_scores.get(seniority, 0.5)
    
    def _calculate_response_likelihood(self, alumni_metadata: Dict[str, Any]) -> float:
        """Calculate likelihood of response based on alumni profile"""
        base_score = alumni_metadata.get('response_rate', 0.5)
        
        # Boost score if they have hiring authority
        if alumni_metadata.get('hiring_authority', False):
            base_score += 0.2
        
        # Boost if high referral success rate
        referral_success = alumni_metadata.get('referral_success_rate', 0.0)
        base_score += referral_success * 0.1
        
        return min(base_score, 1.0)
    
    def _calculate_department_alignment(self, student: Student, alumni_metadata: Dict[str, Any]) -> float:
        """Calculate department alignment score"""
        student_dept = student.department.lower() if student.department else ""
        alumni_dept = alumni_metadata.get('department', '').lower()
        
        if student_dept == alumni_dept:
            return 1.0
        elif student_dept in alumni_dept or alumni_dept in student_dept:
            return 0.7
        else:
            return 0.0
    
    def _calculate_graduation_proximity(self, student: Student, alumni_metadata: Dict[str, Any]) -> float:
        """Calculate graduation year proximity score"""
        current_year = datetime.now().year
        student_grad_year = student.graduation_date.year if student.graduation_date else current_year
        alumni_grad_year = alumni_metadata.get('graduation_year', 2020)
        
        year_diff = abs(student_grad_year - alumni_grad_year)
        
        if year_diff <= 2:
            return 1.0
        elif year_diff <= 5:
            return 0.8
        elif year_diff <= 10:
            return 0.6
        else:
            return 0.3
    
    def _calculate_composite_score(self, enhanced_scores: Dict[str, float]) -> float:
        """Calculate composite score from all individual scores"""
        weights = {
            'vector_similarity': 0.20,
            'custom_similarity': 0.15,
            'company_match': 0.25,
            'skill_overlap': 0.15,
            'seniority_fit': 0.10,
            'response_likelihood': 0.10,
            'department_alignment': 0.03,
            'graduation_proximity': 0.02
        }
        
        composite = 0.0
        for score_type, weight in weights.items():
            composite += enhanced_scores.get(score_type, 0.0) * weight
        
        return composite
    
    def _calculate_connection_strength(self, student: Student, alumni: Dict[str, Any]) -> float:
        """Calculate connection strength between student and alumni"""
        metadata = alumni.get('metadata', alumni)
        
        strength_factors = []
        
        # Same department
        if student.department and student.department.lower() == metadata.get('department', '').lower():
            strength_factors.append(0.3)
        
        # Similar graduation years
        current_year = datetime.now().year
        student_grad_year = student.graduation_date.year if student.graduation_date else current_year
        alumni_grad_year = metadata.get('graduation_year', 2020)
        grad_year_diff = abs(student_grad_year - alumni_grad_year)
        
        if grad_year_diff <= 5:
            strength_factors.append(0.2)
        elif grad_year_diff <= 10:
            strength_factors.append(0.1)
        
        # Skill overlap
        student_skills = set(skill.lower() for skill in student.skills)
        alumni_skills = set(skill.lower() for skill in metadata.get('skills', []))
        skill_overlap = len(student_skills.intersection(alumni_skills))
        if skill_overlap > 0:
            strength_factors.append(min(skill_overlap * 0.1, 0.3))
        
        # Target company match
        if metadata.get('current_company', '').lower() in [tc.lower() for tc in student.target_companies]:
            strength_factors.append(0.4)
        
        return sum(strength_factors)
    
    def _estimate_success_probability(self, student: Student, alumni: Dict[str, Any]) -> float:
        """Estimate success probability for referral"""
        metadata = alumni.get('metadata', alumni)
        
        factors = []
        
        # Base response rate
        factors.append(metadata.get('response_rate', 0.5) * 0.3)
        
        # Referral success rate
        factors.append(metadata.get('referral_success_rate', 0.3) * 0.2)
        
        # Hiring authority
        if metadata.get('hiring_authority', False):
            factors.append(0.2)
        
        # Company match
        if metadata.get('current_company', '').lower() in [tc.lower() for tc in student.target_companies]:
            factors.append(0.2)
        
        # Seniority level
        seniority = metadata.get('seniority_level', 'junior').lower()
        if seniority in ['senior', 'executive', 'director', 'manager']:
            factors.append(0.1)
        
        return min(sum(factors), 1.0)
    
    def _suggest_timeline(self, alumni: Dict[str, Any]) -> Dict[str, str]:
        """Suggest timeline for outreach"""
        metadata = alumni.get('metadata', alumni)
        
        # Base timeline
        timeline = {
            'initial_contact': 'Send within 1-2 days',
            'follow_up_1': 'Follow up after 1 week if no response',
            'relationship_building': '2-3 weeks of light engagement',
            'referral_request': '3-4 weeks after initial contact'
        }
        
        # Adjust based on response rate
        response_rate = metadata.get('response_rate', 0.5)
        if response_rate > 0.7:
            timeline['referral_request'] = '2-3 weeks after initial contact'
        elif response_rate < 0.3:
            timeline['relationship_building'] = '4-6 weeks of consistent engagement'
            timeline['referral_request'] = '6-8 weeks after initial contact'
        
        return timeline
    
    def _extract_talking_points(self, student: Student, alumni: Dict[str, Any]) -> List[str]:
        """Extract key talking points for outreach"""
        metadata = alumni.get('metadata', alumni)
        talking_points = []
        
        # Shared department
        if student.department and student.department.lower() == metadata.get('department', '').lower():
            talking_points.append(f"Fellow {student.department} graduate")
        
        # Skill overlap
        student_skills = set(skill.lower() for skill in student.skills)
        alumni_skills = set(skill.lower() for skill in metadata.get('skills', []))
        common_skills = student_skills.intersection(alumni_skills)
        if common_skills:
            talking_points.append(f"Shared expertise in {', '.join(list(common_skills)[:3])}")
        
        # Target company
        if metadata.get('current_company', '').lower() in [tc.lower() for tc in student.target_companies]:
            talking_points.append(f"Interest in working at {metadata.get('current_company')}")
        
        # Career trajectory
        if metadata.get('seniority_level') in ['senior', 'executive', 'director']:
            talking_points.append("Learning about career growth in the industry")
        
        return talking_points
    
    def _parse_email_content(self, email_content: str) -> Dict[str, str]:
        """Parse email content into components"""
        lines = email_content.strip().split('\n')
        
        components = {
            'subject': '',
            'greeting': '',
            'introduction': '',
            'body': '',
            'ask': '',
            'closing': '',
            'signature': ''
        }
        
        try:
            # Simple parsing - in production, you'd want more sophisticated parsing
            current_section = 'body'
            for line in lines:
                line = line.strip()
                if line.startswith('Subject:'):
                    components['subject'] = line.replace('Subject:', '').strip()
                elif line.startswith('Dear') or line.startswith('Hi') or line.startswith('Hello'):
                    components['greeting'] = line
                elif 'Best regards' in line or 'Sincerely' in line or 'Thank you' in line:
                    current_section = 'closing'
                    components[current_section] += line + '\n'
                else:
                    components[current_section] += line + '\n'
        except Exception as e:
            # Fallback: put everything in body
            components['body'] = email_content
        
        return components
    
    def _calculate_personalization_score(self, student: Student, alumni: Dict[str, Any]) -> float:
        """Calculate how personalized the email can be"""
        metadata = alumni.get('metadata', alumni)
        score = 0.0
        
        # Available contact information
        if metadata.get('email'):
            score += 0.2
        if metadata.get('linkedin_url'):
            score += 0.2
        
        # Shared experiences
        if student.department == metadata.get('department'):
            score += 0.2
        
        # Skill overlap
        student_skills = set(skill.lower() for skill in student.skills)
        alumni_skills = set(skill.lower() for skill in metadata.get('skills', []))
        if student_skills.intersection(alumni_skills):
            score += 0.2
        
        # Company interest
        if metadata.get('current_company', '').lower() in [tc.lower() for tc in student.target_companies]:
            score += 0.2
        
        return min(score, 1.0)
    
    def _get_send_recommendations(self, alumni: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations for when and how to send the email"""
        metadata = alumni.get('metadata', alumni)
        
        recommendations = {
            'best_time': 'Tuesday-Thursday, 9 AM - 11 AM',
            'platform': 'Email' if metadata.get('email') else 'LinkedIn',
            'follow_up_strategy': 'Wait 1 week, then send polite follow-up',
            'tips': []
        }
        
        # Platform-specific tips
        if metadata.get('email'):
            recommendations['tips'].append('Use professional email with clear subject line')
        else:
            recommendations['tips'].append('Send LinkedIn connection request with personalized message')
        
        # Response rate based tips
        response_rate = metadata.get('response_rate', 0.5)
        if response_rate > 0.7:
            recommendations['tips'].append('High response rate - likely to get quick reply')
        elif response_rate < 0.3:
            recommendations['tips'].append('Lower response rate - consider multiple touchpoints')
        
        return recommendations
    
    def generate_multiple_email_variations(
        self,
        student: Student,
        alumni: Dict[str, Any],
        target_company: str,
        target_role: str,
        num_variations: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate multiple email variations for A/B testing"""
        
        variations = []
        email_types = ['formal', 'casual', 'story_driven']
        
        for i in range(min(num_variations, len(email_types))):
            email_type = email_types[i]
            context = f"Style: {email_type}. Make this variation distinct from others."
            
            variation = self.generate_referral_email(
                student=student,
                alumni=alumni,
                target_company=target_company,
                target_role=target_role,
                email_type=email_type,
                context=context
            )
            
            variation['variation_type'] = email_type
            variation['variation_number'] = i + 1
            variations.append(variation)
        
        return variations
    
    def analyze_alumni_network(self, student: Student) -> Dict[str, Any]:
        """Analyze the entire alumni network for a student"""
        
        # Get all relevant alumni
        all_matches = self.find_best_alumni_matches(student)
        
        # Analyze network structure
        network_analysis = {
            'total_potential_referrers': len(all_matches['alumni_matches']),
            'company_coverage': {},
            'skill_coverage': {},
            'seniority_distribution': {},
            'response_rate_analysis': {},
            'recommendations': []
        }
        
        # Company coverage
        for match in all_matches['alumni_matches']:
            company = match['metadata']['current_company']
            if company not in network_analysis['company_coverage']:
                network_analysis['company_coverage'][company] = 0
            network_analysis['company_coverage'][company] += 1
        
        # Add strategic recommendations
        if len(network_analysis['company_coverage']) > 5:
            network_analysis['recommendations'].append("Strong company coverage - good referral network")
        else:
            network_analysis['recommendations'].append("Limited company coverage - consider expanding network")
        
        return network_analysis