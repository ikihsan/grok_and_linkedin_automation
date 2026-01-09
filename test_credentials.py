"""
Test script to verify credentials are loading correctly from .env
"""

import os
from pathlib import Path

print("=" * 50)
print("CREDENTIALS TEST")
print("=" * 50)

# Load .env file manually
env_file = Path(__file__).parent / ".env"

print(f"\n📂 .env file path: {env_file}")
print(f"📄 .env exists: {env_file.exists()}")

if env_file.exists():
    print("\n📝 Contents of .env file:")
    with open(env_file, 'r') as f:
        for i, line in enumerate(f.readlines(), 1):
            line = line.strip()
            if line and not line.startswith("#"):
                if "PASSWORD" in line.upper():
                    key = line.split("=")[0]
                    print(f"   {i}: {key}=********")
                else:
                    print(f"   {i}: {line}")

# Now load them into environment
print("\n🔄 Loading .env into environment...")
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                value = value.strip()
                if value:
                    os.environ[key] = value

# Check what's in environment now
print("\n🔍 Environment variables after loading:")
print(f"   LINKEDIN_EMAIL = {os.getenv('LINKEDIN_EMAIL', 'NOT SET')}")
print(f"   LINKEDIN_PASSWORD = {'*' * len(os.getenv('LINKEDIN_PASSWORD', ''))} ({len(os.getenv('LINKEDIN_PASSWORD', ''))} chars)" if os.getenv('LINKEDIN_PASSWORD') else "   LINKEDIN_PASSWORD = NOT SET")
print(f"   GROQ_API_KEY = {os.getenv('GROQ_API_KEY', 'NOT SET')[:20]}..." if os.getenv('GROQ_API_KEY') else "   GROQ_API_KEY = NOT SET")

# Verify expected values
print("\n✅ VERIFICATION:")
expected_email = "ikihsaan@gmail.com"
expected_password = "Ihsan@987"

actual_email = os.getenv('LINKEDIN_EMAIL', '')
actual_password = os.getenv('LINKEDIN_PASSWORD', '')

if actual_email == expected_email:
    print(f"   ✅ Email is correct: {actual_email}")
else:
    print(f"   ❌ Email MISMATCH!")
    print(f"      Expected: {expected_email}")
    print(f"      Got: {actual_email}")

if actual_password == expected_password:
    print(f"   ✅ Password is correct (length: {len(actual_password)})")
else:
    print(f"   ❌ Password MISMATCH!")
    print(f"      Expected length: {len(expected_password)}")
    print(f"      Got length: {len(actual_password)}")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)
