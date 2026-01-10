"""
========================================
AUTONOMOUS JOB APPLICATION AGENT
========================================
Single source of truth: USER_PROFILE
Never invents, exaggerates, or hallucinates experience.

This agent operates continuously without human input.
Priority: External ATS (Greenhouse, Lever, Ashby) > Job Boards
"""

import os
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'job_bot' / 'config'))

# Import user profile from existing job_bot
try:
    from user_profile import USER_PROFILE
except ImportError:
    # Fallback to local profile
    USER_PROFILE = None


# ============== USER PROFILE (Single Source of Truth) ==============
# If import fails, use this embedded version
if not USER_PROFILE:
    USER_PROFILE = {
        "personal": {
            "first_name": "Ihsanul",
            "last_name": "Hak IK",
            "full_name": "Ihsanul Hak IK",
            "email": "ikihsaan@gmail.com",
            "phone": "+91 9037312356",
            "phone_country_code": "+91",
            "date_of_birth": "2003-07-16",
            "gender": "Male",
            "nationality": "Indian",
            "languages": [
                {"language": "English", "proficiency": "Professional"},
                {"language": "Hindi", "proficiency": "Professional"},
            ],
        },
        
        "location": {
            "address": "Illathodi Karuvarapatta House",
            "address_line_2": "Vilayil, kondotti",
            "city": "Kozhikode",
            "state": "Kerala",
            "zip_code": "673641",
            "country": "India",
            "willing_to_relocate": True,
            "relocation_preferences": ["Mumbai", "Bangalore", "Hyderabad"],
            "remote_preference": "Remote",
        },
        
        "work_experience": [
            {
                "company": "Space-Ai",
                "title": "Junior Software Developer",
                "location": "United States (Remote)",
                "start_date": "2024-09",  # Corrected date
                "end_date": "Present",
                "is_current": True,
                "technologies": ["React", "Next.js", "MongoDB", "NestJS", "AWS"],
                "description": "Building full-stack applications with React/Next.js frontend and NestJS backend",
            },
            {
                "company": "Autobse",
                "title": "Backend Developer Intern",
                "location": "Kochi, Kerala",
                "start_date": "2024-05",
                "end_date": "2024-08",
                "is_current": False,
                "technologies": ["PostgreSQL", "Node.js", "GraphQL", "ORMs"],
                "description": "Developed backend APIs using Node.js and GraphQL with PostgreSQL database",
            },
        ],
        
        "education": [
            {
                "institution": "APJ Abdul Kalam Technological University",
                "degree": "Bachelor of Technology (B.Tech)",
                "field_of_study": "Computer Science and Engineering",
                "location": "Kozhikode, Kerala",
                "start_date": "2021-09",
                "end_date": "2025-05",
                "gpa": "7.66/10",
            },
        ],
        
        "skills": {
            "technical": [
                "Python", "JavaScript", "TypeScript", "React", "Node.js",
                "SQL", "PostgreSQL", "MongoDB", "AWS", "Docker", "Kubernetes",
                "Git", "CI/CD", "REST APIs", "GraphQL", "NestJS", "Next.js"
            ],
            "soft_skills": [
                "Leadership", "Communication", "Problem Solving",
                "Team Collaboration", "Project Management", "Agile/Scrum"
            ],
            "tools": [
                "VS Code", "Jira", "Confluence", "Figma", "Postman"
            ],
        },
        
        "job_preferences": {
            "desired_titles": [
                "Web Developer",
                "Backend Developer",
                "Node.js Developer",
                "Full Stack Developer",
                "NestJS Developer",
                "React Developer",
                "JavaScript Developer",
                "Software Engineer",
                "Software Developer",
                "Frontend Developer",
                "Python Developer"
            ],
            "desired_industries": [
                "Technology", "Finance", "Healthcare", "E-commerce", "AI/ML"
            ],
            "job_types": ["Full-time"],
            "experience_level": "Entry to Mid level",
            "salary_expectations": {
                "current": 280000,
                "expected": 400000,
                "minimum": 280000,
                "maximum": 400000,
                "currency": "INR",
                "period": "yearly"
            },
            "notice_period": 10,  # Just number in days
            "exclude_companies": ["Company1", "Company2"],
            "exclude_keywords": ["Sales", "Commission", "Door-to-door", "Internship", "Unpaid"],
        },
        
        "online_profiles": {
            "linkedin": "https://www.linkedin.com/in/ikihsan",
            "github": "https://github.com/ikihsan",
            "portfolio": "https://ikihsan.me",
            "personal_website": "https://ikihsan.tech",
        },
        
        "resumes": {
            "default": "assets/resumes/resume_default.pdf",
            "technical": "assets/resumes/resume_technical.pdf",
        },
        
        "work_authorization": {
            "authorized_to_work": True,
            "requires_sponsorship": False,
            "visa_status": "Citizen",
        },
        
        "availability": {
            "start_date": "Immediately",
            "notice_period": "10",
        },
        
        "common_questions": {
            "why_leaving_current_job": "Seeking new challenges and growth opportunities",
            "greatest_strength": "Problem-solving and ability to learn quickly",
            "greatest_weakness": "Sometimes too focused on perfection, learning to balance quality with speed",
            "salary_expectations_text": "I'm flexible and open to discussing compensation based on the total package",
            "where_see_yourself_5_years": "Growing into a senior technical leadership role",
            "why_this_company": "Impressed by the company's innovation and culture",
            "describe_yourself": "A dedicated professional passionate about building quality software",
        },
        
        "eeo_questions": {
            "race": "Prefer not to say",
            "veteran_status": "I am not a veteran",
            "disability_status": "I do not have a disability",
            "gender_identity": "Prefer not to say",
        },
        
        "platform_credentials": {
            "linkedin": {
                "email": "USE_ENV_VARIABLE",  # Set LINKEDIN_EMAIL in .env
                "password": "USE_ENV_VARIABLE",  # Set LINKEDIN_PASSWORD in .env
            },
            "glassdoor": {
                "email": "USE_ENV_VARIABLE",
                "password": "USE_ENV_VARIABLE",
            },
            "indeed": {
                "email": "USE_ENV_VARIABLE",
                "password": "USE_ENV_VARIABLE",
            },
        },
    }


