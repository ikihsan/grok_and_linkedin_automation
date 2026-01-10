"""
Website Pinger - Visits your website every minute (2 times per minute)
Keeps free hosting services (Render, Vercel, Railway, etc.) alive
"""

import requests
import time
import sys
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
WEBSITES = [
    "https://github.com/ikihsan",
    "https://ikihsan.me",
    "https://ikihsan.tech",
    # Add more URLs here
]

VISITS_PER_MINUTE = 2
INTERVAL = 60 / VISITS_PER_MINUTE  # 30 seconds between visits


def log(msg: str):
    """Simple print with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} - {msg}", flush=True)


def ping_website(url: str) -> dict:
    """Ping a single website and return status"""
    try:
        start = time.time()
        response = requests.get(
            url,
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        elapsed = round((time.time() - start) * 1000)  # ms
        
        return {
            'url': url,
            'status': response.status_code,
            'time_ms': elapsed,
            'success': response.status_code == 200
        }
    except requests.exceptions.Timeout:
        return {'url': url, 'status': 'TIMEOUT', 'time_ms': 0, 'success': False}
    except requests.exceptions.ConnectionError:
        return {'url': url, 'status': 'CONNECTION_ERROR', 'time_ms': 0, 'success': False}
    except Exception as e:
        return {'url': url, 'status': str(e), 'time_ms': 0, 'success': False}


def ping_all_websites():
    """Ping all websites concurrently"""
    with ThreadPoolExecutor(max_workers=len(WEBSITES)) as executor:
        results = list(executor.map(ping_website, WEBSITES))
    
    for result in results:
        if result['success']:
            log(f"[OK] {result['url']} - {result['status']} ({result['time_ms']}ms)")
        else:
            log(f"[FAIL] {result['url']} - {result['status']}")
    
    return results


def main():
    """Main loop - runs forever"""
    log("=" * 50)
    log("Website Pinger Started")
    log(f"Websites: {', '.join(WEBSITES)}")
    log(f"Visiting {VISITS_PER_MINUTE}x per minute (every {INTERVAL}s)")
    log("=" * 50)
    
    visit_count = 0
    
    try:
        while True:
            visit_count += 1
            log(f"\n--- Visit #{visit_count} at {datetime.now().strftime('%H:%M:%S')} ---")
            
            ping_all_websites()
            
            time.sleep(INTERVAL)
            
    except KeyboardInterrupt:
        log("\nPinger stopped by user")
    except Exception as e:
        log(f"Error: {e}")


if __name__ == "__main__":
    main()
