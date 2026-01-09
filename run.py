"""
Quick Start Script
Run this to start the Ultimate LinkedIn Bot with AI form filling
"""

import os
import sys
from pathlib import Path

# Force unbuffered output so we see print statements immediately
sys.stdout.reconfigure(line_buffering=True)

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent))

# Load .env FIRST before any other imports
env_file = Path(__file__).parent / ".env"
env_vars = {}

print("📂 Loading .env file...", flush=True)

if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                value = value.strip()
                if value and not value.startswith("your"):
                    os.environ[key] = value
                    env_vars[key] = value
                    if 'PASSWORD' not in key:
                        print(f"   ✅ {key} = {value[:30]}...", flush=True)
                    else:
                        print(f"   ✅ {key} = ********")
else:
    print("   ⚠️ .env file not found!")

print()


def save_to_env(key: str, value: str):
    """Save a key to .env file"""
    env_vars[key] = value
    with open(env_file, "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")
    print(f"   ✅ Saved to .env for future use")


def main():
    print("\n" + "="*60)
    print("🚀 AUTO JOB APPLICATION BOT - QUICK START")
    print("="*60)
    
    # Check LinkedIn credentials
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email or email.startswith("your"):
        print("\n📧 LinkedIn Email:")
        email = input("   > ").strip()
        os.environ["LINKEDIN_EMAIL"] = email
        save_to_env("LINKEDIN_EMAIL", email)
    else:
        print(f"\n📧 LinkedIn Email: {email}")
    
    if not password or password.startswith("your"):
        print("\n🔑 LinkedIn Password:")
        password = input("   > ").strip()
        os.environ["LINKEDIN_PASSWORD"] = password
        save_to_env("LINKEDIN_PASSWORD", password)
    else:
        print("🔑 LinkedIn Password: ********")
    
    # Check AI keys
    print("\n" + "-"*40)
    print("🤖 AI API KEY STATUS:")
    print("-"*40)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if openai_key and not openai_key.startswith("sk-your"):
        print("✅ OpenAI API Key: Found (will use GPT-4o-mini)")
    elif groq_key and not groq_key.startswith("gsk_your"):
        print("✅ Groq API Key: Found (FREE - will use Llama 3.1)")
    elif gemini_key and not gemini_key.startswith("your"):
        print("✅ Gemini API Key: Found (FREE)")
    else:
        print("⚠️  No AI API key found - using rule-based filling")
        print("\n   Want to add a FREE AI key? (Groq is recommended)")
        print("   Get one at: https://console.groq.com/")
        
        add_key = input("\n   Enter Groq API key (or press Enter to skip): ").strip()
        if add_key:
            os.environ["GROQ_API_KEY"] = add_key
            save_to_env("GROQ_API_KEY", add_key)
            print("   ✅ Groq key added!", flush=True)
    
    print("\n" + "="*60, flush=True)
    print("🎯 Starting bot...", flush=True)
    print("="*60 + "\n", flush=True)
    
    # Import and run the V2 bot with full debugging
    print("📦 Importing modules...", flush=True)
    from linkedin_bot_v2 import LinkedInBotV2
    print("   ✅ Modules imported!", flush=True)
    
    print("🤖 Creating bot instance...", flush=True)
    bot = LinkedInBotV2()
    print("   ✅ Bot created!", flush=True)
    
    print("▶️ Starting bot.run()...", flush=True)
    bot.run()


if __name__ == "__main__":
    main()