"""
Simple LinkedIn Easy Apply Bot - No external dependencies except selenium
"""
import sys
import os
import time
import random

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
print("=" * 50, flush=True)
print("🚀 SIMPLE LINKEDIN BOT", flush=True)
print("=" * 50, flush=True)

# Load .env manually
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    print(f"📂 Loading .env...", flush=True)
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    print("✅ .env loaded", flush=True)

EMAIL = os.getenv("LINKEDIN_EMAIL", "")
PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

print(f"📧 Email: {EMAIL}", flush=True)
print(f"🔑 Password: {'*' * len(PASSWORD)}", flush=True)

if not EMAIL or not PASSWORD:
    print("❌ Missing credentials in .env file!", flush=True)
    sys.exit(1)

# Now import selenium
print("📦 Loading selenium...", flush=True)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
    print("✅ Selenium loaded", flush=True)
except ImportError as e:
    print(f"❌ Selenium not installed: {e}", flush=True)
    print("Run: pip install selenium", flush=True)
    sys.exit(1)

# User profile - YOUR DATA
USER_PROFILE = {
    "name": "Mohd Ihsan",
    "email": "ikihsaan@gmail.com",
    "phone": "9084aborte703",
    "location": "Noida, India",
    "experience_years": 1,
    "current_ctc": 280000,
    "expected_ctc": 400000,
    "notice_period": 10,
    "skills": ["Python", "Django", "Flask", "FastAPI", "JavaScript", "React", "Node.js", 
               "PostgreSQL", "MongoDB", "Redis", "Docker", "AWS", "Git", "REST API", "GraphQL"],
    "languages": ["English", "Hindi"],
    "education": "Bachelor's in Computer Science",
    "linkedin": "https://linkedin.com/in/ihsan",
    "github": "https://github.com/ihsan",
    "website": "https://ihsan.dev",
    "willing_to_relocate": True,
    "work_authorization": True,
    "requires_sponsorship": False,
}

