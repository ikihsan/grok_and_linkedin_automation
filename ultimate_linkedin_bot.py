"""
Ultimate LinkedIn Easy Apply Bot
Uses AI for intelligent form filling + robust automation.
Designed for 100% hands-off operation.
"""

import time
import random
import os
import traceback
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from itertools import product

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementClickInterceptedException, StaleElementReferenceException
)

from config import USER_PROFILE, RATE_LIMITS, check_job_match, JOB_CRITERIA
from ai_form_filler import AIFormFiller
from smart_form_filler import SmartFormFiller
from application_logger import app_logger


class UltimateLinkedInBot:
    """
    The ultimate LinkedIn Easy Apply bot with AI-powered form filling.
    Designed for 100% autonomous operation.
    """
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.ai_filler = None
        self.smart_filler = None  # Smart form filler
        
        # Credentials - ALWAYS from environment variables
        self.email = os.getenv("LINKEDIN_EMAIL", "")
        self.password = os.getenv("LINKEDIN_PASSWORD", "")
        
        print(f"📧 Using email: {self.email}")
        print(f"🔑 Password: {'*' * len(self.password) if self.password else 'NOT SET'}")
        
        if not self.email or not self.password:
            print("❌ ERROR: LINKEDIN_EMAIL or LINKEDIN_PASSWORD not set in .env!")
        
        # Job search params - randomized on each start
        self.positions = USER_PROFILE["job_preferences"]["desired_titles"].copy()
        random.shuffle(self.positions)  # Randomize positions order each start
        # Search Kerala first, then rest of India
        self.locations = ["Kerala, India", "Kerala", "Kochi", "Kozhikode", "India", "Remote", "Bangalore", "Mumbai"]
        print(f"🎲 Randomized search order. Starting with: {self.positions[0]}")
        
        # Blacklists
        self.company_blacklist = [c.lower() for c in USER_PROFILE["job_preferences"]["exclude_companies"]]
        self.title_blacklist = [t.lower() for t in JOB_CRITERIA["exclusions"]["titles"]]
        
        # State
        self.seen_jobs = set()
        self.is_logged_in = False
        
        # Stats
        self.applied_count = 0
        self.skipped_count = 0
        self.failed_count = 0
    
    def start_browser(self) -> bool:
        """Start Chrome browser with anti-detection"""
        try:
            options = Options()
            
            # Anti-detection settings
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            
            # GPU fixes for Windows
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-software-rasterizer")
            
            # User agent
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Find Chrome
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\Application\chrome.exe",
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    options.binary_location = path
                    break
            
            self.driver = webdriver.Chrome(options=options)
            
            # Remove webdriver flag
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        window.navigator.chrome = {runtime: {}};
                    """
                }
            )
            
            self.wait = WebDriverWait(self.driver, 10)
            
            # Initialize AI form filler
            self.ai_filler = AIFormFiller(USER_PROFILE)
            
            # Initialize Smart form filler
            self.smart_filler = SmartFormFiller(self.driver, USER_PROFILE, self.ai_filler)
            
            print("✅ Browser started successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Browser start error: {e}")
            return False
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def login(self) -> bool:
        """Login to LinkedIn"""
        try:
            print("🔑 Logging into LinkedIn...")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(random.uniform(2, 4))
            
            # Enter email
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            self._human_type(email_field, self.email)
            
            time.sleep(random.uniform(0.3, 0.7))
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            self._human_type(password_field, self.password)
            
            time.sleep(random.uniform(0.3, 0.7))
            
            # Click login
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            
            time.sleep(random.uniform(4, 6))
            
            # Handle security check
            self._handle_security_check()
            
            # Verify login
            if self._is_logged_in():
                self.is_logged_in = True
                print("✅ LinkedIn login successful!")
                return True
            
            print("❌ LinkedIn login failed!")
            return False
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def _human_type(self, element, text: str):
        """Type like a human"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.02, 0.08))
    
    def _is_logged_in(self) -> bool:
        """Check if logged in"""
        indicators = [
            'input[aria-label*="Search"]',
            '.global-nav__me',
            '.feed-identity-module',
        ]
        
        for sel in indicators:
            try:
                if self.driver.find_elements(By.CSS_SELECTOR, sel):
                    return True
            except:
                pass
        return False
    
    def _handle_security_check(self):
        """Handle security verification"""
        time.sleep(2)
        page_source = self.driver.page_source.lower()
        current_url = self.driver.current_url.lower()
        
        if 'checkpoint' in current_url or 'verify' in page_source or 'security verification' in page_source:
            print("\n⚠️  SECURITY CHECK DETECTED!")
            print("Please complete the verification in the browser.")
            input("Press ENTER when done...")
            time.sleep(3)
    
    def run(self):
        """Main run loop"""
        if not self.start_browser():
            return
        
        if not self.login():
            self.close()
            return
        
        print(f"\n🚀 Starting job applications...")
        print(f"📊 Today's applications: {app_logger.get_today_count()}/{RATE_LIMITS['applications_per_day']}")
        
        try:
            # Create search combinations
            searches = list(product(self.positions, self.locations))
            random.shuffle(searches)
            
            for position, location in searches:
                # Check daily limit
                if app_logger.get_today_count() >= RATE_LIMITS['applications_per_day']:
                    print(f"\n📊 Daily limit reached!")
                    break
                
                print(f"\n🔍 Searching: {position} in {location}")
                
                try:
                    self._search_and_apply(position, location)
                except Exception as e:
                    print(f"⚠️ Search error: {str(e)[:50]}")
                    traceback.print_exc()
                
                # Wait between searches
                time.sleep(random.uniform(10, 30))
            
        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")
        
        finally:
            self._print_stats()
            self.close()
    
    def _search_and_apply(self, position: str, location: str):
        """Search for jobs and apply"""
        # Build URL with Easy Apply filter
        url = self._build_search_url(position, location)
        self.driver.get(url)
        time.sleep(random.uniform(3, 5))
        
        for page in range(3):  # Max 3 pages per search
            print(f"   📄 Page {page + 1}")
            
            # Get job listings
            jobs = self._get_job_listings()
            
            if not jobs:
                print("   No jobs found")
                break
            
            print(f"   Found {len(jobs)} jobs")
            
            # Process each job
            for job in jobs:
                try:
                    self._process_job(job)
                except Exception as e:
                    print(f"   ❌ Job error: {str(e)[:30]}")
                
                time.sleep(random.uniform(2, 5))
            
            # Next page
            if not self._goto_next_page():
                break
            
            time.sleep(random.uniform(3, 6))
    
    def _build_search_url(self, position: str, location: str) -> str:
        """Build LinkedIn job search URL"""
        base = "https://www.linkedin.com/jobs/search/?"
        params = [
            f"keywords={position.replace(' ', '%20')}",
            f"location={location.replace(' ', '%20')}",
            "f_AL=true",  # Easy Apply
            "f_TPR=r604800",  # Past week
            "sortBy=DD",  # Date posted
        ]
        return base + "&".join(params)
    
    def _get_job_listings(self) -> List:
        """Get job listings from current page"""
        time.sleep(2)
        
        # Scroll to load jobs
        try:
            job_list = self.driver.find_element(By.CSS_SELECTOR, ".jobs-search-results-list")
            for _ in range(3):
                self.driver.execute_script("arguments[0].scrollBy(0, 300);", job_list)
                time.sleep(0.5)
        except:
            pass
        
        # Find job cards
        selectors = [
            ".jobs-search-results__list-item",
            ".scaffold-layout__list-item",
            "[data-occludable-job-id]",
        ]
        
        for sel in selectors:
            try:
                jobs = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if jobs:
                    return jobs
            except:
                pass
        
        return []
    
    def _process_job(self, job_element):
        """Process a single job listing"""
        # Extract job info
        info = self._extract_job_info(job_element)
        if not info:
            print(f"      ⚠️ Could not extract job info")
            return
        
        title, company, link = info
        print(f"      👀 {title[:40]} at {company[:20]}")
        
        # Skip if already applied
        if app_logger.has_applied(link):
            print(f"         ⏭️ Already applied")
            return
        
        # Check blacklists
        if self._is_blacklisted(title, company):
            print(f"         ⏭️ Blacklisted")
            self.skipped_count += 1
            return
        
        # Check job match - be lenient, most Easy Apply jobs are relevant
        score, should_apply, reason = check_job_match(title)
        if not should_apply:
            print(f"         ⏭️ {reason}")
            self.skipped_count += 1
            return
        
        # Click on job
        self._click_job(job_element)
        time.sleep(random.uniform(2, 3))
        
        # Apply
        success = self._apply_to_job(title, company)
        
        if success:
            print(f"   ✅ Applied: {title} at {company}")
            self.applied_count += 1
            
            app_logger.log_application(
                company=company,
                role=title,
                url=link,
                platform="linkedin",
                status="submitted"
            )
        else:
            self.skipped_count += 1
        
        self.seen_jobs.add(link)
    
    def _extract_job_info(self, job_element) -> Optional[Tuple[str, str, str]]:
        """Extract job title, company, and link"""
        title, company, link = "", "", ""
        
        title_selectors = ['.job-card-list__title', 'a[href*="/jobs/view/"]']
        for sel in title_selectors:
            try:
                elem = job_element.find_element(By.CSS_SELECTOR, sel)
                title = elem.text.strip()
                link = elem.get_attribute('href') or ""
                if title:
                    break
            except:
                pass
        
        company_selectors = ['.job-card-container__primary-description', '.artdeco-entity-lockup__subtitle']
        for sel in company_selectors:
            try:
                company = job_element.find_element(By.CSS_SELECTOR, sel).text.strip()
                if company:
                    break
            except:
                pass
        
        if title and link:
            return (title, company, link.split('?')[0])
        return None
    
    def _is_blacklisted(self, title: str, company: str) -> bool:
        """Check if job is blacklisted"""
        title_lower = title.lower()
        company_lower = company.lower()
        
        for bl in self.title_blacklist:
            if bl in title_lower:
                return True
        
        for bl in self.company_blacklist:
            if bl in company_lower:
                return True
        
        return False
    
    def _click_job(self, job_element):
        """Click on job listing"""
        selectors = ['.job-card-list__title', 'a[href*="/jobs/view/"]']
        
        for sel in selectors:
            try:
                elem = job_element.find_element(By.CSS_SELECTOR, sel)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                time.sleep(0.3)
                elem.click()
                return
            except:
                pass
        
        # Fallback
        try:
            job_element.click()
        except:
            pass
    
    def _apply_to_job(self, title: str, company: str) -> bool:
        """Apply to the currently selected job"""
        # Find Easy Apply button
        easy_apply_btn = self._find_easy_apply_button()
        
        if not easy_apply_btn:
            print(f"         ⚠️ No Easy Apply button found")
            return False
        
        print(f"         🖱️ Clicking Easy Apply button...")
        
        # Click Easy Apply
        try:
            easy_apply_btn.click()
        except:
            self.driver.execute_script("arguments[0].click();", easy_apply_btn)
        
        time.sleep(random.uniform(2, 3))
        
        # Fill application form
        max_steps = 10
        
        for step in range(max_steps):
            try:
                print(f"      📋 Step {step + 1}...")
                
                # Fill current page
                self._fill_form_page()
                time.sleep(0.5)
                
                # Find next/submit button
                button = self._find_next_button()
                
                if not button:
                    print(f"         ⚠️ No next/submit button found")
                    break
                
                button_text = button.text.lower()
                print(f"         🔘 Button found: '{button_text}'")
                
                # Check if submit
                if 'submit' in button_text:
                    # Uncheck follow
                    self._uncheck_follow()
                    
                    print(f"         🚀 Submitting application...")
                    button.click()
                    time.sleep(random.uniform(2, 3))
                    
                    # Check success
                    if self._check_success():
                        self._close_modal()
                        return True
                    
                    print(f"         ❌ Submit failed - no success message")
                    self._close_modal()
                    return False
                
                # Check for review
                if 'review' in button_text:
                    print(f"         📝 Going to review...")
                    button.click()
                    time.sleep(1)
                    continue
                
                # Click next
                print(f"         ➡️ Going to next step...")
                button.click()
                time.sleep(random.uniform(1, 2))
                
                # Check for errors
                if self._has_form_errors():
                    print(f"         ⚠️ Form has errors, trying to fill again...")
                    # Try filling again
                    self._fill_form_page()
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"      ❌ Step error: {str(e)[:50]}")
                break
        
        # Failed - close modal
        print(f"         ❌ Application failed after {step + 1} steps")
        self._close_modal()
        return False
    
    def _find_easy_apply_button(self):
        """Find Easy Apply button"""
        selectors = [
            'button.jobs-apply-button',
            'button[aria-label*="Easy Apply"]',
            '.jobs-apply-button--top-card',
            'button[aria-label*="Apply"]',
            '.jobs-s-apply button',
        ]
        
        for sel in selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for btn in buttons:
                    if btn.is_displayed():
                        btn_text = btn.text.lower()
                        if 'easy apply' in btn_text or 'apply' in btn_text:
                            return btn
            except:
                pass
        
        # Fallback: find any button with "Easy Apply" text
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            for btn in buttons:
                if btn.is_displayed() and 'easy apply' in btn.text.lower():
                    return btn
        except:
            pass
        
        print(f"         ⚠️ No Easy Apply button found")
        return None
    
    def _find_next_button(self):
        """Find next/submit/review button"""
        selectors = [
            'button.artdeco-button--primary',
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
                pass
        
        return None
    
    def _fill_form_page(self):
        """Fill all form fields on current page using SmartFormFiller"""
        time.sleep(0.5)
        
        # Use the comprehensive SmartFormFiller
        try:
            self.smart_filler.fill_all_fields()
        except Exception as e:
            print(f"      ⚠️ Form fill error: {str(e)[:50]}")
            # Fallback to basic filling
            self._basic_fill_form()
    
    def _basic_fill_form(self):
        """Basic fallback form filling"""
        # Fill any empty required text fields with defaults
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR,
                '.jobs-easy-apply-content input[type="text"], '
                '.jobs-easy-apply-content input[type="number"]'
            )
            for inp in inputs:
                try:
                    if inp.is_displayed() and not inp.get_attribute('value'):
                        inp_type = inp.get_attribute('type')
                        if inp_type == 'number':
                            inp.send_keys("1")
                        else:
                            inp.send_keys("N/A")
                except:
                    pass
        except:
            pass
        
        # Check any unchecked checkboxes that might be required
        try:
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR,
                '.jobs-easy-apply-content input[type="checkbox"]')
            for cb in checkboxes:
                try:
                    if cb.is_displayed() and not cb.is_selected():
                        cb.click()
                except:
                    pass
        except:
            pass
    
    def _fill_text_inputs(self):
        """Fill text inputs using AI"""
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
                    
                    # Skip if has value
                    current = inp.get_attribute('value') or ''
                    if current.strip():
                        continue
                    
                    # Get question
                    question = self._get_question_text(inp)
                    
                    # Get input type
                    input_type = inp.get_attribute('type') or 'text'
                    field_type = 'number' if input_type == 'number' else 'text'
                    
                    # Get AI answer
                    answer = self.ai_filler.get_answer(question, field_type)
                    
                    if answer:
                        inp.click()
                        time.sleep(0.1)
                        inp.clear()
                        inp.send_keys(str(answer))
                        print(f"      📝 {question[:35]}... → {answer}")
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _fill_dropdowns(self):
        """Fill dropdowns using AI"""
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
                    
                    # Get AI answer
                    answer = self.ai_filler.get_answer(question, 'dropdown', options)
                    
                    try:
                        select.select_by_visible_text(answer)
                        print(f"      📋 {question[:35]}... → {answer}")
                    except:
                        if len(options) > 1:
                            select.select_by_index(1)
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _fill_radio_buttons(self):
        """Fill radio buttons using AI"""
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
                    
                    # Get question
                    question = fieldset.text.lower()
                    labels = fieldset.find_elements(By.TAG_NAME, 'label')
                    label_texts = [l.text for l in labels if l.text.strip()]
                    
                    # Get AI answer
                    answer = self.ai_filler.get_answer(question, 'radio', label_texts)
                    
                    # Click matching label
                    for label in labels:
                        if answer.lower() in label.text.lower():
                            label.click()
                            print(f"      🔘 {question[:35]}... → {label.text}")
                            break
                    else:
                        # Default: click first
                        if labels:
                            labels[0].click()
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _fill_checkboxes(self):
        """Fill checkboxes - especially consent/agreement checkboxes"""
        try:
            # Find all checkboxes with broader selectors
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR,
                '.jobs-easy-apply-content input[type="checkbox"], '
                '.jobs-easy-apply-modal input[type="checkbox"], '
                'input[type="checkbox"], [role="checkbox"]'
            )
            
            # Keywords for consent/agreement checkboxes
            consent_keywords = [
                'consent', 'agree', 'accept', 'approve', 'authorize', 'confirm',
                'acknowledge', 'certify', 'understand', 'attest',
                'i consent', 'i agree', 'i accept', 'i approve', 'i authorize',
                'i confirm', 'i acknowledge', 'i certify', 'i understand',
                'terms', 'privacy', 'policy', 'conditions', 'declaration',
                'by checking', 'by clicking', 'by submitting'
            ]
            
            for cb in checkboxes:
                try:
                    # Check if already checked
                    is_checked = cb.is_selected()
                    if not is_checked:
                        aria_checked = cb.get_attribute('aria-checked')
                        is_checked = aria_checked == 'true'
                    if is_checked:
                        continue
                    
                    question = self._get_question_text(cb)
                    question_lower = question.lower()
                    
                    # Check if this is a consent/agreement checkbox - ALWAYS check these
                    is_consent_box = any(kw in question_lower for kw in consent_keywords)
                    
                    # Also check visible checkboxes
                    try:
                        is_visible = cb.is_displayed()
                    except:
                        is_visible = False
                    
                    if is_consent_box or is_visible:
                        checked = False
                        
                        # Method 1: Direct click
                        try:
                            cb.click()
                            checked = cb.is_selected() or cb.get_attribute('aria-checked') == 'true'
                        except:
                            pass
                        
                        # Method 2: JavaScript click
                        if not checked:
                            try:
                                self.driver.execute_script("arguments[0].click();", cb)
                                checked = cb.is_selected() or cb.get_attribute('aria-checked') == 'true'
                            except:
                                pass
                        
                        # Method 3: Click via label for attribute
                        if not checked:
                            cb_id = cb.get_attribute("id")
                            if cb_id:
                                try:
                                    label = self.driver.find_element(By.CSS_SELECTOR, f'label[for="{cb_id}"]')
                                    label.click()
                                    checked = cb.is_selected() or cb.get_attribute('aria-checked') == 'true'
                                except:
                                    pass
                        
                        # Method 4: Click parent label
                        if not checked:
                            try:
                                parent_label = cb.find_element(By.XPATH, './ancestor::label')
                                parent_label.click()
                                checked = True
                            except:
                                pass
                        
                        # Method 5: Set via JavaScript
                        if not checked:
                            try:
                                self.driver.execute_script("""
                                    arguments[0].checked = true;
                                    arguments[0].setAttribute('checked', 'checked');
                                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                                    arguments[0].dispatchEvent(new Event('click', {bubbles: true}));
                                """, cb)
                                checked = True
                            except:
                                pass
                        
                        if checked:
                            print(f"      ☑️ Checked: {question[:40]}...")
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _handle_file_uploads(self):
        """Handle resume uploads"""
        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                '.jobs-easy-apply-content input[type="file"]'
            )
            
            for inp in file_inputs:
                try:
                    question = self._get_question_text(inp).lower()
                    
                    if 'resume' in question or 'cv' in question:
                        resume_path = USER_PROFILE["resumes"]["default"]
                        if os.path.exists(resume_path):
                            inp.send_keys(os.path.abspath(resume_path))
                            print(f"      📎 Uploaded resume")
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
    
    def _get_question_text(self, element, max_levels: int = 5) -> str:
        """Get question text from parent elements"""
        try:
            # Try aria-label first
            label = element.get_attribute('aria-label')
            if label:
                return label
            
            # Try placeholder
            placeholder = element.get_attribute('placeholder')
            if placeholder:
                return placeholder
            
            # Try finding label by ID
            elem_id = element.get_attribute('id')
            if elem_id:
                try:
                    label_elem = self.driver.find_element(By.CSS_SELECTOR, f'label[for="{elem_id}"]')
                    return label_elem.text
                except:
                    pass
            
            # Try parent text
            parent = element
            for _ in range(max_levels):
                parent = parent.find_element(By.XPATH, '..')
                text = parent.text
                if 10 < len(text) < 500:
                    return text
        except:
            pass
        
        return ""
    
    def _has_form_errors(self) -> bool:
        """Check for form validation errors and try to fix them"""
        try:
            # Find error messages
            error_selectors = [
                '.artdeco-inline-feedback--error',
                '.fb-form-element__error-text',
                '[data-test-form-element-error]',
                '.jobs-easy-apply-form-element__error',
                '.form-error',
            ]
            
            for sel in error_selectors:
                errors = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for error in errors:
                    if error.is_displayed():
                        error_text = error.text.strip()
                        if error_text:
                            print(f"         ⚠️ Error found: {error_text}")
                            
                            # Try to fix based on error message
                            self._fix_error(error, error_text)
                            return True
            
            # Also check page source for error patterns
            page = self.driver.page_source.lower()
            error_patterns = [
                'please enter a valid',
                'this field is required',
                'file is required',
                'invalid value',
                'must be a number',
                'is required',
            ]
            
            if any(err in page for err in error_patterns):
                print(f"         ⚠️ Form has validation errors")
                return True
                
        except Exception as e:
            pass
        
        return False
    
    def _fix_error(self, error_element, error_text: str):
        """Try to fix a specific form error"""
        try:
            error_lower = error_text.lower()
            
            # Find the parent form element
            parent = error_element
            for _ in range(5):
                parent = parent.find_element(By.XPATH, '..')
                
                # Look for input in this container
                inputs = parent.find_elements(By.CSS_SELECTOR, 'input, textarea, select')
                for inp in inputs:
                    if inp.is_displayed():
                        inp_type = inp.get_attribute('type') or 'text'
                        
                        # Fix based on input type and error
                        if inp_type == 'number' or 'number' in error_lower:
                            inp.clear()
                            inp.send_keys("1")
                            print(f"            → Fixed with: 1")
                            return
                        elif 'required' in error_lower:
                            if inp_type in ['text', 'email', 'tel', 'url']:
                                inp.clear()
                                inp.send_keys("1")
                                print(f"            → Fixed with: 1")
                                return
                        
        except Exception as e:
            pass
    
    def _uncheck_follow(self):
        """Uncheck follow company option"""
        try:
            cb = self.driver.find_element(By.CSS_SELECTOR, 'input[id*="follow-company"]')
            if cb.is_selected():
                cb.click()
        except:
            pass
    
    def _check_success(self) -> bool:
        """Check if application was submitted successfully"""
        time.sleep(2)
        page = self.driver.page_source.lower()
        return any(s in page for s in [
            'application sent',
            'your application was sent',
            'application submitted'
        ])
    
    def _close_modal(self):
        """Close any open modals"""
        try:
            # Close button
            close_btn = self.driver.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss')
            close_btn.click()
            time.sleep(0.5)
            
            # Confirm discard
            try:
                discard_btns = self.driver.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')
                if len(discard_btns) > 1:
                    discard_btns[1].click()
            except:
                pass
        except:
            pass
        
        # Close toasts
        try:
            toast = self.driver.find_element(By.CLASS_NAME, 'artdeco-toast-item__dismiss')
            toast.click()
        except:
            pass
    
    def _goto_next_page(self) -> bool:
        """Go to next page"""
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR,
                'button[aria-label="View next page"]'
            )
            if next_btn.is_enabled():
                next_btn.click()
                return True
        except:
            pass
        return False
    
    def _print_stats(self):
        """Print session statistics"""
        print("\n" + "="*50)
        print("📊 SESSION STATISTICS")
        print("="*50)
        print(f"✅ Applied: {self.applied_count}")
        print(f"⏭️ Skipped: {self.skipped_count}")
        print(f"❌ Failed: {self.failed_count}")
        print(f"📝 Today's total: {app_logger.get_today_count()}")
        print(f"📈 All-time total: {app_logger.get_total_count()}")
        print("="*50)


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🤖 ULTIMATE LINKEDIN EASY APPLY BOT")
    print("    with AI-Powered Form Filling")
    print("="*60 + "\n")
    
    # Check for password
    if not os.getenv("LINKEDIN_PASSWORD"):
        password = input("Enter LinkedIn password: ").strip()
        if password:
            os.environ["LINKEDIN_PASSWORD"] = password
        else:
            print("❌ Password required!")
            return
    
    # Check for AI API key
    if not any([
        os.getenv("OPENAI_API_KEY"),
        os.getenv("GROQ_API_KEY"),
        os.getenv("GEMINI_API_KEY"),
        os.getenv("GOOGLE_API_KEY"),
    ]):
        print("\n⚠️  No AI API key found. Using rule-based form filling.")
        print("For AI-powered filling, set one of:")
        print("  - OPENAI_API_KEY (recommended)")
        print("  - GROQ_API_KEY (free)")
        print("  - GEMINI_API_KEY or GOOGLE_API_KEY (free)")
        print()
    
    # Run bot
    bot = UltimateLinkedInBot()
    bot.run()


if __name__ == "__main__":
    main()
