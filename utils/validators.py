import re
from typing import Dict, Any, List, Tuple

class InputValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  # Added missing closing quote and $
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