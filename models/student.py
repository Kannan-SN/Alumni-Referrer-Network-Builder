from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Student:
    """Student data model"""
    id: str
    name: str
    current_year: int
    degree: str
    department: str
    cgpa: float
    email: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    skills: List[str] = None
    interests: List[str] = None
    target_companies: List[str] = None
    target_roles: List[str] = None
    preferred_locations: List[str] = None
    projects: List[Dict[str, Any]] = None
    internships: List[Dict[str, Any]] = None
    achievements: List[str] = None
    resume_url: Optional[str] = None
    bio: Optional[str] = None
    graduation_date: Optional[datetime] = None
    job_search_status: str = "active"  # active, passive, not_looking
    preferred_industries: List[str] = None
    salary_expectation: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.interests is None:
            self.interests = []
        if self.target_companies is None:
            self.target_companies = []
        if self.target_roles is None:
            self.target_roles = []
        if self.preferred_locations is None:
            self.preferred_locations = []
        if self.projects is None:
            self.projects = []
        if self.internships is None:
            self.internships = []
        if self.achievements is None:
            self.achievements = []
        if self.preferred_industries is None:
            self.preferred_industries = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def get_full_profile(self) -> str:
        """Get formatted full profile for RAG"""
        profile = f"""
        Student Profile:
        Name: {self.name}
        Current Year: {self.current_year}
        Degree: {self.degree}
        Department: {self.department}
        CGPA: {self.cgpa}
        Skills: {', '.join(self.skills)}
        Interests: {', '.join(self.interests)}
        Target Companies: {', '.join(self.target_companies)}
        Target Roles: {', '.join(self.target_roles)}
        Preferred Locations: {', '.join(self.preferred_locations)}
        Preferred Industries: {', '.join(self.preferred_industries)}
        Job Search Status: {self.job_search_status}
        Bio: {self.bio or 'No bio available'}
        """
        
        if self.projects:
            profile += "\nProjects:\n"
            for project in self.projects:
                profile += f"- {project.get('title', 'Untitled')}: {project.get('description', 'No description')}\n"
        
        if self.internships:
            profile += "\nInternships:\n"
            for internship in self.internships:
                profile += f"- {internship.get('company', 'Unknown')} as {internship.get('role', 'Unknown role')}\n"
        
        if self.achievements:
            profile += f"\nAchievements: {', '.join(self.achievements)}\n"
        
        return profile.strip()
    
    def get_search_keywords(self) -> List[str]:
        """Get keywords for alumni search"""
        keywords = []
        keywords.extend(self.skills)
        keywords.extend(self.interests)
        keywords.extend(self.target_companies)
        keywords.extend(self.target_roles)
        keywords.extend(self.preferred_industries)
        
        # Add derived keywords
        if self.department:
            keywords.append(self.department)
        if self.degree:
            keywords.append(self.degree)
        
        return list(set(keywords))  # Remove duplicates
    
    def calculate_company_preference_score(self, company: str) -> float:
        """Calculate preference score for a company"""
        if company.lower() in [tc.lower() for tc in self.target_companies]:
            return 1.0
        
        # Check if company is in preferred industries
        # This would require additional company-industry mapping
        return 0.5  # Default moderate interest
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'current_year': self.current_year,
            'degree': self.degree,
            'department': self.department,
            'cgpa': self.cgpa,
            'email': self.email,
            'phone': self.phone,
            'linkedin_url': self.linkedin_url,
            'github_url': self.github_url,
            'skills': self.skills,
            'interests': self.interests,
            'target_companies': self.target_companies,
            'target_roles': self.target_roles,
            'preferred_locations': self.preferred_locations,
            'projects': self.projects,
            'internships': self.internships,
            'achievements': self.achievements,
            'resume_url': self.resume_url,
            'bio': self.bio,
            'graduation_date': self.graduation_date.isoformat() if self.graduation_date else None,
            'job_search_status': self.job_search_status,
            'preferred_industries': self.preferred_industries,
            'salary_expectation': self.salary_expectation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Student':
        """Create Student instance from dictionary"""
        if 'graduation_date' in data and data['graduation_date']:
            data['graduation_date'] = datetime.fromisoformat(data['graduation_date'])
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)