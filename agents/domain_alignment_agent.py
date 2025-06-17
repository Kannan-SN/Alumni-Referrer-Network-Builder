from typing import Dict, Any, List
from agents.base_agent import BaseAgent
import logging

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
            logging.error(f"Domain alignment failed: {e}")
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
            
            if alignment_score > 0.1:  # Lower threshold for demo
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
        score = 0.2  # Base score
        
        # Interest alignment
        if interests and alumni.get('domain'):
            for interest in interests:
                if interest.lower() in alumni['domain'].lower():
                    score += 0.3
                    break
        
        # Skills alignment
        if skills and alumni.get('skills'):
            common_skills = set(skill.lower() for skill in skills) & \
                          set(skill.lower() for skill in alumni['skills'])
            if common_skills:
                score += len(common_skills) * 0.1
        
        # Company alignment
        if target_companies and alumni.get('current_company'):
            for company in target_companies:
                if company.lower() in alumni['current_company'].lower():
                    score += 0.4
                    break
        
        # Role alignment
        if target_roles and alumni.get('current_role'):
            for role in target_roles:
                if role.lower() in alumni['current_role'].lower():
                    score += 0.3
                    break
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_alignment_reasons(self, interests: List[str], skills: List[str],
                             target_companies: List[str], target_roles: List[str],
                             alumni: Dict[str, Any]) -> List[str]:
        """Get reasons for alignment"""
        reasons = []
        
        # Interest alignment
        if interests and alumni.get('domain'):
            for interest in interests:
                if interest.lower() in alumni['domain'].lower():
                    reasons.append(f"Shared interest in {interest}")
        
        # Skills alignment
        if skills and alumni.get('skills'):
            common_skills = set(skill.lower() for skill in skills) & \
                          set(skill.lower() for skill in alumni['skills'])
            if common_skills:
                reasons.append(f"Common skills: {', '.join(list(common_skills)[:3])}")
        
        # Company alignment
        if target_companies and alumni.get('current_company'):
            for company in target_companies:
                if company.lower() in alumni['current_company'].lower():
                    reasons.append(f"Target company match: {alumni['current_company']}")
        
        # Role alignment
        if target_roles and alumni.get('current_role'):
            for role in target_roles:
                if role.lower() in alumni['current_role'].lower():
                    reasons.append(f"Similar role interest: {alumni['current_role']}")
        
        return reasons
    
    def _get_alignment_factors(self) -> Dict[str, str]:
        """Get explanation of alignment factors"""
        return {
            "interests": "Domain and career interest alignment",
            "skills": "Technical and soft skills overlap", 
            "companies": "Target company preferences",
            "roles": "Desired job role similarities"
        }