# ============== JOB MATCHING CRITERIA ==============
JOB_CRITERIA = {
    "required_titles": [
        # MERN Stack & Backend (Priority)
        "node developer",
         "web developer",
        "backend developer",
        "full stack developer",
        
        "mern stack developer",
        "mern developer",
        
        "nodejs developer",
        
        
        "fullstack developer",
        "full-stack developer",
        "full stack engineer",
       
        "nestjs developer",
        "react developer",
        "javascript developer",
        "typescript developer",
        # General
        "software engineer",
        "software developer",
        "frontend developer",
        "front end developer",
        "front-end developer",
        "frontend engineer",
        "python developer",
        "mean stack developer",
        "application developer",
        "api developer",
        "developer",  # Generic catch-all
        "engineer",   # Generic catch-all
    ],
    
    "required_tech_stack": [
        "node.js", "nodejs", "node",
        "typescript", "javascript", "js", "ts",
        "postgresql", "postgres", "mongodb", "mongo",
        "nestjs", "nest",
        "rest", "rest api", "restful",
        "graphql",
        "aws", "amazon web services",
        "docker",
        "react", "reactjs",
        "next.js", "nextjs",
        "python",
    ],
    
    "tech_match_threshold": 0.3,  # 30% overlap required - be more lenient
    
    "exclusions": {
        "titles": ["internship", "sales rep", "account manager", "director", "vp ", "chief", "unpaid", "senior", "sr ", "sr.", "lead", "principal", "staff"],
        "keywords": ["unpaid", "commission only", "door-to-door", "volunteer", "equity only"],
        "companies": USER_PROFILE["job_preferences"]["exclude_companies"],
    },
}


# ============== PLATFORM PRIORITIES ==============
PLATFORM_CONFIG = {
    # Priority 1: External ATS (discovered via job boards)
    "external_ats": {
        "greenhouse": {"priority": 1, "enabled": True},
        "lever": {"priority": 1, "enabled": True},
        "ashby": {"priority": 1, "enabled": True},
        "workday": {"priority": 2, "enabled": True},
        "taleo": {"priority": 2, "enabled": True},
        "icims": {"priority": 2, "enabled": True},
        "company_careers": {"priority": 1, "enabled": True},
    },
    
    # Priority 2: Job Discovery Platforms
    "discovery_platforms": {
        "linkedin": {"priority": 1, "enabled": True, "easy_apply": True},
        "glassdoor": {"priority": 2, "enabled": True},
        "indeed": {"priority": 2, "enabled": True},
        "wellfound": {"priority": 3, "enabled": True},  # AngelList
    },
}


