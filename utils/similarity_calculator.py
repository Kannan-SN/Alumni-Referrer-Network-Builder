from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SimilarityCalculator:
    """Calculate various similarity scores between students and alumni"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            max_features=1000
        )
    
    def calculate_comprehensive_similarity(
        self, 
        student, 
        alumni_metadata: Dict[str, Any]
    ) -> float:
        """Calculate comprehensive similarity score"""
        
        scores = []
        weights = []
        
        # Skill similarity
        skill_sim = self.calculate_skill_similarity(student, alumni_metadata)
        scores.append(skill_sim)
        weights.append(0.3)
        
        # Interest similarity
        interest_sim = self.calculate_interest_similarity(student, alumni_metadata)
        scores.append(interest_sim)
        weights.append(0.2)
        
        # Company similarity
        company_sim = self.calculate_company_similarity(student, alumni_metadata)
        scores.append(company_sim)
        weights.append(0.25)
        
        # Department similarity
        dept_sim = self.calculate_department_similarity(student, alumni_metadata)
        scores.append(dept_sim)
        weights.append(0.15)
        
        # Career level similarity
        career_sim = self.calculate_career_level_similarity(student, alumni_metadata)
        scores.append(career_sim)
        weights.append(0.1)
        
        # Calculate weighted average
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        
        return weighted_score
    
    def calculate_skill_similarity(
        self, 
        student, 
        alumni_metadata: Dict[str, Any]
    ) -> float:
        """Calculate skill overlap similarity"""
        
        student_skills = set(skill.lower().strip() for skill in student.skills)
        alumni_skills = set(skill.lower().strip() for skill in alumni_metadata.get('skills', []))
        
        if not student_skills or not alumni_skills:
            return 0.0
        
        # Jaccard similarity
        intersection = len(student_skills.intersection(alumni_skills))
        union = len(student_skills.union(alumni_skills))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_interest_similarity(
        self, 
        student, 
        alumni_metadata: Dict[str, Any]
    ) -> float:
        """Calculate interest alignment with alumni's work domain"""
        
        student_interests = set(interest.lower().strip() for interest in student.interests)
        
        # Check against alumni's skills, industry, and position
        alumni_domain_keywords = set()
        
        # Add alumni skills
        alumni_skills = alumni_metadata.get('skills', [])
        alumni_domain_keywords.update(skill.lower().strip() for skill in alumni_skills)
        
        # Add industry keywords
        industry = alumni_metadata.get('industry', '')
        if industry:
            alumni_domain_keywords.add(industry.lower().strip())
        
        # Add position keywords
        position = alumni_metadata.get('current_position', '')
        if position:
            position_words = position.lower().split()
            alumni_domain_keywords.update(word.strip() for word in position_words)
        
        if not student_interests or not alumni_domain_keywords:
            return 0.0
        
        # Calculate overlap
        intersection = len(student_interests.intersection(alumni_domain_keywords))
        return intersection / len(student_interests) if student_interests else 0.0
    
    def calculate_company_similarity(
        self, 
        student, 
        alumni_metadata: Dict[str, Any]
    ) -> float:
        """Calculate company interest similarity"""
        
        alumni_company = alumni_metadata.get('current_company', '').lower().strip()
        target_companies = [company.lower().strip() for company in student.target_companies]
        
        if not alumni_company or not target_companies:
            return 0.0
        
        # Exact match
        if alumni_company in target_companies:
            return 1.0
        
        # Partial match
        for target in target_companies:
            if target in alumni_company or alumni_company in target:
                return 0.7
        
        # Industry similarity (simplified)
        alumni_industry = alumni_metadata.get('industry', '').lower()
        student_industries = [industry.lower() for industry in student.preferred_industries]
        
        if alumni_industry and alumni_industry in student_industries:
            return 0.5
        
        return 0.0
    
    def calculate_department_similarity(
        self, 
        student, 
        alumni_metadata: Dict[str, Any]
    ) -> float:
        """Calculate department similarity"""
        
        student_dept = student.department.lower().strip() if student.department else ""
        alumni_dept = alumni_metadata.get('department', '').lower().strip()
        
        if not student_dept or not alumni_dept:
            return 0.0
        
        if student_dept == alumni_dept:
            return 1.0
        
        # Check for related departments
        related_depts = {
            'computer science': ['software engineering', 'information technology', 'data science'],
            'electrical engineering': ['electronics', 'embedded systems'],
            'mechanical engineering': ['automotive', 'aerospace'],
            'business': ['management', 'finance', 'marketing'],
            'data science': ['computer science', 'statistics', 'analytics']
        }
        
        for main_dept, related in related_depts.items():
            if student_dept == main_dept and alumni_dept in related:
                return 0.7
            if alumni_dept == main_dept and student_dept in related:
                return 0.7
        
        return 0.0
    
    def calculate_career_level_similarity(
        self, 
        student, 
        alumni_metadata: Dict[str, Any]
    ) -> float:
        """Calculate career level compatibility for referrals"""
        
        # Students typically want referrals from mid to senior level professionals
        alumni_seniority = alumni_metadata.get('seniority_level', 'junior').lower()
        
        seniority_scores = {
            'junior': 0.3,      # Recent graduates, limited referral power
            'mid': 0.8,         # Good for peer referrals
            'senior': 1.0,      # Excellent for referrals
            'executive': 0.9,   # Great but might be harder to reach
            'director': 1.0,    # Excellent referral potential
            'manager': 0.9,     # Good referral potential
            'lead': 0.8,        # Good for technical referrals
            'principal': 0.9    # Senior technical roles
        }
        
        return seniority_scores.get(alumni_seniority, 0.5)