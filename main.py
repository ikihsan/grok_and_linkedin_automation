"""
========================================
AUTONOMOUS JOB APPLICATION AGENT
========================================

This agent operates CONTINUOUSLY without human input.
Single source of truth: USER_PROFILE
Never invents, exaggerates, or hallucinates experience.

Run with: python main.py

The agent will:
1. Login to job platforms
2. Search for matching jobs
3. Apply automatically to matching positions
4. Log all applications (never duplicate)
5. Respect rate limits and behave human-like
"""

import os
import sys
import time
import random
import signal
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    USER_PROFILE, 
    JOB_CRITERIA, 
    PLATFORM_CONFIG, 
    RATE_LIMITS,
    check_job_match,
    get_experience_years,
)
from browser_manager import BrowserManager
from application_logger import app_logger
from platforms import LinkedInEasyApply, ExternalATSHandler


class AutonomousJobAgent:
    """
    Main autonomous job application agent.
    Operates continuously, applying to jobs across multiple platforms.
    """
    
    def __init__(self):
        self.browser = None
        self.linkedin = None
        self.external_ats = None
        self.running = False
        self.start_time = None
        
        # Statistics
        self.total_applied = 0
        self.total_skipped = 0
        self.total_failed = 0
        self.session_start = datetime.now()
    
    def start(self):
        """Initialize and start the agent"""
        print("\n" + "="*60)
        print("🤖 AUTONOMOUS JOB APPLICATION AGENT")
        print("="*60)
        print(f"📅 Session started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 Profile: {USER_PROFILE['personal']['full_name']}")
        print(f"📧 Email: {USER_PROFILE['personal']['email']}")
        print(f"💼 Experience: {get_experience_years()} years")
        print(f"🎯 Target roles: {', '.join(JOB_CRITERIA['required_titles'][:3])}...")
        print(f"📊 Daily limit: {RATE_LIMITS['applications_per_day']} applications")
        print("="*60 + "\n")
        
        # Initialize browser
        print("🌐 Starting browser...")
        self.browser = BrowserManager()
        
        if not self.browser.start(headless=False):
            print("❌ Failed to start browser!")
            return False
        
        print("✅ Browser started!\n")
        
        # Initialize platform handlers
        self.linkedin = LinkedInEasyApply(self.browser)
        self.external_ats = ExternalATSHandler(self.browser)
        
        self.running = True
        self.start_time = time.time()
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        
        return True
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signal"""
        print("\n\n🛑 Shutdown signal received...")
        self.stop()
    
    def stop(self):
        """Stop the agent gracefully"""
        self.running = False
        print("\n🛑 Stopping agent...")
        
        # Print final statistics
        self._print_session_summary()
        
        # Close browser
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        
        print("✅ Agent stopped.\n")
    
    def run(self):
        """Main run loop - operates continuously"""
        if not self.start():
            return
        
        print("🚀 Starting autonomous job application process...\n")
        
        try:
            while self.running:
                # Check daily limit
                today_count = app_logger.get_today_count()
                
                if today_count >= RATE_LIMITS["applications_per_day"]:
                    print(f"\n📊 Daily limit reached ({today_count}/{RATE_LIMITS['applications_per_day']})")
                    print("⏸️  Waiting for next day...")
                    
                    # Wait until midnight
                    self._wait_until_midnight()
                    continue
                
                # Run LinkedIn Easy Apply
                if PLATFORM_CONFIG["discovery_platforms"]["linkedin"]["enabled"]:
                    print("\n" + "-"*40)
                    print("🔵 LINKEDIN EASY APPLY")
                    print("-"*40 + "\n")
                    
                    try:
                        self.linkedin.start_applying()
                    except Exception as e:
                        print(f"❌ LinkedIn error: {e}")
                
                # Update statistics
                self._update_statistics()
                
                # Human-like break between platforms
                if self.running:
                    break_time = random.randint(60, 300)  # 1-5 minutes
                    print(f"\n☕ Taking a break for {break_time // 60} minutes...")
                    time.sleep(break_time)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def run_linkedin_only(self):
        """Run only LinkedIn Easy Apply"""
        if not self.start():
            return
        
        print("🚀 Starting LinkedIn Easy Apply...\n")
        
        try:
            self.linkedin.start_applying()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.stop()
    
    def _update_statistics(self):
        """Update session statistics"""
        if self.linkedin:
            self.total_applied = self.linkedin.applied_count
            self.total_skipped = self.linkedin.skipped_count
            self.total_failed = self.linkedin.failed_count
    
    def _wait_until_midnight(self):
        """Wait until midnight to reset daily counter"""
        now = datetime.now()
        tomorrow = datetime(now.year, now.month, now.day + 1)
        seconds_until_midnight = (tomorrow - now).total_seconds()
        
        # Add some random buffer
        wait_time = seconds_until_midnight + random.randint(60, 3600)
        
        print(f"⏳ Resuming in {int(wait_time // 3600)} hours...")
        time.sleep(wait_time)
    
    def _print_session_summary(self):
        """Print session summary"""
        duration = time.time() - (self.start_time or time.time())
        
        print("\n" + "="*60)
        print("📊 SESSION SUMMARY")
        print("="*60)
        print(f"⏱️  Duration: {int(duration // 3600)}h {int((duration % 3600) // 60)}m")
        print(f"✅ Applied: {self.total_applied}")
        print(f"⏭️  Skipped: {self.total_skipped}")
        print(f"❌ Failed: {self.total_failed}")
        print(f"📝 Today's total: {app_logger.get_today_count()}")
        print(f"📈 All-time total: {app_logger.get_total_count()}")
        print("="*60)
        
        # Print recent applications
        recent = app_logger.get_recent_applications(5)
        if recent:
            print("\n📋 Recent applications:")
            for app in recent:
                print(f"   - {app['company']}: {app['role']} ({app['platform']})")
        
        print()


def main():
    """Main entry point"""
    # Check for password in environment
    if not os.getenv("LINKEDIN_PASSWORD"):
        print("\n⚠️  LINKEDIN_PASSWORD environment variable not set!")
        print("Set it with: set LINKEDIN_PASSWORD=your_password")
        
        # Prompt for password
        password = input("Enter LinkedIn password (or press Enter to skip): ").strip()
        if password:
            os.environ["LINKEDIN_PASSWORD"] = password
        else:
            print("❌ Password required to login. Exiting.")
            return
    
    # Create and run agent
    agent = AutonomousJobAgent()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--linkedin-only":
        agent.run_linkedin_only()
    else:
        agent.run()


if __name__ == "__main__":
    main()