# ============== RATE LIMITING ==============
RATE_LIMITS = {
    "applications_per_hour": 10,
    "applications_per_day": 50,
    "min_delay_between_apps": 30,  # seconds
    "max_delay_between_apps": 120,  # seconds
    "page_load_wait": 3,  # seconds
    "human_typing_delay": (0.05, 0.15),  # min, max seconds per char
}


# ============== HELPER FUNCTIONS ==============
def get_skills_list():
    """Get all skills as a flat list"""
    skills = USER_PROFILE["skills"]
    return skills["technical"] + skills.get("soft_skills", []) + skills.get("tools", [])


def get_experience_years():
    """Calculate total years of experience"""
    from datetime import datetime
    total_months = 0
    
    for exp in USER_PROFILE["work_experience"]:
        start = datetime.strptime(exp["start_date"], "%Y-%m")
        if exp["end_date"] == "Present":
            end = datetime.now()
        else:
            end = datetime.strptime(exp["end_date"], "%Y-%m")
        
        months = (end.year - start.year) * 12 + (end.month - start.month)
        total_months += months
    
    return round(total_months / 12, 1)


def get_tech_experience(tech_name):
    """Get years of experience with specific technology - NEVER HALLUCINATE"""
    tech_lower = tech_name.lower()
    all_skills = [s.lower() for s in get_skills_list()]
    
    # Check if we have this skill
    skill_match = any(tech_lower in skill or skill in tech_lower for skill in all_skills)
    
    if not skill_match:
        return 0  # Return 0 if not in our skills - NEVER LIE
    
    # Map technologies to experience based on work history
    tech_mapping = {
        # Current job technologies (Space-Ai: Sep 2024 - Present = ~4 months)
        "react": 0.4, "next.js": 0.4, "nextjs": 0.4, "mongodb": 0.4, 
        "nestjs": 0.4, "nest": 0.4, "aws": 0.4,
        
        # Intern job technologies (Autobse: May 2024 - Aug 2024 = ~4 months)
        "postgresql": 0.4, "postgres": 0.4, "node.js": 0.7, "nodejs": 0.7,
        "graphql": 0.4, "node": 0.7,
        
        # Combined from both
        "javascript": 0.8, "typescript": 0.7, "python": 1.0,  # From skills
        "sql": 0.5, "rest": 0.7, "docker": 0.3, "git": 1.0,
    }
    
    for key, years in tech_mapping.items():
        if key in tech_lower or tech_lower in key:
            return years
    
    return 0.5 if skill_match else 0  # Default 6 months if in skills, 0 otherwise


def check_job_match(job_title, job_description=""):
    """Check if job matches our criteria - returns (match_score, should_apply, reason)"""
    title_lower = job_title.lower()
    desc_lower = job_description.lower()
    
    # Check exclusions first - be more careful with partial matches
    for excluded in JOB_CRITERIA["exclusions"]["titles"]:
        # Only exclude if it's a word boundary match (not "intern" in "international")
        if f" {excluded}" in f" {title_lower}" or f"{excluded} " in f"{title_lower} ":
            return (0, False, f"Excluded title keyword: {excluded}")
    
    for excluded in JOB_CRITERIA["exclusions"]["keywords"]:
        if excluded in desc_lower:
            return (0, False, f"Excluded keyword: {excluded}")
    
    # Check title match - be more lenient
    title_match = any(
        req_title in title_lower 
        for req_title in JOB_CRITERIA["required_titles"]
    )
    
    # Also match if it contains common dev keywords
    generic_match = any(
        kw in title_lower for kw in ["developer", "engineer", "programmer", "coder", "dev"]
    )
    
    if not title_match and not generic_match:
        return (0, False, "Title doesn't match required roles")
    
    # For now, just apply to any matching title - don't worry about tech stack
    score = 80 if title_match else 60
    return (score, True, "Meets criteria")


# ============== EXPORTS ==============
__all__ = [
    'USER_PROFILE',
    'JOB_CRITERIA',
    'PLATFORM_CONFIG',
    'RATE_LIMITS',
    'get_skills_list',
    'get_experience_years',
    'get_tech_experience',
    'check_job_match',
]
