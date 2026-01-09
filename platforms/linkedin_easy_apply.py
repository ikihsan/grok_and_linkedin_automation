"""
LinkedIn Easy Apply Handler
Applies to jobs via LinkedIn Easy Apply feature.
Uses job boards for discovery, applies directly via Easy Apply.
"""

import time
import random
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from itertools import product

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import USER_PROFILE, RATE_LIMITS, check_job_match, JOB_CRITERIA
from form_filler import form_filler
from application_logger import app_logger


class LinkedInEasyApply:
    """
    LinkedIn Easy Apply automation.
    Discovers jobs on LinkedIn and applies via Easy Apply.
    """
    
    def __init__(self, browser):
        self.browser = browser
        self.driver = browser.driver
        
        # Credentials
        creds = USER_PROFILE["platform_credentials"]["linkedin"]
        self.email = creds["email"]
        self.password = os.getenv("LINKEDIN_PASSWORD", "")
        
        # Job preferences
        self.positions = USER_PROFILE["job_preferences"]["desired_titles"][:5]  # Top 5
        self.locations = ["India", "Remote", "Bangalore", "Mumbai"]
        
        # Blacklists
        self.company_blacklist = [c.lower() for c in USER_PROFILE["job_preferences"]["exclude_companies"]]
        self.title_blacklist = [t.lower() for t in JOB_CRITERIA["exclusions"]["titles"]]
        
        # State
        self.seen_jobs = set()
        self.is_logged_in = False
        
        # Statistics
        self.applied_count = 0
        self.skipped_count = 0
        self.failed_count = 0
    
    def login(self) -> bool:
        """Login to LinkedIn"""
        try:
            print("🔑 Logging into LinkedIn...")
            self.browser.goto("https://www.linkedin.com/login")
            time.sleep(random.uniform(2, 4))
            
            # Enter email
            email_field = self.driver.find_element(By.ID, "username")
            email_field.clear()
            self.browser.human_type(email_field, self.email)
            time.sleep(random.uniform(0.3, 0.7))
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            self.browser.human_type(password_field, self.password)
            time.sleep(random.uniform(0.3, 0.7))
            
            # Click login
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            self.browser.human_click(login_btn)
            
            time.sleep(random.uniform(4, 6))
            
            # Check for security verification
            self._handle_security_check()
            
            # Verify login success
            if self._verify_logged_in():
                self.is_logged_in = True
                print("✅ LinkedIn login successful!")
                return True
            
            print("❌ LinkedIn login failed!")
            return False
            
        except Exception as e:
            print(f"❌ LinkedIn login error: {e}")
            return False
    
    def _verify_logged_in(self) -> bool:
        """Verify if logged in"""
        indicators = [
            'input[aria-label*="Search"]',
            '.global-nav__me',
            '.feed-identity-module',
            'nav.global-nav',
        ]
        
        for selector in indicators:
            if self.browser.is_visible(By.CSS_SELECTOR, selector, timeout=3):
                return True
        return False
    
    def _handle_security_check(self):
        """Handle security verification if needed"""
        page_source = self.driver.page_source.lower()
        current_url = self.driver.current_url.lower()
        
        if 'checkpoint' in current_url or 'verify' in page_source or 'security' in page_source:
            print("\n⚠️  SECURITY CHECK DETECTED!")
            print("Please complete verification in the browser...")
            input("Press ENTER when done...")
            time.sleep(3)
    
    def start_applying(self):
        """Main method to start job application process"""
        if not self.is_logged_in:
            if not self.login():
                return
        
        # Create position/location combinations
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        
        print(f"\n🎯 Starting job search with {len(searches)} combinations...")
        
        for position, location in searches:
            # Check daily limit
            if app_logger.get_today_count() >= RATE_LIMITS["applications_per_day"]:
                print(f"📊 Daily limit reached ({RATE_LIMITS['applications_per_day']}). Stopping.")
                break
            
            print(f"\n🔍 Searching: {position} in {location}")
            
            try:
                self._search_and_apply(position, location)
            except Exception as e:
                print(f"⚠️ Search error: {str(e)[:50]}")
            
            # Wait between searches
            time.sleep(random.uniform(5, 15))
        
        self._print_statistics()
    
    def _search_and_apply(self, position: str, location: str, max_pages: int = 3):
        """Search for jobs and apply"""
        # Build search URL
        search_url = self._build_search_url(position, location)
        self.browser.goto(search_url)
        time.sleep(random.uniform(3, 5))
        
        for page in range(max_pages):
            print(f"📄 Page {page + 1}")
            
            # Get job listings
            jobs = self._get_job_listings()
            
            if not jobs:
                print("   No jobs found on this page")
                break
            
            print(f"   Found {len(jobs)} jobs")
            
            # Process each job
            for job in jobs:
                self._process_job(job)
                time.sleep(random.uniform(2, 5))
            
            # Go to next page
            if not self._goto_next_page():
                break
            
            time.sleep(random.uniform(3, 6))
    
    def _build_search_url(self, position: str, location: str) -> str:
        """Build LinkedIn job search URL"""
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = [
            f"keywords={position.replace(' ', '%20')}",
            f"location={location.replace(' ', '%20')}",
            "f_AL=true",  # Easy Apply filter
            "f_TPR=r604800",  # Past week
            "f_E=2",  # Entry level
            "f_WT=2",  # Remote filter
        ]
        return base_url + "&".join(params)
    
    def _get_job_listings(self) -> List:
        """Get job listings from current page"""
        # Multiple possible selectors
        selectors = [
            ".jobs-search-results__list-item",
            ".scaffold-layout__list-item",
            "[data-occludable-job-id]",
            "li.ember-view.occludable-update",
        ]
        
        for selector in selectors:
            try:
                jobs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if jobs:
                    return jobs
            except:
                continue
        
        return []
    
    def _process_job(self, job_element):
        """Process a single job listing"""
        try:
            # Extract job info
            job_info = self._extract_job_info(job_element)
            
            if not job_info:
                return
            
            title, company, link = job_info
            
            # Check if already applied
            if app_logger.has_applied(link):
                print(f"   ⏭️ Already applied: {title}")
                self.skipped_count += 1
                return
            
            # Check blacklists
            if self._is_blacklisted(title, company):
                print(f"   ⏭️ Blacklisted: {title} at {company}")
                self.skipped_count += 1
                return
            
            # Check job match
            score, should_apply, reason = check_job_match(title)
            if not should_apply:
                print(f"   ⏭️ No match: {title} ({reason})")
                self.skipped_count += 1
                return
            
            # Click on job
            self._click_job(job_element)
            time.sleep(random.uniform(2, 3))
            
            # Apply to job
            success = self._apply_to_job()
            
            if success:
                print(f"   ✅ Applied: {title} at {company}")
                self.applied_count += 1
                
                # Log application
                app_logger.log_application(
                    company=company,
                    role=title,
                    url=link,
                    platform="linkedin",
                    resume_used="default",
                    status="submitted"
                )
            else:
                print(f"   ⏭️ Could not apply: {title}")
                self.skipped_count += 1
            
            self.seen_jobs.add(link)
            
        except Exception as e:
            print(f"   ❌ Error processing job: {str(e)[:50]}")
            self.failed_count += 1
    
    def _extract_job_info(self, job_element) -> Optional[Tuple[str, str, str]]:
        """Extract title, company, and link from job element"""
        title, company, link = "", "", ""
        
        # Title selectors
        title_selectors = [
            '.job-card-list__title',
            '.job-card-container__link',
            'a[href*="/jobs/view/"]',
        ]
        
        for sel in title_selectors:
            try:
                elem = job_element.find_element(By.CSS_SELECTOR, sel)
                title = elem.text.strip()
                link = elem.get_attribute('href') or ""
                if title:
                    break
            except:
                continue
        
        # Company selectors
        company_selectors = [
            '.job-card-container__primary-description',
            '.job-card-container__company-name',
            '.artdeco-entity-lockup__subtitle',
        ]
        
        for sel in company_selectors:
            try:
                company = job_element.find_element(By.CSS_SELECTOR, sel).text.strip()
                if company:
                    break
            except:
                continue
        
        if title and link:
            return (title, company, link.split('?')[0])
        return None
    
    def _is_blacklisted(self, title: str, company: str) -> bool:
        """Check if job is blacklisted"""
        title_lower = title.lower()
        company_lower = company.lower()
        
        for blacklisted in self.title_blacklist:
            if blacklisted in title_lower:
                return True
        
        for blacklisted in self.company_blacklist:
            if blacklisted in company_lower:
                return True
        
        return False
    
    def _click_job(self, job_element):
        """Click on job listing to view details"""
        click_selectors = [
            '.job-card-list__title',
            '.job-card-container__link',
            'a[href*="/jobs/view/"]',
        ]
        
        for sel in click_selectors:
            try:
                elem = job_element.find_element(By.CSS_SELECTOR, sel)
                self.browser.human_click(elem)
                return
            except:
                continue
        
        # Fallback: click job element itself
        try:
            self.browser.human_click(job_element)
        except:
            pass
    
    def _apply_to_job(self) -> bool:
        """Apply to the currently selected job"""
        # Find Easy Apply button
        easy_apply_btn = self._find_easy_apply_button()
        
        if not easy_apply_btn:
            return False
        
        # Click Easy Apply
        self.browser.human_click(easy_apply_btn)
        time.sleep(random.uniform(2, 3))
        
        # Fill application form
        max_retries = 3
        
        while max_retries > 0:
            try:
                # Fill all form fields
                self._fill_form_page()
                
                # Find next/submit button
                button = self._find_next_button()
                
                if not button:
                    break
                
                button_text = button.text.lower()
                
                # Check if submit
                if 'submit' in button_text:
                    # Unfollow company option
                    self._unfollow_company()
                    
                    button.click()
                    time.sleep(random.uniform(2, 3))
                    
                    # Close success modal
                    self._close_modals()
                    return True
                
                # Click next
                button.click()
                time.sleep(random.uniform(1.5, 2.5))
                
                # Check for errors
                if self._has_form_errors():
                    max_retries -= 1
                    print(f"      ⚠️ Form errors, retrying... ({max_retries} left)")
                    self._fill_form_page()  # Try filling again
                else:
                    max_retries = 3  # Reset retries on success
                    
            except Exception as e:
                max_retries -= 1
                print(f"      ⚠️ Form error: {str(e)[:30]}")
        
        # Failed - close modal
        self._close_modals()
        return False
    
    def _find_easy_apply_button(self):
        """Find Easy Apply button"""
        selectors = [
            'button.jobs-apply-button',
            'button[aria-label*="Easy Apply"]',
            '.jobs-apply-button--top-card',
        ]
        
        for sel in selectors:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed() and 'easy apply' in btn.text.lower():
                    return btn
            except:
                continue
        
        return None
    
    def _find_next_button(self):
        """Find next/submit button"""
        selectors = [
            '.artdeco-button--primary',
            'button[aria-label*="Continue"]',
            'button[aria-label*="Submit"]',
            'button[aria-label*="Review"]',
        ]
        
        for sel in selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for btn in buttons:
                    if btn.is_displayed():
                        return btn
            except:
                continue
        
        return None
    
    def _fill_form_page(self):
        """Fill all form fields on current page"""
        time.sleep(0.5)
        
        # ===== TEXT INPUTS =====
        self._fill_text_inputs()
        
        # ===== DROPDOWNS =====
        self._fill_dropdowns()
        
        # ===== RADIO BUTTONS =====
        self._fill_radio_buttons()
        
        # ===== CHECKBOXES =====
        self._fill_checkboxes()
        
        # ===== FILE UPLOADS =====
        self._handle_file_uploads()
    
    def _fill_text_inputs(self):
        """Fill all text inputs"""
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                '.jobs-easy-apply-content input[type="text"], '
                '.jobs-easy-apply-content input[type="number"], '
                '.jobs-easy-apply-content input:not([type="file"]):not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), '
                '.jobs-easy-apply-content textarea'
            )
            
            for inp in inputs:
                try:
                    if not inp.is_displayed():
                        continue
                    
                    # Skip if already has value
                    current_value = inp.get_attribute('value') or ''
                    if current_value.strip():
                        continue
                    
                    # Get question text
                    question = self._get_question_text(inp)
                    
                    # Get answer
                    answer = form_filler.get_text_answer(question)
                    
                    if answer:
                        inp.click()
                        time.sleep(0.1)
                        inp.clear()
                        inp.send_keys(str(answer))
                        print(f"      📝 Filled: {question[:40]}... → {answer}")
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _fill_dropdowns(self):
        """Fill all dropdowns"""
        try:
            selects = self.driver.find_elements(By.CSS_SELECTOR, '.jobs-easy-apply-content select')
            
            for select_elem in selects:
                try:
                    if not select_elem.is_displayed():
                        continue
                    
                    select = Select(select_elem)
                    current = select.first_selected_option.text.lower()
                    
                    # Skip if already selected
                    if current and 'select' not in current:
                        continue
                    
                    # Get question and options
                    question = self._get_question_text(select_elem)
                    options = [o.text for o in select.options if o.text.strip()]
                    
                    # Get answer
                    choice = form_filler.get_dropdown_answer(question, options)
                    
                    try:
                        select.select_by_visible_text(choice)
                        print(f"      📋 Selected: {question[:30]}... → {choice}")
                    except:
                        select.select_by_index(1 if len(options) > 1 else 0)
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _fill_radio_buttons(self):
        """Fill all radio buttons"""
        try:
            # Find fieldsets with radio buttons
            fieldsets = self.driver.find_elements(By.CSS_SELECTOR, 
                '.jobs-easy-apply-content fieldset, '
                '.jobs-easy-apply-content [data-test-form-element]'
            )
            
            for fieldset in fieldsets:
                try:
                    radios = fieldset.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                    
                    if not radios:
                        continue
                    
                    # Skip if already selected
                    if any(r.is_selected() for r in radios):
                        continue
                    
                    # Get question and labels
                    question = fieldset.text.lower()
                    labels = fieldset.find_elements(By.TAG_NAME, 'label')
                    label_texts = [l.text.lower() for l in labels]
                    
                    # Get answer
                    answer = form_filler.get_radio_answer(question, label_texts)
                    
                    # Click matching label
                    for label in labels:
                        if answer in label.text.lower():
                            label.click()
                            print(f"      🔘 Radio: {question[:30]}... → {label.text}")
                            break
                            
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _fill_checkboxes(self):
        """Fill checkboxes"""
        try:
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 
                '.jobs-easy-apply-content input[type="checkbox"]'
            )
            
            for cb in checkboxes:
                try:
                    if not cb.is_displayed() or cb.is_selected():
                        continue
                    
                    question = self._get_question_text(cb)
                    
                    if form_filler.should_check_checkbox(question):
                        cb.click()
                        print(f"      ☑️ Checked: {question[:40]}...")
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _handle_file_uploads(self):
        """Handle resume/cover letter uploads"""
        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                '.jobs-easy-apply-content input[type="file"]'
            )
            
            for inp in file_inputs:
                try:
                    # Check if resume upload
                    parent_text = self._get_question_text(inp).lower()
                    
                    if 'resume' in parent_text or 'cv' in parent_text:
                        resume_path = form_filler.select_resume("", "")
                        if os.path.exists(resume_path):
                            inp.send_keys(os.path.abspath(resume_path))
                            print(f"      📎 Uploaded resume: {resume_path}")
                            
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _get_question_text(self, element, max_levels: int = 5) -> str:
        """Get question text from parent elements"""
        try:
            parent = element
            for _ in range(max_levels):
                parent = parent.find_element(By.XPATH, '..')
                text = parent.text.lower()
                if 10 < len(text) < 500:
                    return text
        except:
            pass
        return ""
    
    def _has_form_errors(self) -> bool:
        """Check if form has validation errors"""
        page_source = self.driver.page_source.lower()
        error_indicators = [
            'please enter a valid',
            'this field is required',
            'file is required',
            'invalid input',
        ]
        return any(err in page_source for err in error_indicators)
    
    def _unfollow_company(self):
        """Uncheck follow company option"""
        try:
            follow_checkbox = self.driver.find_element(By.CSS_SELECTOR, 
                'input[id*="follow-company"]'
            )
            if follow_checkbox.is_selected():
                follow_checkbox.click()
        except:
            pass
    
    def _close_modals(self):
        """Close any open modals"""
        try:
            # Close dismiss button
            dismiss = self.driver.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss')
            dismiss.click()
            time.sleep(0.5)
            
            # Confirm discard if prompted
            try:
                discard_btns = self.driver.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')
                if len(discard_btns) > 1:
                    discard_btns[1].click()
            except:
                pass
        except:
            pass
        
        # Close toast notifications
        try:
            toast = self.driver.find_element(By.CLASS_NAME, 'artdeco-toast-item__dismiss')
            toast.click()
        except:
            pass
    
    def _goto_next_page(self) -> bool:
        """Go to next page of results"""
        try:
            # Find next page button
            next_btn = self.driver.find_element(By.CSS_SELECTOR, 
                'button[aria-label="Page forward"], '
                'button[aria-label="Next"]'
            )
            
            if next_btn.is_enabled():
                next_btn.click()
                return True
        except:
            pass
        return False
    
    def _print_statistics(self):
        """Print application statistics"""
        print("\n" + "="*50)
        print("📊 LINKEDIN SESSION STATISTICS")
        print("="*50)
        print(f"✅ Applied: {self.applied_count}")
        print(f"⏭️ Skipped: {self.skipped_count}")
        print(f"❌ Failed: {self.failed_count}")
        print(f"📝 Today's Total: {app_logger.get_today_count()}")
        print("="*50 + "\n")
