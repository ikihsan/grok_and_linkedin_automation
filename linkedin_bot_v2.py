"""
LinkedIn Easy Apply Bot V2
With full debugging and improved element detection
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

from config import USER_PROFILE, RATE_LIMITS
from ai_form_filler import AIFormFiller
from application_logger import app_logger


class LinkedInBotV2:
    """LinkedIn Easy Apply Bot with full debugging"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.ai_filler = None
        
        # Credentials - ALWAYS from environment variables
        self.email = os.getenv("LINKEDIN_EMAIL", "")
        self.password = os.getenv("LINKEDIN_PASSWORD", "")
        
        print(f"📧 Using email: {self.email}")
        print(f"🔑 Password: {'*' * len(self.password) if self.password else 'NOT SET'}")
        
        # Search params - MERN/Backend priority
        self.positions = ["MERN Stack Developer", "Backend Developer", "Node.js Developer", "Full Stack Developer", "Web Developer"]
        self.locations = ["India", "Remote"]
        
        # Blacklist - minimal
        self.title_blacklist = ["intern", "internship", "sales", "manager", "director"]
        self.company_blacklist = []
        
        # Stats
        self.applied_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        self.debug = True  # Enable debug output
    
    def log(self, msg: str, level: str = "INFO"):
        """Debug logging"""
        if self.debug or level in ["ERROR", "SUCCESS"]:
            prefix = {"INFO": "ℹ️", "DEBUG": "🔍", "ERROR": "❌", "SUCCESS": "✅", "WARN": "⚠️"}
            print(f"   {prefix.get(level, '')} {msg}", flush=True)
    
    def start_browser(self) -> bool:
        """Start Chrome browser"""
        try:
            print("🌐 Setting up Chrome options...", flush=True)
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Find Chrome
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    options.binary_location = path
                    print(f"   Found Chrome at: {path}", flush=True)
                    break
            
            print("🚀 Launching Chrome browser (this may take a moment)...", flush=True)
            self.driver = webdriver.Chrome(options=options)
            print("   Chrome launched successfully!", flush=True)
            
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            })
            
            self.wait = WebDriverWait(self.driver, 15)
            self.ai_filler = AIFormFiller(USER_PROFILE)
            
            print("✅ Browser started!", flush=True)
            return True
        except Exception as e:
            print(f"❌ Browser error: {e}", flush=True)
            traceback.print_exc()
            return False
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def login(self) -> bool:
        """Login to LinkedIn"""
        try:
            print("🔑 Logging in...")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(3)
            
            # Email
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            for c in self.email:
                email_field.send_keys(c)
                time.sleep(random.uniform(0.02, 0.05))
            
            # Password
            pw_field = self.driver.find_element(By.ID, "password")
            pw_field.clear()
            for c in self.password:
                pw_field.send_keys(c)
                time.sleep(random.uniform(0.02, 0.05))
            
            # Submit
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(5)
            
            # Handle verification
            if 'checkpoint' in self.driver.current_url.lower():
                print("\n⚠️ SECURITY CHECK - Complete it in browser!")
                input("Press ENTER when done...")
                time.sleep(3)
            
            # Check login
            if self._is_logged_in():
                print("✅ Logged in!")
                return True
            
            print("❌ Login failed")
            return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def _is_logged_in(self) -> bool:
        try:
            self.driver.find_element(By.CSS_SELECTOR, '.global-nav__me, .feed-identity-module')
            return True
        except:
            return 'feed' in self.driver.current_url or 'jobs' in self.driver.current_url
    
    def run(self):
        """Main loop"""
        if not self.start_browser():
            return
        if not self.login():
            self.close()
            return
        
        print(f"\n🚀 Starting applications...")
        
        try:
            for position in self.positions:
                for location in self.locations:
                    try:
                        print(f"\n{'='*50}")
                        print(f"🔍 SEARCHING: {position} in {location}")
                        print(f"{'='*50}")
                        
                        self._search_and_apply(position, location)
                        time.sleep(random.uniform(5, 10))
                    except Exception as e:
                        print(f"❌ Error in search: {e}")
                        continue
        
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            self._print_stats()
            self.close()
    
    def _search_and_apply(self, position: str, location: str):
        """Search and apply to jobs"""
        # Build URL
        url = (
            f"https://www.linkedin.com/jobs/search/?"
            f"keywords={position.replace(' ', '%20')}&"
            f"location={location.replace(' ', '%20')}&"
            f"f_AL=true&"  # Easy Apply filter
            f"f_TPR=r604800&"  # Past week
            f"sortBy=DD"  # Date posted
        )
        
        self.log(f"URL: {url}", "DEBUG")
        self.driver.get(url)
        time.sleep(4)
        
        # Process pages
        for page_num in range(2):  # 2 pages max
            print(f"\n📄 PAGE {page_num + 1}")
            
            try:
                # Get jobs
                jobs = self._get_job_cards()
                print(f"   Found {len(jobs)} job cards")
                
                if not jobs:
                    break
                
                # Process each job
                for i, job in enumerate(jobs):
                    try:
                        print(f"\n   --- Job {i+1}/{len(jobs)} ---")
                        self._process_job(job)
                        time.sleep(random.uniform(1, 3))
                    except StaleElementReferenceException:
                        print("   ⚠️ Stale element - skipping job")
                        continue
                    except Exception as e:
                        print(f"   ❌ Job error: {e}")
                        continue
                
                # Next page
                if not self._next_page():
                    break
                time.sleep(3)
            except Exception as e:
                print(f"   ❌ Page error: {e}")
                break
    
    def _get_job_cards(self) -> List:
        """Get job card elements"""
        time.sleep(2)
        
        # Scroll to load
        try:
            container = self.driver.find_element(By.CSS_SELECTOR, ".jobs-search-results-list")
            for _ in range(3):
                self.driver.execute_script("arguments[0].scrollBy(0, 500);", container)
                time.sleep(0.5)
        except Exception as e:
            self.log(f"Scroll failed: {e}", "DEBUG")
        
        # Find cards with multiple selectors
        selectors = [
            "li.jobs-search-results__list-item",
            ".scaffold-layout__list-item",
            "li[data-occludable-job-id]",
            ".job-card-container",
        ]
        
        for sel in selectors:
            cards = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if cards:
                self.log(f"Found cards with: {sel}", "DEBUG")
                return cards
        
        self.log("No cards found with any selector", "ERROR")
        return []
    
    def _process_job(self, job_card):
        """Process a single job"""
        # Extract info
        title = self._get_text(job_card, [
            ".job-card-list__title",
            ".job-card-container__link",
            "a[href*='/jobs/view/']"
        ])
        
        company = self._get_text(job_card, [
            ".job-card-container__primary-description",
            ".artdeco-entity-lockup__subtitle",
            ".job-card-container__company-name"
        ])
        
        self.log(f"Title: {title[:50] if title else 'N/A'}")
        self.log(f"Company: {company[:30] if company else 'N/A'}")
        
        if not title:
            self.log("Could not get title", "ERROR")
            return
        
        # Check blacklist
        title_lower = title.lower()
        for bl in self.title_blacklist:
            if bl in title_lower:
                self.log(f"Blacklisted: contains '{bl}'", "WARN")
                self.skipped_count += 1
                return
        
        # Click on job card to load details
        self._click_job_card(job_card)
        time.sleep(2)
        
        # Find and click Easy Apply button
        success = self._click_easy_apply_and_fill()
        
        if success:
            self.log(f"APPLIED: {title} @ {company}", "SUCCESS")
            self.applied_count += 1
        else:
            self.failed_count += 1
    
    def _get_text(self, parent, selectors: List[str]) -> str:
        """Get text from first matching selector"""
        for sel in selectors:
            try:
                elem = parent.find_element(By.CSS_SELECTOR, sel)
                text = elem.text.strip()
                if text:
                    return text
            except:
                pass
        return ""
    
    def _click_job_card(self, job_card):
        """Click on job card to load job details"""
        try:
            # Try clicking the title link
            link = job_card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
            time.sleep(0.3)
            link.click()
            self.log("Clicked job card", "DEBUG")
        except Exception as e:
            self.log(f"Card click failed: {e}", "DEBUG")
            try:
                job_card.click()
            except:
                pass
    
    def _click_easy_apply_and_fill(self) -> bool:
        """Find Easy Apply button, click it, and fill form"""
        time.sleep(1)
        
        # Find Easy Apply button
        easy_btn = self._find_easy_apply_button()
        
        if not easy_btn:
            self.log("No Easy Apply button found", "WARN")
            return False
        
        # Click it
        try:
            self.log("Clicking Easy Apply button...", "DEBUG")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_btn)
            time.sleep(0.3)
            easy_btn.click()
        except Exception as e:
            self.log(f"Click failed, trying JS: {e}", "DEBUG")
            self.driver.execute_script("arguments[0].click();", easy_btn)
        
        time.sleep(2)
        
        # Check if modal opened
        if not self._is_modal_open():
            self.log("Modal didn't open", "ERROR")
            return False
        
        self.log("Modal opened - filling form", "DEBUG")
        
        # Fill and submit
        return self._fill_and_submit()
    
    def _find_easy_apply_button(self):
        """Find the Easy Apply button"""
        # Multiple selector strategies
        selectors = [
            "button.jobs-apply-button",
            "button[aria-label*='Easy Apply']",
            ".jobs-apply-button--top-card button",
            ".jobs-s-apply button",
            "button.artdeco-button--primary"
        ]
        
        for sel in selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for btn in buttons:
                    if btn.is_displayed():
                        text = btn.text.lower()
                        aria = (btn.get_attribute("aria-label") or "").lower()
                        
                        if 'easy apply' in text or 'easy apply' in aria:
                            self.log(f"Found button with selector: {sel}", "DEBUG")
                            return btn
            except:
                pass
        
        # Fallback: find by text content
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower().strip()
                    if text == 'easy apply' or 'easy apply' in text:
                        self.log("Found button by text search", "DEBUG")
                        return btn
        except:
            pass
        
        # Debug: print all visible buttons
        self.log("Debugging all buttons:", "DEBUG")
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for i, btn in enumerate(buttons[:10]):
                if btn.is_displayed():
                    self.log(f"  Button {i}: '{btn.text[:30]}'", "DEBUG")
        except:
            pass
        
        return None
    
    def _is_modal_open(self) -> bool:
        """Check if Easy Apply modal is open"""
        selectors = [
            ".jobs-easy-apply-modal",
            ".jobs-easy-apply-content",
            "[data-test-modal]",
            ".artdeco-modal--layer-default"
        ]
        
        for sel in selectors:
            try:
                modal = self.driver.find_element(By.CSS_SELECTOR, sel)
                if modal.is_displayed():
                    return True
            except:
                pass
        return False
    
    def _fill_and_submit(self) -> bool:
        """Fill form and submit application"""
        max_steps = 10
        
        for step in range(max_steps):
            self.log(f"Form step {step + 1}", "DEBUG")
            
            try:
                # Fill current page
                self._fill_current_page()
                time.sleep(0.5)
                
                # Find action button (Next, Review, Submit)
                btn, btn_type = self._find_action_button()
                
                if not btn:
                    self.log("No action button found", "ERROR")
                    self._close_modal()
                    return False
                
                self.log(f"Found button: {btn_type}", "DEBUG")
                
                if btn_type == "submit":
                    # Uncheck follow company
                    self._uncheck_follow()
                    
                    # Click submit with retry
                    try:
                        btn.click()
                    except StaleElementReferenceException:
                        time.sleep(0.5)
                        btn, btn_type = self._find_action_button()
                        if btn:
                            self.driver.execute_script("arguments[0].click();", btn)
                    except:
                        self.driver.execute_script("arguments[0].click();", btn)
                    
                    time.sleep(3)
                    
                    # Check success
                    if self._check_success():
                        self._close_modal()
                        return True
                    else:
                        self.log("Submit didn't succeed", "ERROR")
                        self._close_modal()
                        return False
                
                # Click next/review with retry for stale elements
                try:
                    btn.click()
                except StaleElementReferenceException:
                    time.sleep(0.5)
                    btn, btn_type = self._find_action_button()
                    if btn:
                        self.driver.execute_script("arguments[0].click();", btn)
                except:
                    self.driver.execute_script("arguments[0].click();", btn)
                
                time.sleep(1.5)
                
                # Check for errors
                if self._has_errors():
                    self.log("Form has errors - retrying fill", "WARN")
                    self._fill_current_page()
                    time.sleep(0.5)
                    
            except StaleElementReferenceException:
                self.log("Stale element - retrying step", "WARN")
                time.sleep(1)
                continue
            except Exception as e:
                self.log(f"Step error: {e}", "WARN")
                time.sleep(1)
                continue
        
        self.log("Max steps reached", "ERROR")
        self._close_modal()
        return False
    
    def _find_action_button(self) -> Tuple[any, str]:
        """Find Next/Review/Submit button"""
        try:
            # Look for primary buttons in the modal footer
            buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                ".jobs-easy-apply-content button.artdeco-button--primary, "
                ".jobs-easy-apply-modal button.artdeco-button--primary, "
                "[data-easy-apply-next-button], "
                "button[aria-label*='Submit'], "
                "button[aria-label*='Continue'], "
                "button[aria-label*='Review']"
            )
            
            for btn in buttons:
                if not btn.is_displayed():
                    continue
                
                text = btn.text.lower().strip()
                aria = (btn.get_attribute("aria-label") or "").lower()
                
                if 'submit' in text or 'submit' in aria:
                    return (btn, "submit")
                elif 'review' in text or 'review' in aria:
                    return (btn, "review")
                elif 'next' in text or 'continue' in text or 'next' in aria:
                    return (btn, "next")
            
            # Fallback: any visible primary button
            for btn in buttons:
                if btn.is_displayed():
                    return (btn, "next")
                    
        except Exception as e:
            self.log(f"Button search error: {e}", "DEBUG")
        
        return (None, "")
    
    def _fill_current_page(self):
        """Fill all fields on current modal page"""
        # Text inputs
        self._fill_text_fields()
        
        # Dropdowns
        self._fill_dropdowns()
        
        # Radio buttons
        self._fill_radios()
        
        # Checkboxes
        self._fill_checkboxes()
        
        # File uploads
        self._handle_uploads()
    
    def _fill_text_fields(self):
        """Fill text inputs and textareas"""
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR,
                ".jobs-easy-apply-content input[type='text'], "
                ".jobs-easy-apply-content input[type='number'], "
                ".jobs-easy-apply-content input[type='tel'], "
                ".jobs-easy-apply-content input[type='email'], "
                ".jobs-easy-apply-content textarea, "
                ".jobs-easy-apply-modal input:not([type='file']):not([type='hidden']):not([type='checkbox']):not([type='radio'])"
            )
            
            for inp in inputs:
                try:
                    if not inp.is_displayed():
                        continue
                    
                    # Skip if already filled
                    current = inp.get_attribute("value") or ""
                    if current.strip():
                        continue
                    
                    # Get question
                    question = self._get_question_for_element(inp)
                    input_type = inp.get_attribute("type") or "text"
                    
                    # Get answer from AI
                    field_type = "number" if input_type == "number" else "text"
                    answer = self.ai_filler.get_answer(question, field_type)
                    
                    if answer:
                        inp.click()
                        inp.clear()
                        inp.send_keys(str(answer))
                        self.log(f"Filled: {question[:30]}... → {answer}", "DEBUG")
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            self.log(f"Text fill error: {e}", "DEBUG")
    
    def _fill_dropdowns(self):
        """Fill dropdown selects"""
        try:
            selects = self.driver.find_elements(By.CSS_SELECTOR, 
                ".jobs-easy-apply-content select, "
                ".jobs-easy-apply-modal select"
            )
            
            for sel_elem in selects:
                try:
                    if not sel_elem.is_displayed():
                        continue
                    
                    select = Select(sel_elem)
                    current = select.first_selected_option.text.lower()
                    
                    # Skip if already selected
                    if current and 'select' not in current and 'choose' not in current:
                        continue
                    
                    question = self._get_question_for_element(sel_elem)
                    options = [o.text for o in select.options if o.text.strip()]
                    
                    answer = self.ai_filler.get_answer(question, "dropdown", options)
                    
                    try:
                        select.select_by_visible_text(answer)
                        self.log(f"Selected: {question[:30]}... → {answer}", "DEBUG")
                    except:
                        if len(options) > 1:
                            select.select_by_index(1)
                            
                except Exception as e:
                    pass
                    
        except Exception as e:
            self.log(f"Dropdown fill error: {e}", "DEBUG")
    
    def _fill_radios(self):
        """Fill radio button groups"""
        try:
            fieldsets = self.driver.find_elements(By.CSS_SELECTOR,
                ".jobs-easy-apply-content fieldset, "
                ".jobs-easy-apply-modal [data-test-form-element]"
            )
            
            for fs in fieldsets:
                try:
                    radios = fs.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    if not radios:
                        continue
                    
                    # Skip if one already selected
                    if any(r.is_selected() for r in radios):
                        continue
                    
                    question = fs.text.strip()
                    labels = fs.find_elements(By.TAG_NAME, "label")
                    options = [l.text.strip() for l in labels if l.text.strip()]
                    
                    answer = self.ai_filler.get_answer(question, "radio", options)
                    
                    # Click matching label
                    for label in labels:
                        if answer.lower() in label.text.lower():
                            label.click()
                            self.log(f"Radio: {question[:30]}... → {label.text}", "DEBUG")
                            break
                    else:
                        # Default first
                        if labels:
                            labels[0].click()
                            
                except Exception as e:
                    pass
                    
        except Exception as e:
            self.log(f"Radio fill error: {e}", "DEBUG")
    
    def _fill_checkboxes(self):
        """Fill checkboxes"""
        try:
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR,
                ".jobs-easy-apply-content input[type='checkbox'], "
                ".jobs-easy-apply-modal input[type='checkbox']"
            )
            
            for cb in checkboxes:
                try:
                    if not cb.is_displayed() or cb.is_selected():
                        continue
                    
                    question = self._get_question_for_element(cb)
                    q_lower = question.lower()
                    
                    # Check agreement boxes
                    if any(kw in q_lower for kw in ['agree', 'terms', 'consent', 'acknowledge', 'confirm']):
                        try:
                            cb.click()
                        except:
                            # Try clicking label
                            cb_id = cb.get_attribute("id")
                            if cb_id:
                                label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']")
                                label.click()
                        self.log(f"Checked: {question[:40]}...", "DEBUG")
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            self.log(f"Checkbox fill error: {e}", "DEBUG")
    
    def _handle_uploads(self):
        """Handle file uploads (resume)"""
        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                ".jobs-easy-apply-content input[type='file'], "
                ".jobs-easy-apply-modal input[type='file']"
            )
            
            for inp in file_inputs:
                try:
                    question = self._get_question_for_element(inp).lower()
                    
                    if 'resume' in question or 'cv' in question:
                        resume_path = USER_PROFILE["resumes"]["default"]
                        if os.path.exists(resume_path):
                            inp.send_keys(os.path.abspath(resume_path))
                            self.log("Uploaded resume", "DEBUG")
                            
                except Exception as e:
                    pass
                    
        except Exception as e:
            self.log(f"Upload error: {e}", "DEBUG")
    
    def _get_question_for_element(self, elem) -> str:
        """Get the question/label for a form element"""
        try:
            # Try aria-label
            label = elem.get_attribute("aria-label")
            if label:
                return label
            
            # Try placeholder
            placeholder = elem.get_attribute("placeholder")
            if placeholder:
                return placeholder
            
            # Try associated label
            elem_id = elem.get_attribute("id")
            if elem_id:
                try:
                    label_elem = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{elem_id}']")
                    return label_elem.text
                except:
                    pass
            
            # Try parent text
            parent = elem
            for _ in range(4):
                parent = parent.find_element(By.XPATH, "..")
                text = parent.text.strip()
                if 10 < len(text) < 300:
                    return text
        except:
            pass
        
        return ""
    
    def _has_errors(self) -> bool:
        """Check for form errors"""
        try:
            error_msgs = self.driver.find_elements(By.CSS_SELECTOR, 
                ".artdeco-inline-feedback--error, "
                "[data-test-form-element-error], "
                ".fb-form-element-error"
            )
            return any(e.is_displayed() for e in error_msgs)
        except:
            return False
    
    def _uncheck_follow(self):
        """Uncheck 'follow company' checkbox"""
        try:
            cb = self.driver.find_element(By.CSS_SELECTOR, "input[id*='follow']")
            if cb.is_selected():
                cb.click()
        except:
            pass
    
    def _check_success(self) -> bool:
        """Check if application was submitted"""
        time.sleep(2)
        page = self.driver.page_source.lower()
        return any(s in page for s in [
            'application sent',
            'your application was sent',
            'application submitted',
            'applied'
        ])
    
    def _close_modal(self):
        """Close the Easy Apply modal"""
        try:
            # Dismiss button
            close_btn = self.driver.find_element(By.CSS_SELECTOR, 
                ".artdeco-modal__dismiss, "
                "button[aria-label='Dismiss']"
            )
            close_btn.click()
            time.sleep(0.5)
            
            # Confirm discard if needed
            try:
                discard = self.driver.find_element(By.CSS_SELECTOR, 
                    "[data-test-modal-primary-btn], "
                    ".artdeco-modal__confirm-dialog-btn:last-child"
                )
                if discard.is_displayed():
                    discard.click()
            except:
                pass
                
        except:
            pass
        
        # Also close any toasts
        try:
            toast = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-toast-item__dismiss")
            toast.click()
        except:
            pass
    
    def _next_page(self) -> bool:
        """Go to next results page"""
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='View next page']")
            if next_btn.is_enabled():
                next_btn.click()
                return True
        except:
            pass
        return False
    
    def _print_stats(self):
        """Print session stats"""
        print("\n" + "="*50)
        print("📊 SESSION STATS")
        print("="*50)
        print(f"✅ Applied: {self.applied_count}")
        print(f"⏭️ Skipped: {self.skipped_count}")
        print(f"❌ Failed: {self.failed_count}")
        print("="*50)


def main():
    print("\n" + "="*60)
    print("🤖 LINKEDIN EASY APPLY BOT V2")
    print("    With Full Debugging")
    print("="*60)
    
    # Password
    if not os.getenv("LINKEDIN_PASSWORD"):
        pw = input("Enter LinkedIn password: ").strip()
        os.environ["LINKEDIN_PASSWORD"] = pw
    
    bot = LinkedInBotV2()
    bot.run()


if __name__ == "__main__":
    main()
