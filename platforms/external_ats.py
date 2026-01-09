"""
External ATS Handler
Handles applications on external ATS platforms:
- Greenhouse
- Lever
- Ashby
- Workday
- Company career pages

These are reached via job board redirects.
"""

import time
import random
import os
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import USER_PROFILE, RATE_LIMITS
from form_filler import form_filler
from application_logger import app_logger


class ExternalATSHandler:
    """
    Handles job applications on external ATS platforms.
    Detects ATS type and applies appropriate filling strategy.
    """
    
    def __init__(self, browser):
        self.browser = browser
        self.driver = browser.driver
        
        # ATS URL patterns
        self.ats_patterns = {
            'greenhouse': ['greenhouse.io', 'boards.greenhouse'],
            'lever': ['lever.co', 'jobs.lever'],
            'ashby': ['ashbyhq.com', 'jobs.ashby'],
            'workday': ['myworkday', 'workday.com'],
            'icims': ['icims.com'],
            'taleo': ['taleo.net'],
            'bamboohr': ['bamboohr.com'],
        }
    
    def detect_ats(self, url: str) -> Optional[str]:
        """Detect which ATS platform the URL belongs to"""
        url_lower = url.lower()
        
        for ats_name, patterns in self.ats_patterns.items():
            for pattern in patterns:
                if pattern in url_lower:
                    return ats_name
        
        return None
    
    def apply(self, url: str, job_title: str = "", company: str = "") -> bool:
        """
        Apply to a job on external ATS.
        Returns True if application submitted successfully.
        """
        # Check if already applied
        if app_logger.has_applied(url):
            print(f"   ⏭️ Already applied to this job")
            return False
        
        # Navigate to application page
        self.browser.goto(url)
        time.sleep(random.uniform(3, 5))
        
        # Detect ATS type
        ats_type = self.detect_ats(self.driver.current_url)
        
        if ats_type:
            print(f"   🔍 Detected ATS: {ats_type.upper()}")
        
        # Apply based on ATS type
        try:
            if ats_type == 'greenhouse':
                success = self._apply_greenhouse()
            elif ats_type == 'lever':
                success = self._apply_lever()
            elif ats_type == 'ashby':
                success = self._apply_ashby()
            elif ats_type == 'workday':
                success = self._apply_workday()
            else:
                # Generic application handler
                success = self._apply_generic()
            
            if success:
                app_logger.log_application(
                    company=company,
                    role=job_title,
                    url=url,
                    platform=ats_type or "external",
                    resume_used="default",
                    status="submitted"
                )
                return True
            
            return False
            
        except Exception as e:
            print(f"   ❌ ATS application error: {str(e)[:50]}")
            return False
    
    # =========================================================================
    # GREENHOUSE
    # =========================================================================
    
    def _apply_greenhouse(self) -> bool:
        """Apply on Greenhouse ATS"""
        print("   📝 Filling Greenhouse application...")
        
        try:
            # Fill basic info
            self._fill_greenhouse_basic()
            
            # Upload resume
            self._upload_greenhouse_resume()
            
            # Fill additional fields
            self._fill_greenhouse_additional()
            
            # Submit
            return self._submit_greenhouse()
            
        except Exception as e:
            print(f"   ❌ Greenhouse error: {e}")
            return False
    
    def _fill_greenhouse_basic(self):
        """Fill basic fields on Greenhouse"""
        field_mappings = {
            '#first_name': USER_PROFILE["personal"]["first_name"],
            '#last_name': USER_PROFILE["personal"]["last_name"],
            '#email': USER_PROFILE["personal"]["email"],
            '#phone': USER_PROFILE["personal"]["phone"],
            'input[name*="first_name"]': USER_PROFILE["personal"]["first_name"],
            'input[name*="last_name"]': USER_PROFILE["personal"]["last_name"],
            'input[name*="email"]': USER_PROFILE["personal"]["email"],
            'input[name*="phone"]': USER_PROFILE["personal"]["phone"],
        }
        
        for selector, value in field_mappings.items():
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                if elem.is_displayed() and not elem.get_attribute('value'):
                    elem.clear()
                    elem.send_keys(value)
            except:
                continue
    
    def _upload_greenhouse_resume(self):
        """Upload resume to Greenhouse"""
        try:
            file_input = self.driver.find_element(By.CSS_SELECTOR, 
                'input[type="file"][name*="resume"], input[type="file"]'
            )
            
            resume_path = USER_PROFILE["resumes"]["default"]
            if os.path.exists(resume_path):
                file_input.send_keys(os.path.abspath(resume_path))
                print("   📎 Resume uploaded")
        except:
            pass
    
    def _fill_greenhouse_additional(self):
        """Fill additional questions on Greenhouse"""
        # Fill all text inputs
        inputs = self.driver.find_elements(By.CSS_SELECTOR, 
            'input[type="text"], input[type="number"], textarea'
        )
        
        for inp in inputs:
            try:
                if not inp.is_displayed() or inp.get_attribute('value'):
                    continue
                
                label = self._find_label_for_element(inp)
                answer = form_filler.get_text_answer(label)
                
                if answer:
                    inp.clear()
                    inp.send_keys(str(answer))
            except:
                continue
        
        # Fill dropdowns
        selects = self.driver.find_elements(By.TAG_NAME, 'select')
        
        for select_elem in selects:
            try:
                if not select_elem.is_displayed():
                    continue
                
                select = Select(select_elem)
                label = self._find_label_for_element(select_elem)
                options = [o.text for o in select.options]
                
                choice = form_filler.get_dropdown_answer(label, options)
                select.select_by_visible_text(choice)
            except:
                continue
    
    def _submit_greenhouse(self) -> bool:
        """Submit Greenhouse application"""
        try:
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, 
                'input[type="submit"], button[type="submit"], #submit_app'
            )
            
            if submit_btn.is_displayed():
                submit_btn.click()
                time.sleep(3)
                
                # Check for success
                page_source = self.driver.page_source.lower()
                if 'thank you' in page_source or 'application received' in page_source:
                    print("   ✅ Greenhouse application submitted!")
                    return True
        except:
            pass
        
        return False
    
    # =========================================================================
    # LEVER
    # =========================================================================
    
    def _apply_lever(self) -> bool:
        """Apply on Lever ATS"""
        print("   📝 Filling Lever application...")
        
        try:
            # Find apply button if on job listing
            try:
                apply_btn = self.driver.find_element(By.CSS_SELECTOR, 
                    'a.postings-btn, a[href*="apply"]'
                )
                apply_btn.click()
                time.sleep(2)
            except:
                pass
            
            # Fill application form
            self._fill_lever_form()
            
            # Upload resume
            self._upload_lever_resume()
            
            # Submit
            return self._submit_lever()
            
        except Exception as e:
            print(f"   ❌ Lever error: {e}")
            return False
    
    def _fill_lever_form(self):
        """Fill Lever application form"""
        field_mappings = {
            'input[name="name"]': USER_PROFILE["personal"]["full_name"],
            'input[name="email"]': USER_PROFILE["personal"]["email"],
            'input[name="phone"]': USER_PROFILE["personal"]["phone"],
            'input[name="org"]': USER_PROFILE["work_experience"][0]["company"] if USER_PROFILE["work_experience"] else "",
            'input[name*="linkedin"]': USER_PROFILE["online_profiles"]["linkedin"],
            'input[name*="github"]': USER_PROFILE["online_profiles"]["github"],
            'input[name*="portfolio"]': USER_PROFILE["online_profiles"].get("portfolio", ""),
        }
        
        for selector, value in field_mappings.items():
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                if elem.is_displayed() and not elem.get_attribute('value'):
                    elem.clear()
                    elem.send_keys(value)
            except:
                continue
        
        # Fill additional questions
        self._fill_additional_fields()
    
    def _upload_lever_resume(self):
        """Upload resume to Lever"""
        try:
            file_input = self.driver.find_element(By.CSS_SELECTOR, 
                'input[type="file"][name="resume"], input.resume-upload'
            )
            
            resume_path = USER_PROFILE["resumes"]["default"]
            if os.path.exists(resume_path):
                file_input.send_keys(os.path.abspath(resume_path))
        except:
            pass
    
    def _submit_lever(self) -> bool:
        """Submit Lever application"""
        try:
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, 
                'button[type="submit"], .application-submit'
            )
            
            submit_btn.click()
            time.sleep(3)
            
            page_source = self.driver.page_source.lower()
            if 'thank you' in page_source or 'application submitted' in page_source:
                print("   ✅ Lever application submitted!")
                return True
        except:
            pass
        
        return False
    
    # =========================================================================
    # ASHBY
    # =========================================================================
    
    def _apply_ashby(self) -> bool:
        """Apply on Ashby ATS"""
        print("   📝 Filling Ashby application...")
        
        try:
            # Fill form
            self._fill_additional_fields()
            
            # Upload resume
            try:
                file_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
                resume_path = USER_PROFILE["resumes"]["default"]
                if os.path.exists(resume_path):
                    file_input.send_keys(os.path.abspath(resume_path))
            except:
                pass
            
            # Submit
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, 
                    'button[type="submit"]'
                )
                submit_btn.click()
                time.sleep(3)
                
                if 'thank you' in self.driver.page_source.lower():
                    print("   ✅ Ashby application submitted!")
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"   ❌ Ashby error: {e}")
            return False
    
    # =========================================================================
    # WORKDAY
    # =========================================================================
    
    def _apply_workday(self) -> bool:
        """Apply on Workday ATS"""
        print("   📝 Filling Workday application...")
        
        # Workday is complex with multiple steps
        # This is a simplified handler
        
        try:
            # Fill form fields
            self._fill_additional_fields()
            
            # Handle multi-step forms
            max_pages = 5
            
            for _ in range(max_pages):
                self._fill_additional_fields()
                
                # Look for next/submit button
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, 
                        'button[data-automation-id="bottom-navigation-next-button"]'
                    )
                    next_btn.click()
                    time.sleep(2)
                except:
                    # Try submit
                    try:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, 
                            'button[data-automation-id="submit"]'
                        )
                        submit_btn.click()
                        time.sleep(3)
                        
                        if 'thank you' in self.driver.page_source.lower():
                            print("   ✅ Workday application submitted!")
                            return True
                    except:
                        break
            
            return False
            
        except Exception as e:
            print(f"   ❌ Workday error: {e}")
            return False
    
    # =========================================================================
    # GENERIC HANDLER
    # =========================================================================
    
    def _apply_generic(self) -> bool:
        """Generic application handler for unknown ATS"""
        print("   📝 Using generic application handler...")
        
        try:
            # Fill all form fields
            self._fill_additional_fields()
            
            # Upload resume
            try:
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                for file_input in file_inputs:
                    try:
                        parent_text = self._get_parent_text(file_input).lower()
                        if 'resume' in parent_text or 'cv' in parent_text:
                            resume_path = USER_PROFILE["resumes"]["default"]
                            if os.path.exists(resume_path):
                                file_input.send_keys(os.path.abspath(resume_path))
                                break
                    except:
                        continue
            except:
                pass
            
            # Submit
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Submit")',
                'button:contains("Apply")',
                '#submit',
                '.submit-btn',
            ]
            
            for sel in submit_selectors:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(3)
                        
                        if 'thank you' in self.driver.page_source.lower():
                            print("   ✅ Application submitted!")
                            return True
                        break
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"   ❌ Generic handler error: {e}")
            return False
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _fill_additional_fields(self):
        """Fill all additional form fields"""
        # Text inputs
        inputs = self.driver.find_elements(By.CSS_SELECTOR, 
            'input[type="text"], input[type="email"], input[type="tel"], '
            'input[type="number"], textarea'
        )
        
        for inp in inputs:
            try:
                if not inp.is_displayed() or inp.get_attribute('value'):
                    continue
                
                label = self._find_label_for_element(inp)
                answer = form_filler.get_text_answer(label)
                
                if answer:
                    inp.clear()
                    inp.send_keys(str(answer))
            except:
                continue
        
        # Dropdowns
        selects = self.driver.find_elements(By.TAG_NAME, 'select')
        
        for select_elem in selects:
            try:
                if not select_elem.is_displayed():
                    continue
                
                select = Select(select_elem)
                
                # Skip if already selected
                current = select.first_selected_option.text.lower()
                if current and 'select' not in current:
                    continue
                
                label = self._find_label_for_element(select_elem)
                options = [o.text for o in select.options]
                
                choice = form_filler.get_dropdown_answer(label, options)
                
                try:
                    select.select_by_visible_text(choice)
                except:
                    select.select_by_index(1 if len(options) > 1 else 0)
            except:
                continue
        
        # Radio buttons
        try:
            radio_groups = {}
            radios = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            
            for radio in radios:
                name = radio.get_attribute('name')
                if name and name not in radio_groups:
                    radio_groups[name] = []
                if name:
                    radio_groups[name].append(radio)
            
            for name, group in radio_groups.items():
                if any(r.is_selected() for r in group):
                    continue
                
                # Click first radio as default
                for r in group:
                    if r.is_displayed():
                        try:
                            label = self.driver.find_element(By.CSS_SELECTOR, f'label[for="{r.get_attribute("id")}"]')
                            label.click()
                        except:
                            r.click()
                        break
        except:
            pass
        
        # Checkboxes (terms, consent, etc.)
        try:
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
            
            for cb in checkboxes:
                if not cb.is_displayed() or cb.is_selected():
                    continue
                
                label = self._find_label_for_element(cb)
                
                if form_filler.should_check_checkbox(label):
                    try:
                        cb.click()
                    except:
                        pass
        except:
            pass
    
    def _find_label_for_element(self, element) -> str:
        """Find label text for an element"""
        try:
            # Try explicit label
            elem_id = element.get_attribute('id')
            if elem_id:
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, f'label[for="{elem_id}"]')
                    return label.text.lower()
                except:
                    pass
            
            # Try placeholder
            placeholder = element.get_attribute('placeholder')
            if placeholder:
                return placeholder.lower()
            
            # Try aria-label
            aria = element.get_attribute('aria-label')
            if aria:
                return aria.lower()
            
            # Try parent text
            return self._get_parent_text(element).lower()
            
        except:
            return ""
    
    def _get_parent_text(self, element, max_levels: int = 4) -> str:
        """Get text from parent elements"""
        try:
            parent = element
            for _ in range(max_levels):
                parent = parent.find_element(By.XPATH, '..')
                text = parent.text
                if 10 < len(text) < 300:
                    return text
        except:
            pass
        return ""