class SimpleLinkedInBot:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.applied = 0
        self.skipped = 0
        self.failed = 0
        
    def start_browser(self):
        """Start Chrome browser"""
        print("🌐 Starting Chrome...", flush=True)
        
        try:
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Try to find Chrome
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    options.binary_location = path
                    print(f"✅ Chrome found: {path}", flush=True)
                    break
            
            print("🔧 Creating WebDriver...", flush=True)
            self.driver = webdriver.Chrome(options=options)
            
            # Hide webdriver
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            })
            
            self.wait = WebDriverWait(self.driver, 15)
            print("✅ Browser started!", flush=True)
            return True
            
        except Exception as e:
            print(f"❌ Browser error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False
    
    def login(self):
        """Login to LinkedIn"""
        print("🔑 Going to LinkedIn login...", flush=True)
        
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(3)
            
            print("📝 Entering email...", flush=True)
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            email_field.send_keys(EMAIL)
            
            print("📝 Entering password...", flush=True)
            pw_field = self.driver.find_element(By.ID, "password")
            pw_field.clear()
            pw_field.send_keys(PASSWORD)
            
            print("📤 Submitting...", flush=True)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(5)
            
            # Check for security verification
            if 'checkpoint' in self.driver.current_url.lower() or 'challenge' in self.driver.current_url.lower():
                print("\n" + "=" * 50, flush=True)
                print("⚠️  SECURITY CHECK DETECTED!", flush=True)
                print("Please complete the verification in the browser.", flush=True)
                print("=" * 50, flush=True)
                input("Press ENTER when done...")
                time.sleep(3)
            
            # Verify login
            if 'feed' in self.driver.current_url or 'jobs' in self.driver.current_url:
                print("✅ Login successful!", flush=True)
                return True
            
            try:
                self.driver.find_element(By.CSS_SELECTOR, '.global-nav__me, .feed-identity-module')
                print("✅ Login successful!", flush=True)
                return True
            except:
                pass
            
            print("❌ Login may have failed. Current URL:", self.driver.current_url, flush=True)
            return False
            
        except Exception as e:
            print(f"❌ Login error: {e}", flush=True)
            return False
    
    def search_jobs(self, keyword="Software Engineer", location="India"):
        """Search for jobs"""
        print(f"\n🔍 Searching: {keyword} in {location}", flush=True)
        
        url = (
            f"https://www.linkedin.com/jobs/search/?"
            f"keywords={keyword.replace(' ', '%20')}&"
            f"location={location.replace(' ', '%20')}&"
            f"f_AL=true&"  # Easy Apply
            f"f_TPR=r604800&"  # Past week
            f"sortBy=DD"  # Most recent
        )
        
        self.driver.get(url)
        time.sleep(4)
        print("✅ Search results loaded", flush=True)
    
    def get_job_cards(self):
        """Get job listing cards"""
        try:
            # Scroll to load more
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(1)
            
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
            print(f"📋 Found {len(cards)} job cards", flush=True)
            return cards
        except Exception as e:
            print(f"❌ Error getting jobs: {e}", flush=True)
            return []
    
    def click_easy_apply(self):
        """Click the Easy Apply button"""
        try:
            # Wait for job details to load
            time.sleep(2)
            
            # Find Easy Apply button
            selectors = [
                "button.jobs-apply-button",
                "button[aria-label*='Easy Apply']",
                ".jobs-apply-button--top-card button",
                "button.jobs-apply-button--top-card",
            ]
            
            for selector in selectors:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed() and "Easy Apply" in btn.text:
                        btn.click()
                        time.sleep(2)
                        print("✅ Clicked Easy Apply", flush=True)
                        return True
                except:
                    continue
            
            print("⚠️ No Easy Apply button found", flush=True)
            return False
            
        except Exception as e:
            print(f"❌ Easy Apply click error: {e}", flush=True)
            return False
    
    def fill_form(self):
        """Fill the application form"""
        try:
            time.sleep(1)
            
            # Fill text inputs
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input:not([type])")
            for inp in inputs:
                try:
                    if not inp.is_displayed():
                        continue
                    
                    label = self._get_label(inp)
                    current_val = inp.get_attribute("value") or ""
                    
                    if current_val.strip():
                        continue  # Already filled
                    
                    answer = self._get_answer(label)
                    if answer:
                        inp.clear()
                        inp.send_keys(str(answer))
                        print(f"   ✏️ {label[:30]}: {answer}", flush=True)
                except:
                    continue
            
            # Fill number inputs
            number_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='number']")
            for inp in number_inputs:
                try:
                    if not inp.is_displayed():
                        continue
                    
                    label = self._get_label(inp)
                    current_val = inp.get_attribute("value") or ""
                    
                    if current_val.strip():
                        continue
                    
                    answer = self._get_number_answer(label)
                    inp.clear()
                    inp.send_keys(str(answer))
                    print(f"   🔢 {label[:30]}: {answer}", flush=True)
                except:
                    continue
            
            # Fill dropdowns
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            for sel in selects:
                try:
                    if not sel.is_displayed():
                        continue
                    
                    select = Select(sel)
                    if select.first_selected_option.text.strip():
                        continue
                    
                    options = [o.text for o in select.options if o.text.strip() and o.text != "Select an option"]
                    if options:
                        # Pick best option
                        label = self._get_label(sel)
                        best = self._pick_dropdown_option(label, options)
                        select.select_by_visible_text(best)
                        print(f"   📋 {label[:30]}: {best}", flush=True)
                except:
                    continue
            
            # Handle radio buttons - select Yes/positive options
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            radio_groups = {}
            for radio in radios:
                try:
                    name = radio.get_attribute("name")
                    if name and name not in radio_groups:
                        radio_groups[name] = []
                    if name:
                        radio_groups[name].append(radio)
                except:
                    continue
            
            for name, group in radio_groups.items():
                try:
                    # Check if any already selected
                    selected = any(r.is_selected() for r in group)
                    if selected:
                        continue
                    
                    # Pick Yes/positive option
                    for radio in group:
                        label = self._get_label(radio).lower()
                        if any(pos in label for pos in ['yes', 'true', 'agree', 'confirm']):
                            self._safe_click(radio)
                            print(f"   🔘 Selected: Yes", flush=True)
                            break
                    else:
                        # Just select first if no positive found
                        if group:
                            self._safe_click(group[0])
                except:
                    continue
            
            # ALWAYS check ALL checkboxes
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for cb in checkboxes:
                try:
                    if not cb.is_displayed():
                        continue
                    if not cb.is_selected():
                        self._safe_click(cb)
                        print(f"   ☑️ Checkbox ticked", flush=True)
                except:
                    continue
            
            return True
            
        except Exception as e:
            print(f"❌ Form fill error: {e}", flush=True)
            return False
    
    def _get_label(self, element):
        """Get label for an input element"""
        try:
            # Try aria-label
            label = element.get_attribute("aria-label")
            if label:
                return label
            
            # Try placeholder
            label = element.get_attribute("placeholder")
            if label:
                return label
            
            # Try associated label
            elem_id = element.get_attribute("id")
            if elem_id:
                try:
                    lbl = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{elem_id}']")
                    return lbl.text
                except:
                    pass
            
            # Try parent label
            try:
                parent = element.find_element(By.XPATH, "./ancestor::label")
                return parent.text
            except:
                pass
            
            # Try nearby text
            try:
                parent = element.find_element(By.XPATH, "./..")
                return parent.text[:100]
            except:
                pass
            
            return ""
        except:
            return ""
    
    def _get_answer(self, label):
        """Get answer for text field based on label"""
        label_lower = label.lower()
        
        # Name fields
        if any(x in label_lower for x in ['first name', 'full name', 'your name']):
            return USER_PROFILE["name"]
        if 'last name' in label_lower:
            return USER_PROFILE["name"].split()[-1]
        
        # Contact
        if 'email' in label_lower:
            return USER_PROFILE["email"]
        if 'phone' in label_lower or 'mobile' in label_lower:
            return USER_PROFILE["phone"]
        
        # Location
        if any(x in label_lower for x in ['city', 'location', 'address']):
            return USER_PROFILE["location"]
        
        # Links
        if 'linkedin' in label_lower:
            return USER_PROFILE["linkedin"]
        if 'github' in label_lower:
            return USER_PROFILE["github"]
        if 'website' in label_lower or 'portfolio' in label_lower:
            return USER_PROFILE["website"]
        
        # Experience - ALWAYS return 1 for any "years" or "experience" question
        if any(x in label_lower for x in ['years', 'experience', 'how long', 'how many']):
            return "1"
        
        # Salary - numbers only
        if any(x in label_lower for x in ['current ctc', 'current salary', 'present ctc', 'present salary']):
            return str(USER_PROFILE["current_ctc"])
        if any(x in label_lower for x in ['expected ctc', 'expected salary', 'desired salary']):
            return str(USER_PROFILE["expected_ctc"])
        if 'ctc' in label_lower or 'salary' in label_lower:
            return str(USER_PROFILE["expected_ctc"])
        
        # Notice period
        if 'notice' in label_lower:
            return str(USER_PROFILE["notice_period"])
        
        return None
    
    def _get_number_answer(self, label):
        """Get numeric answer"""
        label_lower = label.lower()
        
        # CTC/Salary
        if any(x in label_lower for x in ['current ctc', 'current salary', 'present']):
            return USER_PROFILE["current_ctc"]
        if any(x in label_lower for x in ['expected ctc', 'expected salary', 'desired']):
            return USER_PROFILE["expected_ctc"]
        if 'ctc' in label_lower or 'salary' in label_lower:
            return USER_PROFILE["expected_ctc"]
        
        # Notice period
        if 'notice' in label_lower:
            return USER_PROFILE["notice_period"]
        
        # Experience - always 1
        if any(x in label_lower for x in ['year', 'experience', 'how many', 'how long']):
            return 1
        
        # Default
        return 1
    
    def _pick_dropdown_option(self, label, options):
        """Pick best dropdown option"""
        label_lower = label.lower()
        
        # Yes/No questions - prefer Yes
        for opt in options:
            if opt.lower() in ['yes', 'true']:
                return opt
        
        # Experience level
        if 'experience' in label_lower:
            for opt in options:
                if '1' in opt or 'entry' in opt.lower() or 'junior' in opt.lower():
                    return opt
        
        # Education
        if 'education' in label_lower or 'degree' in label_lower:
            for opt in options:
                if "bachelor" in opt.lower():
                    return opt
        
        # Work authorization
        if 'authorized' in label_lower or 'authorization' in label_lower:
            for opt in options:
                if 'yes' in opt.lower():
                    return opt
        
        # Sponsorship - No
        if 'sponsor' in label_lower:
            for opt in options:
                if 'no' in opt.lower():
                    return opt
        
        # Default - first non-empty option
        return options[0] if options else ""
    
    def _safe_click(self, element):
        """Safely click an element"""
        try:
            element.click()
            return True
        except:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                return False
    
    def submit_application(self):
        """Navigate through application and submit"""
        max_pages = 10
        
        for page in range(max_pages):
            time.sleep(1)
            
            # Fill current page
            self.fill_form()
            
            # Look for buttons
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label], footer button")
                
                submit_btn = None
                next_btn = None
                review_btn = None
                
                for btn in buttons:
                    try:
                        text = (btn.text + " " + (btn.get_attribute("aria-label") or "")).lower()
                        
                        if 'submit' in text:
                            submit_btn = btn
                        elif 'next' in text or 'continue' in text:
                            next_btn = btn
                        elif 'review' in text:
                            review_btn = btn
                    except:
                        continue
                
                # Priority: Submit > Review > Next
                if submit_btn and submit_btn.is_enabled():
                    print("📤 Submitting application...", flush=True)
                    self._safe_click(submit_btn)
                    time.sleep(2)
                    
                    # Handle post-submit dialog
                    try:
                        dismiss = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Dismiss']")
                        dismiss.click()
                    except:
                        pass
                    
                    return True
                
                elif review_btn and review_btn.is_enabled():
                    print("📋 Going to review...", flush=True)
                    self._safe_click(review_btn)
                    time.sleep(1)
                
                elif next_btn and next_btn.is_enabled():
                    print("➡️ Next page...", flush=True)
                    self._safe_click(next_btn)
                    time.sleep(1)
                
                else:
                    print("⚠️ No navigation button found", flush=True)
                    break
                    
            except Exception as e:
                print(f"⚠️ Button error: {e}", flush=True)
                break
        
        return False
    
    def close_modal(self):
        """Close any open modal"""
        try:
            # Try dismiss button
            dismiss_selectors = [
                "button[aria-label*='Dismiss']",
                "button[aria-label*='dismiss']",
                ".artdeco-modal__dismiss",
                "button.artdeco-button--circle",
            ]
            
            for selector in dismiss_selectors:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(1)
                        return True
                except:
                    continue
            
            # Try pressing Escape
            try:
                webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
            except:
                pass
                
        except:
            pass
        
        return False
    
    def apply_to_job(self, card):
        """Apply to a single job"""
        try:
            # Click job card
            self._safe_click(card)
            time.sleep(2)
            
            # Get job title
            try:
                title = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title").text
                print(f"\n📌 Job: {title[:50]}", flush=True)
            except:
                title = "Unknown"
            
            # Click Easy Apply
            if not self.click_easy_apply():
                return False
            
            # Fill and submit
            if self.submit_application():
                print(f"✅ Applied successfully!", flush=True)
                self.applied += 1
                return True
            else:
                print(f"❌ Could not complete application", flush=True)
                self.close_modal()
                self.failed += 1
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}", flush=True)
            self.close_modal()
            self.failed += 1
            return False
    
    def run(self):
        """Main run loop"""
        print("\n" + "=" * 50, flush=True)
        print("🚀 STARTING BOT", flush=True)
        print("=" * 50, flush=True)
        
        if not self.start_browser():
            return
        
        if not self.login():
            print("❌ Login failed, exiting", flush=True)
            self.driver.quit()
            return
        
        # Search keywords (randomized on each start)
        searches = [
            ("MERN Stack Developer", "Kerala, India"),
            ("Backend Developer", "Kerala, India"),
            ("Node.js Developer", "Kerala, India"),
            ("Full Stack Developer", "Kerala, India"),
            ("Web Developer", "Kerala, India"),
            ("Software Engineer", "Kerala, India"),
            ("MERN Stack Developer", "India"),
            ("Backend Developer", "India"),
            ("Node.js Developer", "India"),
            ("Full Stack Developer", "India"),
            ("Web Developer", "India"),
            ("Software Engineer", "India"),
        ]
        # Shuffle to randomize search order on each start
        random.shuffle(searches)
        print(f"🎲 Randomized search order. Starting with: {searches[0][0]} in {searches[0][1]}", flush=True)
        
        try:
            for keyword, location in searches:
                self.search_jobs(keyword, location)
                
                cards = self.get_job_cards()
                
                for i, card in enumerate(cards[:10]):  # Limit to 10 per search
                    print(f"\n--- Job {i+1}/{min(len(cards), 10)} ---", flush=True)
                    
                    try:
                        self.apply_to_job(card)
                    except StaleElementReferenceException:
                        print("⚠️ Page changed, refreshing...", flush=True)
                        self.search_jobs(keyword, location)
                        break
                    except Exception as e:
                        print(f"⚠️ Error: {e}", flush=True)
                        continue
                    
                    # Random delay
                    time.sleep(random.uniform(3, 6))
                
                time.sleep(5)
        
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user", flush=True)
        
        finally:
            print("\n" + "=" * 50, flush=True)
            print("📊 RESULTS", flush=True)
            print(f"   ✅ Applied: {self.applied}", flush=True)
            print(f"   ❌ Failed: {self.failed}", flush=True)
            print("=" * 50, flush=True)
            
            try:
                self.driver.quit()
            except:
                pass


if __name__ == "__main__":
    bot = SimpleLinkedInBot()
    bot.run()
