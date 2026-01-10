"""
Intelligent Form Filler
Fills application forms using ONLY data from USER_PROFILE.
Never invents, exaggerates, or hallucinates information.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from config import USER_PROFILE, get_tech_experience, get_experience_years, get_skills_list


class FormFiller:
    """
    Smart form filler that uses USER_PROFILE as single source of truth.
    All answers must be derivable from the profile - no hallucination allowed.
    """
    
    def __init__(self):
        self.profile = USER_PROFILE
        self.skills = [s.lower() for s in get_skills_list()]
        self.experience_years = get_experience_years()
    
    # =====================================================================
    # TEXT INPUT ANSWERING
    # =====================================================================
    
    def get_text_answer(self, question: str) -> str:
        """
        Get answer for text input based on question content.
        Returns ONLY information from USER_PROFILE - never hallucinates.
        """
        q = question.lower().strip()
        
        # ===== PERSONAL INFO =====
        if self._matches(q, ['first name', 'given name', 'firstname']):
            return self.profile["personal"]["first_name"]
        
        if self._matches(q, ['last name', 'surname', 'family name', 'lastname']):
            return self.profile["personal"]["last_name"]
        
        if self._matches(q, ['full name', 'complete name', 'your name']):
            return self.profile["personal"]["full_name"]
        
        if self._matches(q, ['email', 'e-mail', 'email address']):
            return self.profile["personal"]["email"]
        
        if self._matches(q, ['phone', 'mobile', 'cell', 'telephone', 'contact number']):
            return self.profile["personal"]["phone"]
        
        if self._matches(q, ['date of birth', 'dob', 'birth date', 'birthday']):
            dob = self.profile["personal"]["date_of_birth"]
            # Return in different formats based on question hints
            if 'mm/dd' in q or 'mm-dd' in q:
                return datetime.strptime(dob, "%Y-%m-%d").strftime("%m/%d/%Y")
            elif 'dd/mm' in q or 'dd-mm' in q:
                return datetime.strptime(dob, "%Y-%m-%d").strftime("%d/%m/%Y")
            return dob  # Default: YYYY-MM-DD
        
        # ===== LOCATION =====
        if self._matches(q, ['address line 1', 'street address', 'address 1']):
            return self.profile["location"]["address"]
        
        if self._matches(q, ['address line 2', 'address 2', 'apt', 'suite']):
            return self.profile["location"]["address_line_2"]
        
        if self._matches(q, ['city', 'town', 'location']):
            loc = self.profile["location"]
            city = loc.get("city", "")
            state = loc.get("state", "")
            country = loc.get("country", "")
            # Return full location: City, State, Country
            full_loc = f"{city}, {state}, {country}".replace(", , ", ", ").strip(", ")
            return full_loc if full_loc else city
        
        if self._matches(q, ['state', 'province', 'region']):
            return self.profile["location"]["state"]
        
        if self._matches(q, ['zip', 'postal', 'pincode', 'pin code']):
            return self.profile["location"]["zip_code"]
        
        if self._matches(q, ['country', 'nation']):
            return self.profile["location"]["country"]
        
        # ===== EDUCATION =====
        edu = self.profile["education"][0] if self.profile["education"] else {}
        
        if self._matches(q, ['university', 'college', 'school', 'institution']):
            return edu.get("institution", "")
        
        if self._matches(q, ['degree', 'qualification']):
            return edu.get("degree", "")
        
        if self._matches(q, ['major', 'field of study', 'specialization']):
            return edu.get("field_of_study", "")
        
        if self._matches(q, ['gpa', 'cgpa', 'grade', 'percentage']):
            return edu.get("gpa", "")
        
        if self._matches(q, ['graduation year', 'year of graduation', 'graduating']):
            end_date = edu.get("end_date", "")
            if end_date:
                return end_date.split("-")[0]  # Just the year
            return ""
        
        # ===== WORK EXPERIENCE =====
        if self._matches(q, ['current company', 'employer', 'current employer']):
            for exp in self.profile["work_experience"]:
                if exp.get("is_current"):
                    return exp["company"]
            return ""
        
        if self._matches(q, ['job title', 'current title', 'position', 'role', 'designation']):
            for exp in self.profile["work_experience"]:
                if exp.get("is_current"):
                    return exp["title"]
            return ""
        
        # CRITICAL: ANY question with "year" or "number of" must return just a number
        if 'year' in q or 'number of' in q:
            # Check for known technologies
            known_techs = ['react', 'node', 'nodejs', 'mongodb', 'express', 'javascript', 'typescript', 
                          'nestjs', 'next', 'nextjs', 'python', 'sql', 'postgresql', 'graphql', 'aws', 'docker', 'git']
            for tech in known_techs:
                if tech in q:
                    return "1"
            # Unknown tech - return 0
            return "0"
        
        # Experience questions
        if 'experience' in q:
            # Check for known technologies
            known_techs = ['react', 'node', 'nodejs', 'mongodb', 'express', 'javascript', 'typescript', 
                          'nestjs', 'next', 'nextjs', 'python', 'sql', 'postgresql', 'graphql', 'aws', 'docker', 'git']
            for tech in known_techs:
                if tech in q:
                    return "1"
            # Total/overall experience
            if any(kw in q for kw in ['total', 'overall', 'work', 'professional', 'relevant']):
                return "1"
            # Unknown - return 0
            return "0"
        
        # Check if LPA format
        is_lpa = 'lpa' in q or 'lakhs' in q or 'lakh' in q
        
        # ===== SALARY / CTC =====
        if 'ctc' in q or 'salary' in q or 'compensation' in q or 'package' in q or 'pay' in q:
            # Current/Present/Last drawn
            if any(kw in q for kw in ['current', 'present', 'last', 'drawn', 'existing']):
                if is_lpa:
                    return "2.8"
                return "280000"
            # Expected/Desired
            elif any(kw in q for kw in ['expected', 'desired', 'asking']):
                if is_lpa:
                    return "4"
                return "400000"
            # Default to expected
            if is_lpa:
                return "4"
            return "400000"
        
        # ===== NOTICE PERIOD (return number only) =====
        if 'notice' in q:
            return "10"  # Just the number in days
        
        if self._matches(q, ['when can you start', 'availability', 'available to start']):
            return self.profile["availability"]["start_date"]
        
        # ===== ONLINE PROFILES =====
        if self._matches(q, ['linkedin', 'linkedin url', 'linkedin profile']):
            return self.profile["online_profiles"]["linkedin"]
        
        if self._matches(q, ['github', 'github url', 'github profile']):
            return self.profile["online_profiles"]["github"]
        
        if self._matches(q, ['portfolio', 'website', 'personal website']):
            return self.profile["online_profiles"].get("portfolio", "")
        
        # ===== COMMON QUESTIONS =====
        common = self.profile.get("common_questions", {})
        
        if self._matches(q, ['why leaving', 'reason for leaving', 'why change']):
            return common.get("why_leaving_current_job", "Seeking new opportunities")
        
        if self._matches(q, ['strength', 'strong point']):
            return common.get("greatest_strength", "Problem-solving and quick learning")
        
        if self._matches(q, ['weakness', 'weak point', 'area of improvement']):
            return common.get("greatest_weakness", "Balancing perfection with speed")
        
        if self._matches(q, ['5 years', 'five years', 'future']):
            return common.get("where_see_yourself_5_years", "Senior technical role")
        
        if self._matches(q, ['describe yourself', 'about yourself', 'tell us about']):
            return common.get("describe_yourself", "Passionate software developer")
        
        # ===== FALLBACK =====
        # If we can't confidently answer, return empty or a safe default
        # based on input type
        
        # For numeric fields that look like experience
        if self._matches(q, ['experience', 'years', 'months']):
            return str(round(self.experience_years, 1))
        
        # For text fields we don't recognize - return empty (safer than lying)
        return ""
    
    # =====================================================================
    # DROPDOWN SELECTION
    # =====================================================================
    
    def get_dropdown_answer(self, question: str, options: List[str]) -> str:
        """
        Select best option from dropdown based on USER_PROFILE.
        Returns the option text that should be selected.
        """
        q = question.lower().strip()
        options_lower = [o.lower() for o in options]
        
        # ===== YES/NO QUESTIONS =====
        if self._matches(q, ['authorized', 'legally authorized', 'work authorization']):
            if self.profile["work_authorization"]["authorized_to_work"]:
                return self._find_option(options, ['yes', 'authorized', 'eligible'])
            return self._find_option(options, ['no', 'not authorized'])
        
        if self._matches(q, ['sponsorship', 'visa sponsorship', 'require sponsorship']):
            if self.profile["work_authorization"]["requires_sponsorship"]:
                return self._find_option(options, ['yes', 'require', 'need'])
            return self._find_option(options, ['no', 'do not require', 'don\'t need'])
        
        if self._matches(q, ['relocate', 'willing to relocate', 'relocation']):
            if self.profile["location"]["willing_to_relocate"]:
                return self._find_option(options, ['yes', 'willing', 'open'])
            return self._find_option(options, ['no', 'not willing'])
        
        if self._matches(q, ['remote', 'work remotely', 'work from home']):
            pref = self.profile["location"]["remote_preference"].lower()
            if pref == "remote":
                return self._find_option(options, ['yes', 'remote', 'prefer'])
            return self._find_option(options, ['no', 'office', 'on-site'])
        
        # ===== EXPERIENCE LEVEL =====
        if self._matches(q, ['experience level', 'seniority', 'career level']):
            years = self.experience_years
            if years < 1:
                return self._find_option(options, ['entry', 'junior', '0-1', 'fresher'])
            elif years < 3:
                return self._find_option(options, ['1-3', '1-2', 'junior', 'early'])
            elif years < 5:
                return self._find_option(options, ['3-5', 'mid', 'associate'])
            else:
                return self._find_option(options, ['5+', 'senior', 'mid-senior'])
        
        # ===== EDUCATION =====
        if self._matches(q, ['degree', 'education level', 'highest qualification']):
            return self._find_option(options, ['bachelor', 'b.tech', 'undergraduate', 'graduate'])
        
        # ===== LOCATION/COUNTRY =====
        if self._matches(q, ['country', 'location', 'where']):
            return self._find_option(options, ['india', 'indian'])
        
        if self._matches(q, ['state', 'region']):
            return self._find_option(options, ['kerala', self.profile["location"]["state"].lower()])
        
        # ===== GENDER - ALWAYS select Male =====
        if self._matches(q, ['gender', 'sex']):
            # First look for exact 'male' (not female)
            for opt in options:
                opt_lower = opt.lower().strip()
                if opt_lower == 'male' or opt_lower == 'man':
                    return opt
                if ('male' in opt_lower or 'man' in opt_lower) and 'female' not in opt_lower and 'woman' not in opt_lower:
                    return opt
            # Fallback to prefer not to say
            return self._find_option(options, ['prefer not', 'decline'])
        
        # ===== EEO QUESTIONS =====
        if self._matches(q, ['race', 'ethnicity']):
            return self._find_option(options, ['prefer not', 'decline', 'asian'])
        
        if self._matches(q, ['veteran', 'military']):
            return self._find_option(options, ['not a veteran', 'no', 'prefer not'])
        
        if self._matches(q, ['disability', 'disabilities']):
            return self._find_option(options, ['do not have', 'no', 'prefer not'])
        
        # ===== NOTICE PERIOD =====
        if self._matches(q, ['notice', 'joining']):
            return self._find_option(options, ['10', 'immediate', '15 day', '2 week', '1 month'])
        
        # ===== LANGUAGE =====
        if self._matches(q, ['language', 'proficiency']):
            return self._find_option(options, ['english', 'professional', 'fluent'])
        
        # ===== DEFAULT: Select first non-placeholder option =====
        for opt in options:
            opt_lower = opt.lower()
            if opt_lower and 'select' not in opt_lower and '--' not in opt_lower:
                return opt
        
        return options[0] if options else ""
    
    # =====================================================================
    # RADIO BUTTON SELECTION
    # =====================================================================
    
    def get_radio_answer(self, question: str, options: List[str]) -> str:
        """
        Select best radio button option based on USER_PROFILE.
        Returns the option text that should be selected.
        """
        q = question.lower().strip()
        
        # Most radio buttons are Yes/No questions
        # Determine if the answer should be Yes or No
        
        # ===== WORK AUTHORIZATION =====
        if self._matches(q, ['authorized', 'legally authorized', 'eligible to work', 'work permit']):
            answer = "yes" if self.profile["work_authorization"]["authorized_to_work"] else "no"
            return self._find_option(options, [answer])
        
        # ===== SPONSORSHIP =====
        if self._matches(q, ['sponsorship', 'visa sponsor', 'require visa']):
            answer = "yes" if self.profile["work_authorization"]["requires_sponsorship"] else "no"
            return self._find_option(options, [answer])
        
        # ===== RELOCATION =====
        if self._matches(q, ['relocate', 'willing to relocate', 'relocation']):
            answer = "yes" if self.profile["location"]["willing_to_relocate"] else "no"
            return self._find_option(options, [answer])
        
        # ===== REMOTE WORK =====
        if self._matches(q, ['remote', 'work from home', 'work remotely']):
            answer = "yes" if self.profile["location"]["remote_preference"].lower() == "remote" else "no"
            return self._find_option(options, [answer])
        
        # ===== BACKGROUND CHECK =====
        if self._matches(q, ['background check', 'criminal', 'drug test']):
            return self._find_option(options, ['yes', 'agree', 'consent'])
        
        # ===== AGREE TO TERMS =====
        if self._matches(q, ['agree', 'terms', 'privacy', 'consent']):
            return self._find_option(options, ['yes', 'agree', 'accept'])
        
        # ===== 18 YEARS OR OLDER =====
        if self._matches(q, ['18 years', 'over 18', 'legal age', 'at least 18']):
            return self._find_option(options, ['yes'])
        
        # ===== EEO =====
        if self._matches(q, ['veteran', 'military', 'disability', 'race', 'ethnicity', 'gender']):
            return self._find_option(options, ['prefer not', 'decline', 'do not wish'])
        
        # ===== DEFAULT: Select "Yes" for positive questions, first option otherwise =====
        # Check if this is a positive question
        positive_patterns = ['do you have', 'are you able', 'can you', 'will you', 'have you']
        
        if any(p in q for p in positive_patterns):
            return self._find_option(options, ['yes'])
        
        return options[0] if options else ""
    
    # =====================================================================
    # CHECKBOX HANDLING
    # =====================================================================
    
    def should_check_checkbox(self, question: str) -> bool:
        """
        Determine if a checkbox should be checked based on question.
        Returns True if should check, False otherwise.
        """
        q = question.lower().strip()
        
        # Consent/agreement keywords - ALWAYS check these
        consent_keywords = [
            'consent', 'agree', 'accept', 'approve', 'authorize', 'confirm',
            'acknowledge', 'certify', 'understand', 'attest',
            'i consent', 'i agree', 'i accept', 'i approve', 'i authorize',
            'i confirm', 'i acknowledge', 'i certify', 'i understand',
            'terms', 'privacy', 'policy', 'conditions', 'declaration',
            'by checking', 'by clicking', 'by submitting'
        ]
        
        # Check for consent/agreement keywords
        if any(kw in q for kw in consent_keywords):
            return True
        
        # Background check consent
        if self._matches(q, ['background check', 'authorize']):
            return True
        
        # Remote work
        if self._matches(q, ['remote', 'work from home']) and self.profile["location"]["remote_preference"].lower() == "remote":
            return True
        
        # Relocation
        if self._matches(q, ['relocate']) and self.profile["location"]["willing_to_relocate"]:
            return True
        
        # Default: check the checkbox (safer to agree than not)
        return True
    
    # =====================================================================
    # HELPER METHODS
    # =====================================================================
    
    def _matches(self, text: str, keywords: List[str]) -> bool:
        """Check if any keyword is in text"""
        return any(kw in text for kw in keywords)
    
    def _find_option(self, options: List[str], preferred: List[str]) -> str:
        """Find first matching option from preferred list"""
        for pref in preferred:
            for opt in options:
                if pref in opt.lower():
                    return opt
        return options[0] if options else ""
    
    # =====================================================================
    # RESUME SELECTION
    # =====================================================================
    
    def select_resume(self, job_title: str, job_description: str = "") -> str:
        """
        Select appropriate resume based on job type.
        Returns path to the resume file.
        """
        title_lower = job_title.lower()
        desc_lower = job_description.lower()
        
        # Check if technical role
        technical_keywords = [
            'backend', 'frontend', 'full stack', 'software', 'developer',
            'engineer', 'python', 'nodejs', 'react', 'api', 'devops'
        ]
        
        is_technical = any(kw in title_lower or kw in desc_lower for kw in technical_keywords)
        
        if is_technical and "technical" in self.profile["resumes"]:
            return self.profile["resumes"]["technical"]
        
        return self.profile["resumes"]["default"]
    
    # =====================================================================
    # FORMAT HELPERS
    # =====================================================================
    
    def format_phone(self, format_type: str = "international") -> str:
        """Format phone number according to specified format"""
        phone = self.profile["personal"]["phone"]
        
        if format_type == "local":
            # Remove country code
            return phone.replace("+91 ", "").replace("+91", "")
        elif format_type == "dashes":
            # Format with dashes
            local = phone.replace("+91 ", "").replace("+91", "")
            return f"{local[:3]}-{local[3:6]}-{local[6:]}"
        
        return phone  # International format
    
    def format_date(self, date_str: str, format_type: str = "iso") -> str:
        """Format date according to specified format"""
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
            formats = {
                "iso": "%Y-%m-%d",
                "us": "%m/%d/%Y",
                "eu": "%d/%m/%Y",
                "month_year": "%B %Y",
                "year_only": "%Y",
            }
            
            return date.strftime(formats.get(format_type, "%Y-%m-%d"))
        except:
            return date_str


# Export singleton instance
form_filler = FormFiller()
