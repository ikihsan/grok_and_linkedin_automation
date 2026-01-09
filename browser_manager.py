"""
Browser Manager
Handles browser automation with anti-detection and human-like behavior
"""

import os
import time
import random
from typing import List, Optional, Tuple
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementClickInterceptedException, StaleElementReferenceException
)

from config import RATE_LIMITS


class BrowserManager:
    """
    Manages browser instance with human-like behavior to avoid detection.
    Uses Selenium with various anti-detection measures.
    """
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.is_started = False
    
    def start(self, headless: bool = False) -> bool:
        """Start browser with anti-detection settings"""
        try:
            options = Options()
            
            # Basic settings
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Disable automation flags
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            
            # User agent
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
            
            if headless:
                options.add_argument("--headless=new")
            
            # Try different Chrome paths
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\Application\chrome.exe",
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    options.binary_location = chrome_path
                    break
            
            # Create driver using system chromedriver
            self.driver = webdriver.Chrome(options=options)
            
            # Anti-detection: Remove webdriver flag
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        window.navigator.chrome = {
                            runtime: {},
                        };
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5],
                        });
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en'],
                        });
                    """
                }
            )
            
            self.wait = WebDriverWait(self.driver, 10)
            self.is_started = True
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
        self.is_started = False
    
    def goto(self, url: str, wait_time: float = None):
        """Navigate to URL with random delay"""
        if wait_time is None:
            wait_time = RATE_LIMITS["page_load_wait"]
        
        self.driver.get(url)
        time.sleep(wait_time + random.uniform(0, 1))
    
    def human_type(self, element, text: str, clear_first: bool = True):
        """Type text with human-like delays"""
        if clear_first:
            element.clear()
        
        for char in text:
            element.send_keys(char)
            delay = random.uniform(*RATE_LIMITS["human_typing_delay"])
            time.sleep(delay)
    
    def human_click(self, element):
        """Click element with human-like behavior"""
        try:
            # Scroll element into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(random.uniform(0.2, 0.5))
            
            # Move to element and click
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()
            
        except ElementClickInterceptedException:
            # JavaScript click as fallback
            self.driver.execute_script("arguments[0].click();", element)
    
    def find_element(self, by: By, value: str, timeout: float = 5) -> Optional:
        """Find element with wait"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            return None
    
    def find_elements(self, by: By, value: str) -> List:
        """Find all matching elements"""
        try:
            return self.driver.find_elements(by, value)
        except:
            return []
    
    def is_visible(self, by: By, value: str, timeout: float = 3) -> bool:
        """Check if element is visible"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            return False
    
    def scroll_slow(self, element=None, distance: int = 500, reverse: bool = False):
        """Scroll slowly like human"""
        if element:
            scroll_script = f"arguments[0].scrollBy(0, {-distance if reverse else distance});"
            self.driver.execute_script(scroll_script, element)
        else:
            scroll_script = f"window.scrollBy(0, {-distance if reverse else distance});"
            self.driver.execute_script(scroll_script)
        
        time.sleep(random.uniform(0.5, 1))
    
    def random_delay(self, min_sec: float = 1, max_sec: float = 3):
        """Add random delay to appear human"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def fill_input(self, element, value: str):
        """Fill input field"""
        try:
            element.click()
            time.sleep(0.1)
            element.clear()
            self.human_type(element, str(value))
            return True
        except:
            return False
    
    def select_dropdown(self, element, value: str) -> bool:
        """Select dropdown option by visible text"""
        try:
            select = Select(element)
            select.select_by_visible_text(value)
            return True
        except:
            # Try partial match
            try:
                select = Select(element)
                for option in select.options:
                    if value.lower() in option.text.lower():
                        select.select_by_visible_text(option.text)
                        return True
            except:
                pass
            return False
    
    def click_radio(self, element) -> bool:
        """Click radio button"""
        try:
            if not element.is_selected():
                self.human_click(element)
            return True
        except:
            return False
    
    def upload_file(self, input_element, file_path: str) -> bool:
        """Upload file to input element"""
        try:
            if os.path.exists(file_path):
                input_element.send_keys(file_path)
                return True
        except:
            pass
        return False
    
    def get_page_source(self) -> str:
        """Get current page source"""
        return self.driver.page_source
    
    def get_current_url(self) -> str:
        """Get current URL"""
        return self.driver.current_url
    
    def switch_to_frame(self, frame):
        """Switch to iframe"""
        self.driver.switch_to.frame(frame)
    
    def switch_to_default(self):
        """Switch back to main content"""
        self.driver.switch_to.default_content()


# Export singleton
browser = BrowserManager()
