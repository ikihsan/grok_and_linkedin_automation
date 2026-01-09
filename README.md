# Autonomous Job Application Agent

## Overview
This is a fully autonomous job application agent that:
- Operates continuously without human input
- Uses USER_PROFILE as the single source of truth
- Never invents, exaggerates, or hallucinates experience
- Applies to jobs matching your criteria
- Logs all applications to prevent duplicates

## Setup

### 1. Install Dependencies
```bash
cd auto_job_agent
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Windows
set LINKEDIN_PASSWORD=your_linkedin_password

# Linux/Mac
export LINKEDIN_PASSWORD=your_linkedin_password
```

### 3. Update User Profile
Edit `config.py` to update your:
- Personal information
- Work experience
- Education
- Skills
- Job preferences

### 4. Add Resume
Create folder structure:
```
auto_job_agent/
├── assets/
│   └── resumes/
│       ├── resume_default.pdf
│       └── resume_technical.pdf
```

## Running the Agent

### Full Autonomous Mode
```bash
python main.py
```

### LinkedIn Only Mode
```bash
python main.py --linkedin-only
```

## Configuration

### Job Matching Criteria (`config.py`)
- **required_titles**: Job titles to apply for
- **required_tech_stack**: Technologies that must match (60% threshold)
- **exclusions**: Titles and keywords to avoid

### Rate Limits
- **applications_per_day**: 50 (default)
- **min_delay_between_apps**: 30 seconds
- **max_delay_between_apps**: 120 seconds

## Features

### Platforms Supported
1. **LinkedIn Easy Apply** - Direct applications
2. **External ATS** - Greenhouse, Lever, Ashby, Workday

### Form Filling
The agent intelligently fills:
- Personal information
- Work experience
- Education
- Skills
- Common questions (EEO, work authorization, etc.)

### Duplicate Prevention
All applications are logged to `data/applications.json` to prevent:
- Re-applying to the same job
- Exceeding daily limits

## File Structure
```
auto_job_agent/
├── main.py              # Entry point
├── config.py            # Configuration & USER_PROFILE
├── form_filler.py       # Intelligent form filling
├── browser_manager.py   # Browser automation
├── application_logger.py # Application tracking
├── platforms/
│   ├── linkedin_easy_apply.py  # LinkedIn handler
│   └── external_ats.py         # External ATS handler
├── data/
│   └── applications.json       # Application log
└── assets/
    └── resumes/
```

## Safety Features
- Human-like typing and clicking delays
- Random pauses between applications
- Anti-detection measures
- Rate limiting
- Graceful shutdown (Ctrl+C)

## Important Notes
1. **Never share your credentials** - Use environment variables
2. **Review applications** - Check the log regularly
3. **Respect rate limits** - Don't modify limits to avoid bans
4. **Keep profile accurate** - Never exaggerate experience

## Troubleshooting

### Login Issues
- Check credentials in environment variables
- Complete CAPTCHA/security checks manually when prompted
- Ensure LinkedIn account is in good standing

### Form Filling Issues
- Check browser console for errors
- Update selectors if LinkedIn changes their UI
- Verify USER_PROFILE data is correct

### Application Not Submitting
- Check for required fields
- Verify resume file exists
- Review error messages in console
