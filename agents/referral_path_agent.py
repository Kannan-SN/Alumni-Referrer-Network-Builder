from typing import Dict, Any, List, Tuple
from agents.base_agent import BaseAgent
import networkx as nx

class ReferralPathAgent(BaseAgent):
    def __init__(self):
        super().__init__("Referral Path Recommender Agent")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construct optimal outreach paths for student-alumni matches
        """
        try:
            student_profile = input_data.get('student_profile', {})
            alumni_matches = input_data.get('alumni_matches', [])
            
            referral_paths = await self._construct_referral_paths(
                student_profile, alumni_matches
            )
            
            return {
                "status": "success",
                "total_paths": len(referral_paths),
                "referral_paths": referral_paths,
                "path_recommendations": await self._rank_paths(referral_paths)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _construct_referral_paths(self, student_profile: Dict[str, Any],
                                      alumni_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Construct optimal referral paths"""
        paths = []
        
        for alumni in alumni_matches:
            path = await self._create_single_path(student_profile, alumni)
            if path:
                paths.append(path)
        
        return paths
    
    async def _create_single_path(self, student_profile: Dict[str, Any],
                                alumni: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single referral path"""
        try:
            path = {
                "alumni_id": str(alumni.get('_id', '')),
                "alumni_name": alumni.get('name', ''),
                "path_description": self._generate_path_description(student_profile, alumni),
                "connection_strength": await self._calculate_connection_strength(student_profile, alumni),
                "recommended_approach": await self._get_recommended_approach(student_profile, alumni),
                "success_probability": await self._estimate_success_probability(student_profile, alumni),
                "timeline": self._estimate_timeline(alumni),
                "preparation_steps": await self._get_preparation_steps(student_profile, alumni)
            }
            return path
        except Exception as e:
            return None
    
    def _generate_path_description(self, student_profile: Dict[str, Any],
                                 alumni: Dict[str, Any]) -> str:
        """Generate human-readable path description"""
        alumni_name = alumni.get('name', 'Alumni')
        graduation_year = alumni.get('graduation_year', 'Unknown')
        company = alumni.get('current_company', 'Unknown Company')
        role = alumni.get('current_role', 'Unknown Role')
        domain = alumni.get('domain', 'Unknown Domain')
        
        return f"{alumni_name} - {graduation_year} Graduate - {company} - {role} - {domain}"
    
    async def _calculate_connection_strength(self, student_profile: Dict[str, Any],
                                           alumni: Dict[str, Any]) -> str:
        """Calculate the strength of potential connection"""
        score = 0
        
        # Same degree program
        if student_profile.get('degree', '').lower() == alumni.get('degree', '').lower():
            score += 3
        
        # Similar interests/domain
        student_interests = [i.lower() for i in student_profile.get('interests', [])]
        alumni_domain = alumni.get('domain', '').lower()
        if any(interest in alumni_domain for interest in student_interests):
            score += 2
        
        # Common skills
        student_skills = set(s.lower() for s in student_profile.get('skills', []))
        alumni_skills = set(s.lower() for s in alumni.get('skills', []))
        common_skills = student_skills & alumni_skills
        score += len(common_skills)
        
        # Graduation year proximity
        current_year = student_profile.get('current_year', 1)
        expected_grad_year = 2024 + (4 - current_year)  # Assuming 4-year program
        year_diff = abs(alumni.get('graduation_year', 2020) - expected_grad_year)
        if year_diff <= 3:
            score += 2
        elif year_diff <= 6:
            score += 1
        
        if score >= 6:
            return "Strong"
        elif score >= 3:
            return "Moderate"
        else:
            return "Weak"
    
    async def _get_recommended_approach(self, student_profile: Dict[str, Any],
                                      alumni: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommended approach for outreach"""
        approaches = {
            "primary": "LinkedIn Message",
            "secondary": "Email",
            "timing": "Weekday mornings (9-11 AM)",
            "follow_up": "After 1 week if no response",
            "tone": "Professional but friendly"
        }
        
        # Customize based on alumni seniority
        experience = alumni.get('experience_years', 0)
        if experience >= 10:
            approaches["tone"] = "Respectful and formal"
            approaches["timing"] = "Tuesday-Thursday mornings"
        elif experience <= 3:
            approaches["tone"] = "Casual and enthusiastic"
        
        return approaches
    
    async def _estimate_success_probability(self, student_profile: Dict[str, Any],
                                          alumni: Dict[str, Any]) -> str:
        """Estimate probability of successful referral"""
        connection_strength = await self._calculate_connection_strength(student_profile, alumni)
        alignment_score = alumni.get('alignment_score', 0)
        
        if connection_strength == "Strong" and alignment_score > 0.7:
            return "High (70-85%)"
        elif connection_strength == "Moderate" and alignment_score > 0.5:
            return "Medium (50-70%)"
        else:
            return "Low (30-50%)"
    
    def _estimate_timeline(self, alumni: Dict[str, Any]) -> Dict[str, str]:
        """Estimate timeline for referral process"""
        return {
            "initial_response": "2-5 business days",
            "referral_submission": "1-2 weeks after connection",
            "interview_process": "2-4 weeks",
            "total_timeline": "4-7 weeks"
        }
    
    async def _get_preparation_steps(self, student_profile: Dict[str, Any],
                                   alumni: Dict[str, Any]) -> List[str]:
        """Get preparation steps for the student"""
        steps = [
            "Research the alumni's current company and recent news",
            "Review the job requirements for target roles",
            "Prepare a concise elevator pitch about yourself",
            "Update your resume and LinkedIn profile",
            "Prepare specific questions about the company culture"
        ]
        
        # Add specific steps based on alumni domain
        domain = alumni.get('domain', '').lower()
        if 'engineering' in domain or 'technical' in domain:
            steps.append("Prepare to discuss your technical projects and skills")
            steps.append("Review the company's tech stack and recent developments")
        elif 'business' in domain or 'management' in domain:
            steps.append("Prepare business-focused questions and examples")
            steps.append("Research the company's market position and strategy")
        
        return steps
    
    async def _rank_paths(self, paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank paths by overall recommendation score"""
        for path in paths:
            score = 0
            
            # Connection strength weight
            if path['connection_strength'] == 'Strong':
                score += 3
            elif path['connection_strength'] == 'Moderate':
                score += 2
            else:
                score += 1
            
            # Success probability weight
            if 'High' in path['success_probability']:
                score += 3
            elif 'Medium' in path['success_probability']:
                score += 2
            else:
                score += 1
            
            path['recommendation_score'] = score
        
        return sorted(paths, key=lambda x: x['recommendation_score'], reverse=True)