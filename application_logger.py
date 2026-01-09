"""
Application Logger
Maintains internal log of all job applications - no duplicates allowed.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ApplicationLogger:
    """
    Tracks all job applications to prevent duplicates.
    Maintains persistent log across sessions.
    """
    
    def __init__(self, log_dir: str = "data"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.log_file = self.log_dir / "applications.json"
        self.applied_jobs_file = self.log_dir / "applied_jobs.txt"
        
        self.applications: List[Dict] = []
        self.applied_urls: set = set()
        
        self._load_log()
    
    def _load_log(self):
        """Load existing log from file"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.applications = json.load(f)
                    # Build set of applied URLs
                    self.applied_urls = {app["url"] for app in self.applications}
        except Exception as e:
            print(f"Warning: Could not load application log: {e}")
            self.applications = []
            self.applied_urls = set()
    
    def _save_log(self):
        """Save log to file"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.applications, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save application log: {e}")
    
    def has_applied(self, url: str) -> bool:
        """Check if already applied to this job"""
        # Normalize URL
        normalized = url.split('?')[0].rstrip('/')
        return normalized in self.applied_urls
    
    def log_application(
        self,
        company: str,
        role: str,
        url: str,
        platform: str,
        resume_used: str = "default",
        status: str = "submitted",
        notes: str = ""
    ) -> bool:
        """
        Log a job application.
        Returns True if logged successfully, False if duplicate.
        """
        # Normalize URL
        normalized_url = url.split('?')[0].rstrip('/')
        
        # Check duplicate
        if normalized_url in self.applied_urls:
            return False
        
        # Create log entry
        entry = {
            "company": company,
            "role": role,
            "url": normalized_url,
            "platform": platform,
            "resume_used": resume_used,
            "status": status,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        self.applications.append(entry)
        self.applied_urls.add(normalized_url)
        
        self._save_log()
        
        # Also append to simple text file for quick reference
        try:
            with open(self.applied_jobs_file, 'a', encoding='utf-8') as f:
                f.write(f"{entry['date']} | {company} | {role} | {platform}\n")
        except:
            pass
        
        return True
    
    def get_today_count(self) -> int:
        """Get number of applications submitted today"""
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(1 for app in self.applications if app.get("date") == today)
    
    def get_total_count(self) -> int:
        """Get total number of applications"""
        return len(self.applications)
    
    def get_recent_applications(self, limit: int = 10) -> List[Dict]:
        """Get most recent applications"""
        return sorted(
            self.applications,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
    
    def get_applications_by_platform(self, platform: str) -> List[Dict]:
        """Get applications filtered by platform"""
        return [app for app in self.applications if app.get("platform") == platform]
    
    def get_statistics(self) -> Dict:
        """Get application statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Count by platform
        by_platform = {}
        for app in self.applications:
            platform = app.get("platform", "unknown")
            by_platform[platform] = by_platform.get(platform, 0) + 1
        
        # Count by status
        by_status = {}
        for app in self.applications:
            status = app.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total": len(self.applications),
            "today": sum(1 for app in self.applications if app.get("date") == today),
            "by_platform": by_platform,
            "by_status": by_status,
        }
    
    def update_status(self, url: str, status: str, notes: str = ""):
        """Update status of an application"""
        normalized = url.split('?')[0].rstrip('/')
        
        for app in self.applications:
            if app.get("url") == normalized:
                app["status"] = status
                if notes:
                    app["notes"] = notes
                app["updated_at"] = datetime.now().isoformat()
                break
        
        self._save_log()
    
    def print_summary(self):
        """Print summary of applications"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("📊 APPLICATION SUMMARY")
        print("="*50)
        print(f"Total Applications: {stats['total']}")
        print(f"Applied Today: {stats['today']}")
        print("\nBy Platform:")
        for platform, count in stats['by_platform'].items():
            print(f"  - {platform}: {count}")
        print("\nBy Status:")
        for status, count in stats['by_status'].items():
            print(f"  - {status}: {count}")
        print("="*50 + "\n")


# Export singleton
app_logger = ApplicationLogger()
