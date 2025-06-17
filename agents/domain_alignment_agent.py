from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class DomainAlignmentAgent(BaseAgent):
    def __init__(self):
        super().__init__("Domain Alignment Agent")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match student interests and skills with alumni domains
        """
        try:
            student_profile = input_data.get('student_profile', {})
            alumni_list = input_data.get('alumni_list', [])
            
            aligned_matches = await self._calculate_domain_alignment(
                student_profile, alumni_list
            )
            
            return {
                "status": "success",
                "total_matches": len(aligned_matches),
                "aligned_alumni": aligned_matches,
                "alignment_factors": self._get_alignment_factors()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _calculate_domain_alignment(self, student_profile: Dict[str, Any], 
                                        alumni_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate alignment between student and alumni"""
        student_interests = student_profile.get('interests', [])
        student_skills = student_profile.get('skills', [])
        target_companies = student_profile.get('target_companies', [])
        target_roles = student_profile.get('target_roles', [])
        
        aligned_alumni = []
        
        for alumni in alumni_list:
            alignment_score = await self._compute_alignment_score(
                student_interests, student_skills, target_companies, target_roles, alumni
            )
            
            if alignment_score > 0.3:  # Threshold for meaningful alignment
                alumni['alignment_score'] = alignment_score
                alumni['alignment_reasons'] = self._get_alignment_reasons(
                    student_interests, student_skills, target_companies, target_roles, alumni
                )
                aligned_alumni.append(alumni)
        
        return sorted(aligned_alumni, key=lambda x: x['alignment_score'], reverse=True)
    
    async def _compute_alignment_score(self, interests: List[str], skills: List[str],
                                     target_companies: List[str], target_roles: List[str],
                                     alumni: Dict[str, Any]) -> float:
        """Compute alignment score between student and alumni"""
        score = 0.0
        total_weight = 0.0
        
        # Interest alignment (weight: 0.3)
        if interests and alumni.get('domain'):
            interest_match = any(interest.lower() in alumni['domain'].lower() 
                               for interest in interests)
            if interest_match:
                score += 0.3
            total_weight += 0.3
        
        # Skills alignment (weight: 0.4)
        if skills and alumni.get('skills'):
            common_skills = set(skill.lower() for skill in skills) & \
                          set(skill.lower() for skill in alumni['skills'])
            skill_ratio = len(common_skills) / len(skills) if skills else 0
            score += skill_ratio * 0.4
            total_weight += 0.4
        
        # Company alignment (weight: 0.2)
        if target_companies and alumni.get('current_company'):
            company_match = any(company.lower() in alumni['current_company'].lower()
                              for company in target_companies)
            if company_match:
                score += 0.2
            total_weight += 0.2
        
        # Role alignment (weight: 0.1)
        if target_roles and alumni.get('current_role'):
            role_match = any(role.lower() in alumni['current_role'].lower()
                           for role in target_roles)
            if role_match:
                score += 0.1
            total_weight += 0.1
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _get_alignment_reasons(self, interests: List[str], skills: List[str],
                             target_companies: List[str], target_roles: List[str],
                             alumni: Dict[str, Any]) -> List[str]:
        """Get reasons for alignment"""
        reasons = []
        
        # Check interest alignment
        if interests and alumni.get('domain'):
            matching_interests = [interest for interest in interests 
                                if interest.lower() in alumni['domain'].lower()]
            if matching_interests:
                reasons.append(f"Shared interests in {', '.join(matching_interests)}")
        
        # Check skill alignment
        if skills and alumni.get('skills'):
            common_skills = set(skill.lower() for skill in skills) & \
                          set(skill.lower() for skill in alumni['skills'])
            if common_skills:
                reasons.append(f"Common skills: {', '.join(common_skills)}")
        
        # Check company alignment
        if target_companies and alumni.get('current_company'):
            matching_companies = [company for company in target_companies
                                if company.lower() in alumni['current_company'].lower()]
            if matching_companies:
                reasons.append(f"Target company match: {alumni['current_company']}")
        
        return reasons
    
    def _get_alignment_factors(self) -> Dict[str, str]:
        """Get explanation of alignment factors"""
        return {
            "interests": "Domain and career interest alignment",
            "skills": "Technical and soft skills overlap",
            "companies": "Target company preferences",
            "roles": "Desired job role similarities"
        }