"""
AI-Powered Form Filler
Uses OpenAI/Groq/Free LLMs to intelligently answer application questions.
Falls back to rule-based answers if AI unavailable.
"""

import os
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

# Try importing AI libraries
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class AIFormFiller:
    """
    AI-powered form filler that uses LLMs to understand questions
    and generate accurate responses based on USER_PROFILE.
    
    Priority: OpenAI > Groq (free) > Gemini (free) > Rule-based fallback
    """
    
    def __init__(self, user_profile: Dict):
        self.profile = user_profile
        self.client = None
        self.provider = None
        
        # Initialize AI client
        self._init_ai_client()
        
        # Build profile context for AI
        self.profile_context = self._build_profile_context()
        
        # Cache for repeated questions
        self.answer_cache = {}
    
    def _init_ai_client(self):
        """Initialize the best available AI client"""
        
        # Try OpenAI first
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and OPENAI_AVAILABLE:
            try:
                self.client = openai.OpenAI(api_key=openai_key)
                self.provider = "openai"
                print("🤖 AI Form Filler: Using OpenAI")
                return
            except Exception as e:
                print(f"OpenAI init failed: {e}")
        
        # Try Groq (free tier - very fast)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and GROQ_AVAILABLE:
            try:
                self.client = Groq(api_key=groq_key)
                self.provider = "groq"
                print("🤖 AI Form Filler: Using Groq (free)")
                return
            except Exception as e:
                print(f"Groq init failed: {e}")
        
        # Try Google Gemini (free tier)
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=gemini_key)
                self.client = genai.GenerativeModel('gemini-pro')
                self.provider = "gemini"
                print("🤖 AI Form Filler: Using Google Gemini (free)")
                return
            except Exception as e:
                print(f"Gemini init failed: {e}")
        
        # Fallback to rule-based
        self.provider = "rules"
        print("🤖 AI Form Filler: Using rule-based fallback (no AI key found)")
    
    def _build_profile_context(self) -> str:
        """Build a concise profile context for AI prompts"""
        p = self.profile
        
        # Calculate experience
        total_exp = self._calculate_experience()
        
        context = f"""
CANDIDATE PROFILE:
Name: {p['personal']['full_name']}
Email: {p['personal']['email']}
Phone: {p['personal']['phone']}
Location: {p['location']['city']}, {p['location']['state']}, {p['location']['country']}
Date of Birth: {p['personal']['date_of_birth']}
Gender: {p['personal']['gender']}
Nationality: {p['personal']['nationality']}

WORK EXPERIENCE ({total_exp:.1f} years total):
"""
        for exp in p.get('work_experience', []):
            context += f"- {exp['title']} at {exp['company']} ({exp['start_date']} to {exp['end_date']})\n"
            context += f"  Technologies: {', '.join(exp.get('technologies', []))}\n"
        
        context += f"""
EDUCATION:
"""
        for edu in p.get('education', []):
            context += f"- {edu['degree']} in {edu['field_of_study']} from {edu['institution']} ({edu['start_date']} to {edu['end_date']})\n"
            context += f"  GPA: {edu.get('gpa', 'N/A')}\n"
        
        context += f"""
TECHNICAL SKILLS: {', '.join(p['skills']['technical'])}
SOFT SKILLS: {', '.join(p['skills'].get('soft_skills', []))}

ONLINE PROFILES:
- LinkedIn: {p['online_profiles']['linkedin']}
- GitHub: {p['online_profiles']['github']}
- Portfolio: {p['online_profiles'].get('portfolio', 'N/A')}

WORK AUTHORIZATION:
- Authorized to work: {'Yes' if p['work_authorization']['authorized_to_work'] else 'No'}
- Requires sponsorship: {'Yes' if p['work_authorization']['requires_sponsorship'] else 'No'}
- Visa status: {p['work_authorization']['visa_status']}

AVAILABILITY:
- Start date: {p['availability']['start_date']}
- Notice period: {p['availability']['notice_period']}

PREFERENCES:
- Willing to relocate: {'Yes' if p['location']['willing_to_relocate'] else 'No'}
- Remote preference: {p['location']['remote_preference']}

SALARY EXPECTATIONS: {p['job_preferences']['salary_expectations']['minimum']}-{p['job_preferences']['salary_expectations']['maximum']} {p['job_preferences']['salary_expectations']['currency']}/year
"""
        return context
    
    def _calculate_experience(self) -> float:
        """Calculate total years of experience"""
        total_months = 0
        for exp in self.profile.get('work_experience', []):
            try:
                start = datetime.strptime(exp['start_date'], "%Y-%m")
                if exp['end_date'] == "Present":
                    end = datetime.now()
                else:
                    end = datetime.strptime(exp['end_date'], "%Y-%m")
                months = (end.year - start.year) * 12 + (end.month - start.month)
                total_months += max(0, months)
            except:
                pass
        return total_months / 12
    
    def get_answer(self, question: str, field_type: str = "text", options: List[str] = None) -> str:
        """
        Get answer for a form field using AI or rules.
        
        Args:
            question: The question/label text
            field_type: 'text', 'dropdown', 'radio', 'checkbox', 'number'
            options: List of options for dropdown/radio fields
        
        Returns:
            The answer string
        """
        # Check cache first
        cache_key = f"{question}:{field_type}:{str(options)}"
        if cache_key in self.answer_cache:
            return self.answer_cache[cache_key]
        
        q = question.lower()
        
        # Check if LPA format is being asked
        is_lpa = 'lpa' in q or 'lakhs' in q or 'lakh' in q
        
        # CRITICAL: ANY question asking about years/experience/number MUST return just a number
        # This catches "describe your experience... number of years" type questions
        if any(kw in q for kw in ['year', 'years', 'number of year', 'how many']):
            # Check for known technologies we have experience in
            known_techs = ['react', 'node', 'nodejs', 'mongodb', 'express', 'javascript', 'typescript', 
                          'nestjs', 'next', 'nextjs', 'python', 'sql', 'postgresql', 'graphql', 'aws', 'docker', 'git']
            for tech in known_techs:
                if tech in q:
                    self.answer_cache[cache_key] = "1"
                    return "1"
            # Unknown technology - return 0
            self.answer_cache[cache_key] = "0"
            return "0"
        
        # Experience questions without "year" keyword
        if 'experience' in q:
            # Check for known technologies
            known_techs = ['react', 'node', 'nodejs', 'mongodb', 'express', 'javascript', 'typescript', 
                          'nestjs', 'next', 'nextjs', 'python', 'sql', 'postgresql', 'graphql', 'aws', 'docker', 'git']
            for tech in known_techs:
                if tech in q:
                    self.answer_cache[cache_key] = "1"
                    return "1"
            # Total/overall experience
            if any(kw in q for kw in ['total', 'overall', 'work', 'professional']):
                self.answer_cache[cache_key] = "1"
                return "1"
            # Unknown technology experience - return 0
            self.answer_cache[cache_key] = "0"
            return "0"
        
        # CRITICAL: Handle salary/CTC/notice period/experience BEFORE AI - always return numbers
        # CTC/Salary questions - catch all variations including "current/last drawn"
        if 'ctc' in q or 'salary' in q or 'compensation' in q or 'package' in q or 'pay' in q:
            # Current/Present/Last drawn salary
            if any(kw in q for kw in ['current', 'present', 'last', 'drawn', 'existing']):
                if is_lpa:
                    self.answer_cache[cache_key] = "2.8"
                    return "2.8"
                self.answer_cache[cache_key] = "280000"
                return "280000"
            # Expected/Desired salary
            elif any(kw in q for kw in ['expected', 'desired', 'asking', 'require']):
                if is_lpa:
                    self.answer_cache[cache_key] = "4"
                    return "4"
                self.answer_cache[cache_key] = "400000"
                return "400000"
            # Generic CTC/salary question - default to expected
            else:
                if is_lpa:
                    self.answer_cache[cache_key] = "4"
                    return "4"
                self.answer_cache[cache_key] = "400000"
                return "400000"
        
        # Notice period - just number (catch "notice period", "notice", etc.)
        if 'notice' in q:
            self.answer_cache[cache_key] = "10"
            return "10"
        
        # Try AI first
        if self.provider != "rules":
            try:
                answer = self._get_ai_answer(question, field_type, options)
                if answer:
                    self.answer_cache[cache_key] = answer
                    return answer
            except Exception as e:
                print(f"AI error: {e}, falling back to rules")
        
        # Fallback to rule-based
        answer = self._get_rule_based_answer(question, field_type, options)
        self.answer_cache[cache_key] = answer
        return answer
    
    def _get_ai_answer(self, question: str, field_type: str, options: List[str] = None) -> Optional[str]:
        """Get answer using AI"""
        
        # Build the prompt
        prompt = self._build_prompt(question, field_type, options)
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Fast and cheap
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.1  # Low temperature for consistent answers
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "groq":
                response = self.client.chat.completions.create(
                    model="llama-3.1-8b-instant",  # Fast free model
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.1
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "gemini":
                full_prompt = f"{self._get_system_prompt()}\n\n{prompt}"
                response = self.client.generate_content(full_prompt)
                return response.text.strip()
        
        except Exception as e:
            print(f"AI API error: {e}")
            return None
        
        return None
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI"""
        return f"""You are a job application form filler assistant. Your task is to answer application questions based ONLY on the candidate's profile information provided below.

CRITICAL RULES:
1. NEVER invent, exaggerate, or hallucinate any information
2. If the candidate doesn't have experience with something, answer "0" or "No"
3. For years of experience questions, calculate based on actual work history
4. Keep answers concise and professional
5. For dropdown/radio questions, return ONLY the exact option text
6. For numeric fields, return ONLY the number
7. For yes/no questions, return ONLY "Yes" or "No"

{self.profile_context}"""
    
    def _build_prompt(self, question: str, field_type: str, options: List[str] = None) -> str:
        """Build the prompt for AI"""
        prompt = f"Question: {question}\n"
        prompt += f"Field type: {field_type}\n"
        
        if options:
            prompt += f"Available options: {', '.join(options)}\n"
            prompt += "\nReturn ONLY the exact text of the best matching option."
        elif field_type == "number":
            prompt += "\nReturn ONLY the numeric value."
        elif field_type in ["radio", "checkbox"]:
            prompt += "\nReturn ONLY 'Yes' or 'No'."
        else:
            prompt += "\nProvide a concise, professional answer."
        
        return prompt
    
    def _get_rule_based_answer(self, question: str, field_type: str, options: List[str] = None) -> str:
        """Fallback rule-based answer system"""
        q = question.lower().strip()
        p = self.profile
        
        # ===== PERSONAL INFO =====
        if any(kw in q for kw in ['first name', 'given name', 'firstname']):
            return p['personal']['first_name']
        
        if any(kw in q for kw in ['last name', 'surname', 'family name', 'lastname']):
            return p['personal']['last_name']
        
        if any(kw in q for kw in ['full name', 'complete name', 'your name']):
            return p['personal']['full_name']
        
        if any(kw in q for kw in ['email', 'e-mail']):
            return p['personal']['email']
        
        if any(kw in q for kw in ['phone', 'mobile', 'cell', 'telephone']):
            return p['personal']['phone']
        
        if any(kw in q for kw in ['date of birth', 'dob', 'birth date']):
            return p['personal']['date_of_birth']
        
        # ===== LOCATION - Return full location =====
        if any(kw in q for kw in ['city', 'town', 'location']):
            loc = p['location']
            city = loc.get('city', '')
            state = loc.get('state', '')
            country = loc.get('country', '')
            # Return full location: City, State, Country
            full_loc = f"{city}, {state}, {country}".replace(", , ", ", ").strip(", ")
            return full_loc if full_loc else city
        
        if any(kw in q for kw in ['state', 'province']):
            return p['location']['state']
        
        if any(kw in q for kw in ['country', 'nation']):
            return p['location']['country']
        
        if any(kw in q for kw in ['zip', 'postal', 'pincode']):
            return p['location']['zip_code']
        
        if 'address' in q:
            return p['location']['address']
        
        # ===== EXPERIENCE =====
        if any(kw in q for kw in ['total experience', 'years of experience', 'overall experience']):
            return str(round(self._calculate_experience(), 1))
        
        # Technology-specific experience
        tech_keywords = [
            ('python', 1.0), ('javascript', 0.8), ('typescript', 0.7),
            ('react', 0.4), ('node', 0.7), ('nestjs', 0.4), ('aws', 0.4),
            ('docker', 0.3), ('sql', 0.5), ('mongodb', 0.4), ('postgresql', 0.4),
            ('graphql', 0.4), ('git', 1.0),
        ]
        
        for tech, years in tech_keywords:
            if tech in q:
                skills_lower = [s.lower() for s in p['skills']['technical']]
                if any(tech in s for s in skills_lower):
                    return str(years) if 'year' in q else str(int(years * 12))
                return "0"
        
        # For unknown technologies, return 0
        if any(kw in q for kw in ['experience', 'years', 'months']) and any(kw in q for kw in ['salesforce', 'apex', 'sap', 'oracle', 'azure', 'java', 'c++', 'ruby', 'go', 'swift']):
            return "0"
        
        # ===== ONLINE PROFILES =====
        if 'linkedin' in q:
            return p['online_profiles']['linkedin']
        
        if 'github' in q:
            return p['online_profiles']['github']
        
        if any(kw in q for kw in ['portfolio', 'website']):
            return p['online_profiles'].get('portfolio', '')
        
        # ===== EDUCATION =====
        edu = p['education'][0] if p.get('education') else {}
        
        if any(kw in q for kw in ['university', 'college', 'school', 'institution']):
            return edu.get('institution', '')
        
        if any(kw in q for kw in ['degree', 'qualification']):
            return edu.get('degree', '')
        
        if any(kw in q for kw in ['major', 'field of study']):
            return edu.get('field_of_study', '')
        
        if any(kw in q for kw in ['gpa', 'grade']):
            return edu.get('gpa', '')
        
        # ===== WORK AUTHORIZATION =====
        if options:
            return self._select_best_option(q, options)
        
        # ===== SALARY / CTC (return numbers only) =====
        if any(kw in q for kw in ['current salary', 'current ctc', 'present ctc', 'present salary', 'last drawn', 'current compensation', 'current pay', 'current package']):
            return "280000"  # Current CTC in INR
        
        if any(kw in q for kw in ['expected salary', 'desired salary', 'expected ctc', 'desired ctc', 'expected compensation', 'expected pay', 'expected package']):
            return "400000"  # Expected CTC in INR
        
        # Generic salary/ctc question - return expected
        if any(kw in q for kw in ['salary', 'ctc', 'compensation', 'lpa', 'package']):
            return "400000"
        
        # ===== AVAILABILITY (return numbers only) =====
        if any(kw in q for kw in ['notice period', 'notice']):
            return "10"  # Just the number in days
        
        if any(kw in q for kw in ['start date', 'when can you start']):
            return p['availability']['start_date']
        
        # ===== DEFAULT =====
        return ""
    
    def _select_best_option(self, question: str, options: List[str]) -> str:
        """Select best option from a list"""
        q = question.lower()
        options_lower = [o.lower() for o in options]
        p = self.profile
        
        # Work authorization
        if any(kw in q for kw in ['authorized', 'legally authorized']):
            if p['work_authorization']['authorized_to_work']:
                return self._find_match(options, ['yes', 'authorized'])
            return self._find_match(options, ['no'])
        
        # Sponsorship
        if any(kw in q for kw in ['sponsorship', 'visa']):
            if p['work_authorization']['requires_sponsorship']:
                return self._find_match(options, ['yes', 'require'])
            return self._find_match(options, ['no', 'do not'])
        
        # Relocation
        if 'relocate' in q:
            if p['location']['willing_to_relocate']:
                return self._find_match(options, ['yes', 'willing'])
            return self._find_match(options, ['no'])
        
        # Remote
        if 'remote' in q:
            if p['location']['remote_preference'].lower() == 'remote':
                return self._find_match(options, ['yes', 'remote'])
            return self._find_match(options, ['no', 'hybrid', 'office'])
        
        # Gender - ALWAYS select Male
        if 'gender' in q:
            # First look for exact 'male' (not female)
            for opt in options:
                opt_lower = opt.lower().strip()
                if opt_lower == 'male' or opt_lower == 'man':
                    return opt
                if ('male' in opt_lower or 'man' in opt_lower) and 'female' not in opt_lower and 'woman' not in opt_lower:
                    return opt
            # Fallback to prefer not to say
            return self._find_match(options, ['prefer not', 'decline'])
        
        # Default: first non-placeholder option
        for opt in options:
            if opt.lower() and 'select' not in opt.lower():
                return opt
        
        return options[0] if options else ""
    
    def _find_match(self, options: List[str], preferred: List[str]) -> str:
        """Find matching option from preferred list"""
        for pref in preferred:
            for opt in options:
                if pref in opt.lower():
                    return opt
        return options[0] if options else ""


# Global instance
_ai_filler = None

def get_ai_filler(profile: Dict) -> AIFormFiller:
    """Get or create AI filler instance"""
    global _ai_filler
    if _ai_filler is None:
        _ai_filler = AIFormFiller(profile)
    return _ai_filler
