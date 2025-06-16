from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Alumni:
    """Alumni data model"""
    id: str
    name: str
    graduation_year: int
    degree: str
    department: str
    current_company: str
    current_position: str
    current_team: Optional[str] = None
    location: str = ""
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    skills: List[str] = None
    previous_companies: List[Dict[str, Any]] = None
    bio: Optional[str] = None
    contact_preference: str = "linkedin"  # linkedin, email, phone
    response_rate: float = 0.0  # Historical response rate for referrals
    referral_success_rate: float = 0.0
    industry: Optional[str] = None
    seniority_level: str = "mid"  # junior, mid, senior, executive
    hiring_authority: bool = False
    mentorship_available: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.previous_companies is None:
            self.previous_companies = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def get_full_profile(self) -> str:
        """Get formatted full profile for RAG"""
        profile = f"""
        Alumni Profile:
        Name: {self.name}
        Graduation Year: {self.graduation_year}
        Degree: {self.degree}
        Department: {self.department}
        Current Company: {self.current_company}
        Current Position: {self.current_position}
        Team: {self.current_team or 'Not specified'}
        Location: {self.location}
        Skills: {', '.join(self.skills)}
        Industry: {self.industry or 'Not specified'}
        Seniority Level: {self.seniority_level}
        Hiring Authority: {'Yes' if self.hiring_authority else 'No'}
        Mentorship Available: {'Yes' if self.mentorship_available else 'No'}
        Bio: {self.bio or 'No bio available'}
        """
        
        if self.previous_companies:
            profile += "\nPrevious Companies:\n"
            for company in self.previous_companies:
                profile += f"- {company.get('name', 'Unknown')} as {company.get('position', 'Unknown position')}\n"
        
        return profile.strip()
    
    def calculate_similarity_score(self, student_interests: List[str], student_skills: List[str]) -> float:
        """Calculate similarity score with student profile"""
        # Simple similarity calculation based on skills overlap
        alumni_skills_lower = [skill.lower() for skill in self.skills]
        student_skills_lower = [skill.lower() for skill in student_skills]
        student_interests_lower = [interest.lower() for interest in student_interests]
        
        skill_overlap = len(set(alumni_skills_lower) & set(student_skills_lower))
        interest_overlap = len(set(alumni_skills_lower) & set(student_interests_lower))
        
        total_possible = len(set(student_skills_lower + student_interests_lower))
        if total_possible == 0:
            return 0.0
        
        return (skill_overlap + interest_overlap) / total_possible
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'graduation_year': self.graduation_year,
            'degree': self.degree,
            'department': self.department,
            'current_company': self.current_company,
            'current_position': self.current_position,
            'current_team': self.current_team,
            'location': self.location,
            'email': self.email,
            'linkedin_url': self.linkedin_url,
            'skills': self.skills,
            'previous_companies': self.previous_companies,
            'bio': self.bio,
            'contact_preference': self.contact_preference,
            'response_rate': self.response_rate,
            'referral_success_rate': self.referral_success_rate,
            'industry': self.industry,
            'seniority_level': self.seniority_level,
            'hiring_authority': self.hiring_authority,
            'mentorship_available': self.mentorship_available,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alumni':
        """Create Alumni instance from dictionary"""
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)