"""
Smart Form Filler - Handles ALL LinkedIn Easy Apply form fields
With extensive debugging and AI-powered answers
"""

import os
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException,
    ElementNotInteractableException, ElementClickInterceptedException
)


class SmartFormFiller:
    """
    Comprehensive form filler that handles ALL LinkedIn Easy Apply fields.
    Uses AI when available, falls back to smart rules.
    """
    
    def __init__(self, driver: WebDriver, profile: Dict, ai_filler=None):
        self.driver = driver
        self.profile = profile
        self.ai_filler = ai_filler
        
        # Build quick lookup for profile data
        self._build_answer_map()
    
    def _build_answer_map(self):
        """Build a map of common questions to answers from profile"""
        p = self.profile
        personal = p.get("personal", {})
        location = p.get("location", {})
        work_auth = p.get("work_authorization", {})
        prefs = p.get("job_preferences", {})
        online = p.get("online_profiles", {})
        skills = p.get("skills", {})
        
        # Total years of experience - always set to 1
        work_exp = p.get("work_experience", [])
        total_years = 1
        
        # Get all technologies from work experience
        all_techs = set()
        for job in work_exp:
            for tech in job.get("technologies", []):
                all_techs.add(tech.lower())
        
        # Add skills
        for skill in skills.get("technical", []):
            all_techs.add(skill.lower())
        
        self.all_technologies = all_techs
        self.total_years = total_years
        
        # Quick answer map
        self.answers = {
            # Personal
            "first name": personal.get("first_name", ""),
            "last name": personal.get("last_name", ""),
            "full name": personal.get("full_name", ""),
            "email": personal.get("email", ""),
            "phone": personal.get("phone", ""),
            "mobile": personal.get("phone", ""),
            
            # Location - city should include full location
            "city": f"{location.get('city', '')}, {location.get('state', '')}, {location.get('country', '')}".replace(', , ', ', ').strip(', '),
            "location": f"{location.get('city', '')}, {location.get('state', '')}, {location.get('country', '')}".replace(', , ', ', ').strip(', '),
            "state": location.get("state", ""),
            "zip": location.get("zip_code", ""),
            "postal": location.get("zip_code", ""),
            "country": location.get("country", ""),
            "address": location.get("address", ""),
            
            # Online
            "linkedin": online.get("linkedin", ""),
            "github": online.get("github", ""),
            "portfolio": online.get("portfolio", ""),
            "website": online.get("personal_website", ""),
            
            # Experience
            "years of experience": str(total_years),
            "total experience": str(total_years),
            
            # Education
            "degree": "Bachelor's",
            "university": p.get("education", [{}])[0].get("institution", ""),
            "gpa": p.get("education", [{}])[0].get("gpa", "").split("/")[0],
            
            # Salary - just numbers (in LPA if asked, else full amount)
            "salary": "4",
            "current salary": "2.8",
            "current ctc": "2.8",
            "ctc": "4",
            "current compensation": "2.8",
            "expected salary": "4",
            "expected ctc": "4",
            "expected compensation": "4",
            "lpa": "4",
            "lakhs": "4",
            
            # Availability - just numbers
            "start date": "Immediately",
            "notice period": "10",
            "notice": "10",
            
            # Experience - just number
            "years of experience": "1",
            "total experience": "1",
            "work experience": "1",
        }
        
        # Yes/No answers
        self.yes_questions = [
            "authorized to work", "legally authorized", "eligible to work",
            "work authorization", "right to work", "permission to work",
            "18 years", "at least 18", "over 18", "legal age",
            "background check", "agree to", "consent", "acknowledge",
            "i consent", "i agree", "i approve", "i accept", "i acknowledge",
            "i confirm", "i authorize", "i understand", "i certify",
            "agree", "accept", "approve", "confirm", "authorize",
            "terms and conditions", "privacy policy", "terms of service",
            "willing to relocate", "open to relocation",
            "comfortable with", "willing to",
            "us citizen", "permanent resident",
            "can commute", "able to commute",
        ]
        
        self.no_questions = [
            "require sponsorship", "need sponsorship", "visa sponsorship",
            "require visa", "need visa", "immigration sponsorship",
            "disability", "veteran", "protected veteran",
            "have you been convicted", "criminal", "felony",
        ]
    
    def _calculate_experience_years(self, work_exp: List[Dict]) -> int:
        """Calculate total years of experience from work history"""
        from datetime import datetime
        
        if not work_exp:
            return 1  # Default to 1 if no experience
        
        total_months = 0
        for exp in work_exp:
            try:
                start_str = exp.get("start_date", "")
                end_str = exp.get("end_date", "")
                
                if not start_str:
                    continue
                    
                start = datetime.strptime(start_str, "%Y-%m")
                
                if end_str == "Present" or exp.get("is_current", False):
                    end = datetime.now()
                else:
                    end = datetime.strptime(end_str, "%Y-%m")
                
                months = (end.year - start.year) * 12 + (end.month - start.month)
                total_months += max(0, months)  # Avoid negative months
            except (ValueError, TypeError):
                # If date parsing fails, estimate 6 months per job
                total_months += 6
        
        years = max(1, round(total_months / 12))  # At least 1 year, rounded
        return years
    
    def fill_all_fields(self) -> int:
        """
        Fill ALL form fields on the current page.
        Returns the number of fields filled.
        """
        filled_count = 0
        
        print("      🔍 Scanning form fields...")
        
        # 1. Fill text inputs and textareas
        filled_count += self._fill_text_fields()
        
        # 2. Fill number inputs
        filled_count += self._fill_number_fields()
        
        # 3. Fill dropdowns/selects
        filled_count += self._fill_dropdowns()
        
        # 4. Fill radio buttons
        filled_count += self._fill_radio_groups()
        
        # 5. Fill checkboxes
        filled_count += self._fill_checkboxes()
        
        # 6. Handle file uploads
        self._handle_file_uploads()
        
        print(f"      ✅ Filled {filled_count} fields")
        return filled_count
    
    def _fill_text_fields(self) -> int:
        """Fill all text inputs and textareas"""
        filled = 0
        
        # Find all text inputs
        selectors = [
            'input[type="text"]',
            'input[type="email"]',
            'input[type="tel"]',
            'input[type="url"]',
            'input:not([type])',  # Default type is text
            'textarea',
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    f'.jobs-easy-apply-content {selector}')
                
                for elem in elements:
                    if self._fill_text_element(elem):
                        filled += 1
            except Exception as e:
                pass
        
        return filled
    
    def _fill_text_element(self, elem: WebElement) -> bool:
        """Fill a single text element"""
        try:
            if not elem.is_displayed():
                return False
            
            # Skip if already has value
            current_value = elem.get_attribute('value') or ''
            if current_value.strip():
                return False
            
            # Get the question/label
            question = self._get_field_question(elem)
            if not question:
                return False
            
            question_lower = question.lower()
            print(f"         📝 Text field: {question[:50]}...")
            
            # Get answer
            answer = self._get_text_answer(question_lower)
            
            if answer:
                self._safe_fill(elem, answer)
                print(f"            → {answer}")
                return True
            else:
                print(f"            → [NO ANSWER FOUND]")
                
        except Exception as e:
            pass
        
        return False
    
    def _fill_number_fields(self) -> int:
        """Fill all number inputs"""
        filled = 0
        
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR,
                '.jobs-easy-apply-content input[type="number"]')
            
            for elem in elements:
                try:
                    if not elem.is_displayed():
                        continue
                    
                    current = elem.get_attribute('value') or ''
                    if current.strip():
                        continue
                    
                    question = self._get_field_question(elem)
                    if not question:
                        continue
                    
                    question_lower = question.lower()
                    print(f"         🔢 Number field: {question[:50]}...")
                    
                    # Get number answer
                    answer = self._get_number_answer(question_lower)
                    
                    if answer is not None:
                        self._safe_fill(elem, str(answer))
                        print(f"            → {answer}")
                        filled += 1
                    else:
                        # Default to 1 for any number field (safer than 0)
                        self._safe_fill(elem, "1")
                        print(f"            → 1 (default)")
                        filled += 1
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
        
        return filled
    
    def _fill_dropdowns(self) -> int:
        """Fill all dropdown/select elements"""
        filled = 0
        
        try:
            selects = self.driver.find_elements(By.CSS_SELECTOR,
                '.jobs-easy-apply-content select')
            
            for select_elem in selects:
                try:
                    if not select_elem.is_displayed():
                        continue
                    
                    select = Select(select_elem)
                    current = select.first_selected_option.text.lower()
                    
                    # Skip if already selected (not placeholder)
                    if current and 'select' not in current and 'choose' not in current:
                        continue
                    
                    question = self._get_field_question(select_elem)
                    options = [o.text for o in select.options if o.text.strip()]
                    
                    print(f"         📋 Dropdown: {question[:50]}...")
                    print(f"            Options: {options[:5]}...")
                    
                    # Get best option
                    best_option = self._get_dropdown_answer(question.lower(), options)
                    
                    if best_option:
                        try:
                            select.select_by_visible_text(best_option)
                            print(f"            → {best_option}")
                            filled += 1
                        except:
                            # Try index
                            if len(options) > 1:
                                select.select_by_index(1)
                                print(f"            → {options[1]} (by index)")
                                filled += 1
                                
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
        
        return filled
    
    def _fill_radio_groups(self) -> int:
        """Fill all radio button groups"""
        filled = 0
        
        try:
            # Find fieldsets or divs containing radio buttons
            containers = self.driver.find_elements(By.CSS_SELECTOR,
                '.jobs-easy-apply-content fieldset, '
                '.jobs-easy-apply-content [data-test-form-element], '
                '.jobs-easy-apply-content .fb-dash-form-element')
            
            processed_names = set()
            
            for container in containers:
                try:
                    radios = container.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                    
                    if not radios:
                        continue
                    
                    # Skip if already selected
                    if any(r.is_selected() for r in radios):
                        continue
                    
                    # Get radio name to avoid duplicates
                    radio_name = radios[0].get_attribute('name') or ''
                    if radio_name in processed_names:
                        continue
                    processed_names.add(radio_name)
                    
                    # Get question text
                    question = container.text.strip()
                    
                    # Get labels/options
                    labels = container.find_elements(By.TAG_NAME, 'label')
                    options = [l.text.strip() for l in labels if l.text.strip()]
                    
                    print(f"         🔘 Radio group: {question[:50]}...")
                    print(f"            Options: {options}")
                    
                    # Determine best answer
                    best_answer = self._get_radio_answer(question.lower(), options)
                    
                    # Click the matching label
                    clicked = False
                    for label in labels:
                        if best_answer.lower() in label.text.lower():
                            try:
                                label.click()
                                print(f"            → {label.text}")
                                filled += 1
                                clicked = True
                                break
                            except:
                                # Try clicking the radio directly
                                for radio in radios:
                                    radio_id = radio.get_attribute('id')
                                    label_for = label.get_attribute('for')
                                    if radio_id == label_for:
                                        self.driver.execute_script("arguments[0].click();", radio)
                                        print(f"            → {label.text} (JS click)")
                                        filled += 1
                                        clicked = True
                                        break
                    
                    # If no match, click first option
                    if not clicked and labels:
                        try:
                            labels[0].click()
                            print(f"            → {labels[0].text} (default first)")
                            filled += 1
                        except:
                            pass
                            
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
        
        return filled
    
    def _fill_checkboxes(self) -> int:
        """Fill ALL checkboxes - always check them, especially consent/agree boxes"""
        filled = 0
        
        # Keywords that indicate a checkbox should definitely be checked
        consent_keywords = [
            'consent', 'agree', 'accept', 'approve', 'authorize', 'confirm',
            'acknowledge', 'certify', 'understand', 'attest',
            'i consent', 'i agree', 'i accept', 'i approve', 'i authorize',
            'i confirm', 'i acknowledge', 'i certify', 'i understand',
            'terms', 'privacy', 'policy', 'conditions', 'declaration',
            'by checking', 'by clicking', 'by submitting'
        ]
        
        try:
            # Find all checkboxes in the form - broader selectors
            checkbox_selectors = [
                '.jobs-easy-apply-content input[type="checkbox"]',
                '.jobs-easy-apply-modal input[type="checkbox"]',
                'input[type="checkbox"]',
                '[role="checkbox"]'
            ]
            
            all_checkboxes = []
            for selector in checkbox_selectors:
                try:
                    found = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_checkboxes.extend(found)
                except:
                    pass
            
            # Remove duplicates
            seen_ids = set()
            unique_checkboxes = []
            for cb in all_checkboxes:
                try:
                    cb_id = cb.get_attribute('id') or id(cb)
                    if cb_id not in seen_ids:
                        seen_ids.add(cb_id)
                        unique_checkboxes.append(cb)
                except:
                    unique_checkboxes.append(cb)
            
            for cb in unique_checkboxes:
                try:
                    # Skip if already checked
                    is_checked = cb.is_selected()
                    if not is_checked:
                        # Also check aria-checked attribute
                        aria_checked = cb.get_attribute('aria-checked')
                        is_checked = aria_checked == 'true'
                    
                    if is_checked:
                        continue
                    
                    # Check visibility
                    is_visible = False
                    try:
                        is_visible = cb.is_displayed()
                    except:
                        pass
                    
                    if not is_visible:
                        # Try to find parent and check visibility
                        try:
                            parent = cb.find_element(By.XPATH, '..')
                            is_visible = parent.is_displayed()
                        except:
                            pass
                    
                    question = self._get_field_question(cb)
                    question_lower = question.lower()
                    print(f"         ☐ Checkbox: {question[:50]}...")
                    
                    # Check if this is a consent/agreement checkbox
                    is_consent_box = any(kw in question_lower for kw in consent_keywords)
                    
                    # ALWAYS try to check consent boxes, optionally check others
                    should_check = is_consent_box or is_visible
                    
                    if not should_check:
                        print(f"            → Skipped (not consent/visible)")
                        continue
                    
                    checked = False
                    
                    # Method 1: Direct click
                    try:
                        cb.click()
                        time.sleep(0.1)
                        if cb.is_selected() or cb.get_attribute('aria-checked') == 'true':
                            checked = True
                            print(f"            → ✓ Checked (direct)")
                    except:
                        pass
                    
                    # Method 2: JavaScript click on checkbox
                    if not checked:
                        try:
                            self.driver.execute_script("arguments[0].click();", cb)
                            time.sleep(0.1)
                            if cb.is_selected() or cb.get_attribute('aria-checked') == 'true':
                                checked = True
                                print(f"            → ✓ Checked (JS click)")
                        except:
                            pass
                    
                    # Method 3: Click via label using 'for' attribute
                    if not checked:
                        cb_id = cb.get_attribute('id')
                        if cb_id:
                            try:
                                label = self.driver.find_element(By.CSS_SELECTOR, f'label[for="{cb_id}"]')
                                label.click()
                                time.sleep(0.1)
                                checked = cb.is_selected() or cb.get_attribute('aria-checked') == 'true'
                                if checked:
                                    print(f"            → ✓ Checked (via label for)")
                            except:
                                pass
                    
                    # Method 4: Click parent label element
                    if not checked:
                        try:
                            parent_label = cb.find_element(By.XPATH, './ancestor::label')
                            parent_label.click()
                            time.sleep(0.1)
                            checked = cb.is_selected() or cb.get_attribute('aria-checked') == 'true'
                            if checked:
                                print(f"            → ✓ Checked (parent label)")
                        except:
                            pass
                    
                    # Method 5: Set checked attribute via JavaScript
                    if not checked:
                        try:
                            self.driver.execute_script("""
                                arguments[0].checked = true;
                                arguments[0].setAttribute('checked', 'checked');
                                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                                arguments[0].dispatchEvent(new Event('click', {bubbles: true}));
                            """, cb)
                            time.sleep(0.1)
                            checked = True
                            print(f"            → ✓ Checked (JS set checked)")
                        except:
                            pass
                    
                    # Method 6: For role="checkbox", set aria-checked
                    if not checked:
                        try:
                            role = cb.get_attribute('role')
                            if role == 'checkbox':
                                self.driver.execute_script("""
                                    arguments[0].setAttribute('aria-checked', 'true');
                                    arguments[0].click();
                                """, cb)
                                time.sleep(0.1)
                                checked = True
                                print(f"            → ✓ Checked (aria-checked)")
                        except:
                            pass
                    
                    # Method 7: Click on nearby clickable elements (spans, divs with checkbox styling)
                    if not checked:
                        try:
                            # Try clicking sibling or nearby elements
                            clickable = cb.find_element(By.XPATH, './following-sibling::*[1]')
                            clickable.click()
                            time.sleep(0.1)
                            checked = cb.is_selected() or cb.get_attribute('aria-checked') == 'true'
                            if checked:
                                print(f"            → ✓ Checked (sibling click)")
                        except:
                            pass
                    
                    if checked:
                        filled += 1
                    else:
                        print(f"            → ❌ Could not check")
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
        
        return filled
    
    def _handle_file_uploads(self):
        """Handle resume/document uploads"""
        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                '.jobs-easy-apply-content input[type="file"]')
            
            for inp in file_inputs:
                try:
                    question = self._get_field_question(inp).lower()
                    
                    if 'resume' in question or 'cv' in question:
                        resume_path = self.profile.get("resumes", {}).get("default", "")
                        if resume_path and os.path.exists(resume_path):
                            inp.send_keys(os.path.abspath(resume_path))
                            print(f"         📎 Uploaded resume: {resume_path}")
                        else:
                            print(f"         ⚠️ Resume not found: {resume_path}")
                            
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _get_field_question(self, elem: WebElement) -> str:
        """Get the question/label text for a form field"""
        question = ""
        
        try:
            # 1. Try aria-label
            question = elem.get_attribute('aria-label') or ''
            if question:
                return question
            
            # 2. Try placeholder
            question = elem.get_attribute('placeholder') or ''
            if question:
                return question
            
            # 3. Try label by ID
            elem_id = elem.get_attribute('id')
            if elem_id:
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, f'label[for="{elem_id}"]')
                    question = label.text.strip()
                    if question:
                        return question
                except:
                    pass
            
            # 4. Try parent elements for text
            parent = elem
            for _ in range(5):
                try:
                    parent = parent.find_element(By.XPATH, '..')
                    text = parent.text.strip()
                    # Get first meaningful line
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    if lines and 10 < len(lines[0]) < 300:
                        return lines[0]
                except:
                    break
            
            # 5. Try name attribute
            name = elem.get_attribute('name') or ''
            if name:
                return name.replace('-', ' ').replace('_', ' ')
                
        except Exception as e:
            pass
        
        return question
    
    def _get_text_answer(self, question: str) -> str:
        """Get answer for a text question"""
        q = question.lower()
        
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
        
        # Handle salary/CTC questions
        if 'ctc' in q or 'salary' in q or 'compensation' in q or 'package' in q or 'pay' in q:
            if any(x in q for x in ['current', 'present', 'last', 'drawn', 'existing']):
                if is_lpa:
                    return "2.8"
                return "280000"
            elif any(x in q for x in ['expected', 'desired', 'asking']):
                if is_lpa:
                    return "4"
                return "400000"
            # Default to expected
            if is_lpa:
                return "4"
            return "400000"
        
        # Handle notice period - return numbers only
        if 'notice' in q:
            return "10"
        
        # Check direct map first
        for key, value in self.answers.items():
            if key in q:
                return value
        
        # Use AI if available
        if self.ai_filler:
            try:
                answer = self.ai_filler.get_answer(question, 'text')
                if answer:
                    return answer
            except:
                pass
        
        # Fallback patterns
        if any(x in q for x in ['first name', 'given name']):
            return self.profile.get("personal", {}).get("first_name", "")
        if any(x in q for x in ['last name', 'surname', 'family name']):
            return self.profile.get("personal", {}).get("last_name", "")
        if 'email' in q:
            return self.profile.get("personal", {}).get("email", "")
        if any(x in q for x in ['phone', 'mobile', 'contact number']):
            return self.profile.get("personal", {}).get("phone", "")
        if 'linkedin' in q:
            return self.profile.get("online_profiles", {}).get("linkedin", "")
        if 'github' in q:
            return self.profile.get("online_profiles", {}).get("github", "")
        if any(x in q for x in ['portfolio', 'website', 'personal site']):
            return self.profile.get("online_profiles", {}).get("portfolio", "")
        if 'city' in q or 'location' in q:
            loc = self.profile.get("location", {})
            city = loc.get("city", "")
            state = loc.get("state", "")
            country = loc.get("country", "")
            # Return full location: City, State, Country
            full_loc = f"{city}, {state}, {country}".replace(", , ", ", ").strip(", ")
            return full_loc if full_loc else city
        if any(x in q for x in ['zip', 'postal']):
            return self.profile.get("location", {}).get("zip_code", "")
        
        return ""
    
    def _get_number_answer(self, question: str) -> Optional[int]:
        """Get answer for a number question - NUMBERS ONLY"""
        q = question.lower()
        
        # "How many" questions - return number
        if 'how many' in q:
            return self._get_experience_years(q)
        
        # Salary/CTC questions - check for LPA format
        if any(x in q for x in ['current ctc', 'current salary', 'present ctc', 'present salary', 'current compensation', 'last drawn']):
            if any(x in q for x in ['lpa', 'lakhs', 'lakh']):
                return 2.8
            return 280000
        if any(x in q for x in ['expected ctc', 'expected salary', 'desired salary', 'desired ctc', 'expected compensation']):
            if any(x in q for x in ['lpa', 'lakhs', 'lakh']):
                return 4
            return 400000
        
        # Generic salary with LPA check
        if any(x in q for x in ['salary', 'ctc', 'compensation', 'package']):
            if any(x in q for x in ['lpa', 'lakhs', 'lakh']):
                if any(x in q for x in ['current', 'present', 'last']):
                    return 2.8
                return 4
            return 280000
        
        # Notice period - just number
        if 'notice' in q:
            return 10
        
        # Years of experience - return 1
        if any(x in q for x in ['experience', 'years', 'year']):
            return 1
        
        # Age
        if 'age' in q:
            return 22
        
        # GPA
        if 'gpa' in q or 'grade' in q:
            gpa_str = self.profile.get("education", [{}])[0].get("gpa", "3.0")
            try:
                return int(float(gpa_str.split("/")[0]))
            except:
                return 3
        
        # Default: return 1 for any number field (safer than 0)
        return 1
    
    def _get_experience_years(self, question: str) -> int:
        """Calculate years of experience for a specific technology/skill
        ALWAYS returns at least 1 - we have experience in everything we claim
        """
        q = question.lower()
        
        # All technologies we have experience with - return 1 for all
        known_techs = [
            # Languages
            'python', 'javascript', 'typescript', 'java', 'js', 'ts',
            # Frontend
            'react', 'reactjs', 'next', 'nextjs', 'next.js', 'angular', 'vue',
            'frontend', 'front-end', 'front end', 'html', 'css', 'sass', 'tailwind',
            # Backend
            'node', 'nodejs', 'node.js', 'nestjs', 'nest', 'express', 'fastapi',
            'django', 'flask', 'spring', 'backend', 'back-end', 'back end',
            # Databases
            'sql', 'mongodb', 'mongo', 'postgresql', 'postgres', 'mysql',
            'database', 'redis', 'firebase', 'supabase', 'dynamodb',
            # Cloud & DevOps
            'aws', 'amazon', 'docker', 'kubernetes', 'k8s', 'ci/cd', 'cicd',
            'jenkins', 'terraform', 'azure', 'gcp', 'cloud',
            # APIs
            'rest', 'restful', 'api', 'graphql', 'grpc', 'microservices',
            # Other
            'git', 'agile', 'scrum', 'jira', 'n8n', 'automation',
            'prompt', 'ai', 'machine learning', 'ml', 'llm',
            # Full stack
            'full stack', 'fullstack', 'full-stack', 'mern', 'mean',
            'web', 'software', 'development', 'programming', 'coding',
            'engineer', 'developer',
        ]
        
        # Check if asking about total/overall experience
        total_patterns = [
            'total', 'overall', 'professional', 'work experience', 'industry', 'relevant',
            'scalable', 'development', 'production', 'enterprise', 'commercial',
            'paid', 'full-time', 'full time', 'working', 'hands-on', 'hands on',
            'practical', 'real-world', 'real world', 'corporate', 'company'
        ]
        if any(p in q for p in total_patterns):
            return 1  # Total experience = 1 year
        
        # Check if any known tech is mentioned - return 1
        for tech in known_techs:
            if tech in q:
                return 1  # We have 1 year experience in everything
        
        # Default: return 1 for any experience question
        return 1
    
    def _get_dropdown_answer(self, question: str, options: List[str]) -> str:
        """Get best option for a dropdown"""
        q = question.lower()
        options_lower = [o.lower() for o in options]
        
        # Yes/No dropdowns
        for pattern in self.yes_questions:
            if pattern in q:
                for i, opt in enumerate(options_lower):
                    if 'yes' in opt:
                        return options[i]
        
        for pattern in self.no_questions:
            if pattern in q:
                for i, opt in enumerate(options_lower):
                    if 'no' in opt:
                        return options[i]
        
        # Experience level
        if 'experience' in q and 'level' in q:
            preferred = ['entry', 'junior', 'mid', 'associate', '1-2', '0-2', '1-3']
            for pref in preferred:
                for i, opt in enumerate(options_lower):
                    if pref in opt:
                        return options[i]
        
        # Education level
        if 'education' in q or 'degree' in q:
            preferred = ["bachelor", "master", "b.tech", "b.s.", "bs", "undergraduate"]
            for pref in preferred:
                for i, opt in enumerate(options_lower):
                    if pref in opt:
                        return options[i]
        
        # Country
        if 'country' in q:
            for i, opt in enumerate(options_lower):
                if 'india' in opt or 'united states' in opt:
                    return options[i]
        
        # Remote preference
        if 'remote' in q or 'work location' in q or 'hybrid' in q:
            preferred = ['remote', 'yes', 'hybrid', 'flexible']
            for pref in preferred:
                for i, opt in enumerate(options_lower):
                    if pref in opt:
                        return options[i]
        
        # Gender - ALWAYS select Male
        if 'gender' in q:
            # First try to find exact "male" (not female)
            for i, opt in enumerate(options_lower):
                opt_clean = opt.strip()
                # Check for exact 'male' or 'man' - but NOT 'female' or 'woman'
                if opt_clean == 'male' or opt_clean == 'man':
                    return options[i]
                if ('male' in opt_clean or 'man' in opt_clean) and 'female' not in opt_clean and 'woman' not in opt_clean:
                    return options[i]
            # Fallback to prefer not to say
            for i, opt in enumerate(options_lower):
                if 'prefer not' in opt or 'decline' in opt:
                    return options[i]
        
        # EEO questions - prefer not to say
        if any(x in q for x in ['race', 'ethnicity', 'veteran', 'disability']):
            for i, opt in enumerate(options_lower):
                if 'prefer not' in opt or 'decline' in opt or 'not' in opt:
                    return options[i]
        
        # Use AI if available
        if self.ai_filler:
            try:
                answer = self.ai_filler.get_answer(question, 'dropdown', options)
                if answer:
                    return answer
            except:
                pass
        
        # Default: first non-placeholder option
        for i, opt in enumerate(options_lower):
            if opt and 'select' not in opt and 'choose' not in opt:
                return options[i]
        
        return options[1] if len(options) > 1 else options[0]
    
    def _get_radio_answer(self, question: str, options: List[str]) -> str:
        """Get best answer for radio buttons"""
        q = question.lower()
        options_lower = [o.lower() for o in options]
        
        # Yes/No questions
        for pattern in self.yes_questions:
            if pattern in q:
                for i, opt in enumerate(options_lower):
                    if 'yes' in opt:
                        return options[i]
        
        for pattern in self.no_questions:
            if pattern in q:
                for i, opt in enumerate(options_lower):
                    if 'no' in opt:
                        return options[i]
        
        # Default to first option or "Yes" if available
        for i, opt in enumerate(options_lower):
            if 'yes' in opt:
                return options[i]
        
        return options[0] if options else "Yes"
    
    def _safe_fill(self, elem: WebElement, value: str):
        """Safely fill a form field"""
        try:
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            time.sleep(0.1)
            
            # Click to focus
            try:
                elem.click()
            except:
                self.driver.execute_script("arguments[0].click();", elem)
            
            time.sleep(0.1)
            
            # Clear and fill
            elem.clear()
            elem.send_keys(str(value))
            
        except Exception as e:
            # Try JS as fallback
            try:
                self.driver.execute_script(f"arguments[0].value = '{value}';", elem)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", elem)
            except:
                pass
