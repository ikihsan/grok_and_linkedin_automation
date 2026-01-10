"""
Selenium Website Visitor - Opens links in real browser
Visits 20+ times per minute using actual browser instances
"""

import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
WEBSITES = [
    "https://github.com/ikihsan",
    # Add more URLs here
]

VISITS_PER_MINUTE = 20
INTERVAL = 60 / VISITS_PER_MINUTE  # 3 seconds between visits


def log(msg: str):
    """Print with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} - {msg}", flush=True)


def get_driver():
    """Create a new Chrome driver instance"""
    options = Options()
    
    # Make it look more human-like
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Random window size
    width = random.randint(1200, 1920)
    height = random.randint(800, 1080)
    options.add_argument(f'--window-size={width},{height}')
    
    # Other options
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Uncomment to run headless (invisible browser)
    # options.add_argument('--headless=new')
    
    driver = webdriver.Chrome(options=options)
    
    # Remove webdriver flag
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def visit_website(url: str):
    """Visit a website with real browser"""
    driver = None
    try:
        driver = get_driver()
        
        # Navigate to the page
        driver.get(url)
        
        # Wait for page to load
        time.sleep(random.uniform(2, 4))
        
        # Scroll down randomly to simulate reading
        scroll_amount = random.randint(100, 500)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
        
        time.sleep(random.uniform(1, 2))
        
        # Scroll back up
        driver.execute_script("window.scrollTo(0, 0)")
        
        time.sleep(random.uniform(0.5, 1))
        
        log(f"[OK] Visited {url}")
        return True
        
    except Exception as e:
        log(f"[FAIL] {url} - {e}")
        return False
        
    finally:
        if driver:
            driver.quit()


def visit_website_reuse_driver(driver, url: str):
    """Visit website reusing existing driver (faster)"""
    try:
        driver.get(url)
        time.sleep(random.uniform(1, 2))
        
        # Random scroll
        scroll_amount = random.randint(100, 500)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
        time.sleep(random.uniform(0.5, 1))
        
        log(f"[OK] Visited {url}")
        return True
    except Exception as e:
        log(f"[FAIL] {url} - {e}")
        return False


def main():
    """Main loop - visits websites continuously"""
    log("=" * 50)
    log("Selenium Website Visitor Started")
    log(f"Target: {', '.join(WEBSITES)}")
    log(f"Speed: {VISITS_PER_MINUTE} visits/minute (every {INTERVAL:.1f}s)")
    log("=" * 50)
    
    visit_count = 0
    
    # Create single driver instance for speed
    driver = None
    
    try:
        driver = get_driver()
        
        while True:
            for url in WEBSITES:
                visit_count += 1
                log(f"\n--- Visit #{visit_count} ---")
                
                visit_website_reuse_driver(driver, url)
                
                # Wait before next visit
                wait_time = INTERVAL + random.uniform(-0.5, 0.5)
                time.sleep(max(1, wait_time))
                
    except KeyboardInterrupt:
        log("\nVisitor stopped by user")
    except Exception as e:
        log(f"Error: {e}")
    finally:
        if driver:
            driver.quit()
            log("Browser closed")


def main_new_browser_each_visit():
    """Alternative: New browser for each visit (slower but more unique)"""
    log("=" * 50)
    log("Selenium Visitor (New Browser Each Visit)")
    log(f"Target: {', '.join(WEBSITES)}")
    log("=" * 50)
    
    visit_count = 0
    
    try:
        while True:
            for url in WEBSITES:
                visit_count += 1
                log(f"\n--- Visit #{visit_count} ---")
                
                visit_website(url)
                
                time.sleep(INTERVAL)
                
    except KeyboardInterrupt:
        log("\nVisitor stopped by user")


if __name__ == "__main__":
    # Default: Reuse browser (fast, 20+ visits/min)
    main()
    
    # Alternative: New browser each time (slower, more "unique")
    # main_new_browser_each_visit()
