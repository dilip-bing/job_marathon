# 🤖 Job Application Automation System

**Intelligent AI-powered job application automation using browser-use and LangChain**

Automate your job applications with tailored resumes and cover letters, all powered by AI agents!

---

## 📋 Table of Contents

- [Features](#-features)
- [How It Works](#-how-it-works)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Detailed Workflow](#-detailed-workflow)
- [Logs & Monitoring](#-logs--monitoring)
- [Troubleshooting](#-troubleshooting)
- [Security](#-security)
- [Future Enhancements](#-future-enhancements)

---

## ✨ Features

- 🔍 **Intelligent Job Scraping** - AI agent extracts complete job descriptions from any URL
- 📄 **Tailored Resume Generation** - API creates ATS-optimized resumes with 95%+ keyword matching
- ✉️ **Custom Cover Letters** - AI-generated cover letters personalized for each job
- 🤖 **Smart Form Filling** - Browser automation fills out application forms using your profile
- 📊 **Detailed Logging** - Every step logged with timestamps and status tracking
- 🔄 **Parallel Processing** - Resume and cover letter generated simultaneously for speed
- 💾 **Application History** - All applications tracked in JSON log file
- 🛡️ **Error Handling** - Robust retry logic and error recovery

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    JOB APPLICATION WORKFLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. Input Job URL
        ↓
2. Scrape Job Description (browser-use AI agent)
        ↓
3. Generate Documents in Parallel
   ├── Tailored Resume (Resume API)
   └── Custom Cover Letter (Resume API)
        ↓
4. Fill Application Form (browser-use AI agent)
   ├── Personal Information
   ├── Work Experience
   ├── Upload Resume
   └── Upload Cover Letter
        ↓
5. Review (Manual) → Submit (Manual for now)
        ↓
6. Log Application Status
```

---

## 📦 Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** installed
- **Google Gemini API Key** (free tier available)
- **Resume API Access** (already configured in code)
- **Internet Connection** for API calls and browser automation

---

## 🚀 Installation

### Step 1: Clone or Download This Repository

```powershell
cd C:\Users\dilip\job_marathon
```

### Step 2: Create Virtual Environment (Recommended)

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Install Playwright Browsers

```powershell
playwright install
```

This downloads the necessary browser binaries for automation.

---

## ⚙️ Configuration

### 1. Review User Profile

Open `user_profile.json` and update with your information:

```json
{
  "personal_info": {
    "full_name": "Your Name",
    "email": "your.email@example.com",
    "phone": "+1-234-567-8900"
    // ... update all fields
  }
  // ... update all sections
}
```

**Important Fields to Update:**
- ✅ `personal_info` - Name, email, phone, LinkedIn, GitHub
- ✅ `address` - Current address
- ✅ `education` - Degrees and universities
- ✅ `work_experience` - All previous jobs
- ✅ `skills` - Programming languages, frameworks, tools
- ✅ `preferences` - Salary expectations, remote preference

### 2. Verify API Keys

The API keys are already configured in `config.py`:
- ✅ Resume API Key: Already set
- ✅ Gemini API Key: Already set

If you want to use environment variables instead:

```powershell
# Copy example env file
cp .env.example .env

# Edit .env with your keys (optional)
```

---

## 🎯 Usage

### Quick Start

1. **Open the main script**

   Open `job_application_automation.py` and find the `main()` function at the bottom

2. **Set Your Job URL**

   ```python
   async def main():
       # Replace this with your actual job URL
       JOB_URL = "https://careers.company.com/jobs/123456"
   ```

3. **Run the automation**

   ```powershell
   python job_application_automation.py
   ```

### What Happens Next

1. ✅ **User Profile Loaded** - Your information is loaded from `user_profile.json`

2. ✅ **Job Description Scraped** - Browser opens and AI agent extracts job details

3. ✅ **Documents Generated** (parallel)
   - Tailored resume created (may take 30-120 seconds)
   - Custom cover letter created (may take 30-120 seconds)

4. ✅ **Form Filled** - Browser navigates to job URL, clicks Apply, fills form
   - Personal information entered
   - Files uploaded
   - ⚠️ **NOT SUBMITTED** - You review and submit manually

5. ✅ **Log Saved** - Application status saved to `logs/application_log.json`

### Example Output

```
════════════════════════════════════════════════════════════════════
JOB APPLICATION AUTOMATION SYSTEM - STARTED
════════════════════════════════════════════════════════════════════

STEP 1: SCRAPE JOB DESCRIPTION
────────────────────────────────────────────────────────────────────
Target URL: https://careers.company.com/jobs/123456
Initializing browser-use agent...
✅ Gemini LLM initialized (model: gemini-2.0-flash-exp)
🤖 Agent created, starting browser automation...
✅ Job description extracted successfully
   Length: 2453 characters

STEP 2 & 3: GENERATING DOCUMENTS IN PARALLEL
────────────────────────────────────────────────────────────────────
⚡ Starting parallel document generation...
✅ API response received
   Match Score: 95-98%
   Keywords Added: 23
✅ Resume saved: generated_documents/resume_tailored_20260211_143022.docx
✅ Cover letter saved: generated_documents/cover_letter_20260211_143025.docx

STEP 5-9: FILLING APPLICATION FORM
────────────────────────────────────────────────────────────────────
🤖 Agent created, starting form filling automation...
✅ Form filling completed
⚠️  IMPORTANT: Form is filled but NOT submitted

════════════════════════════════════════════════════════════════════
✅ JOB APPLICATION AUTOMATION COMPLETED
════════════════════════════════════════════════════════════════════

📊 SUMMARY:
   ✅ Job description scraped
   ✅ Resume generated: generated_documents/resume_tailored_20260211_143022.docx
   ✅ Cover letter generated: generated_documents/cover_letter_20260211_143025.docx
   ✅ Application form filled (NOT SUBMITTED)

⚠️  NEXT STEPS:
   1. Review the filled form in the browser
   2. Verify all information is correct
   3. Manually click Submit when ready
```

---

## 📁 Project Structure

```
job_marathon/
│
├── job_application_automation.py  # Main automation script
├── config.py                       # Configuration settings
├── utils.py                        # Helper functions
├── user_profile.json               # Your personal information (EDIT THIS!)
│
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore file
├── README.md                       # This file
│
├── generated_documents/            # Generated resumes & cover letters
│   ├── resume_tailored_*.docx
│   └── cover_letter_*.docx
│
└── logs/                           # Application logs
    ├── automation_*.log            # Detailed execution logs
    └── application_log.json        # Application history
```

---

## 🔍 Detailed Workflow

### Step 1: Scrape Job Description

```python
# Uses browser-use AI agent with Google Gemini
# Opens browser, navigates to job URL
# Extracts complete job description using AI
```

**Model Used:** `gemini-2.0-flash-exp` (faster for scraping)

### Step 2: Generate Resume

```python
# Calls Resume Optimizer API
# Sends job description
# Receives ATS-optimized resume with keyword matching
# Saves as .docx file
```

**API:** `https://resume-optimizer-api-fvpd.onrender.com/api/v1/optimize`

### Step 3: Generate Cover Letter

```python
# Calls Cover Letter API (runs in parallel with Step 2)
# Sends job description + applicant info
# Receives personalized cover letter
# Saves as .docx file
```

**API:** `https://resume-optimizer-api-fvpd.onrender.com/api/v1/generate-cover-letter`

### Step 4-9: Fill Application Form

```python
# Uses browser-use AI agent with Google Gemini Pro
# Clicks "Apply" button
# Fills all form fields from user_profile.json
# Uploads resume and cover letter
# Leaves form ready for manual review
```

**Model Used:** `gemini-2.5-pro` (better reasoning for complex forms)

**⚠️ Important:** Form is NOT submitted automatically. You must review and submit manually.

---

## 📊 Logs & Monitoring

### Real-Time Logs

All activity is logged to console and files:

```
logs/
├── automation_20260211_143022.log  # Detailed step-by-step log
└── application_log.json             # Structured application history
```

### Application Log Format

```json
[
  {
    "timestamp": "2026-02-11T14:30:22.123456",
    "job_url": "https://careers.company.com/jobs/123456",
    "status": "SUCCESS",
    "details": {
      "steps_completed": [
        "User profile loaded",
        "Job description scraped",
        "Resume generated",
        "Cover letter generated",
        "Application form filled (not submitted)"
      ],
      "resume_path": "generated_documents/resume_tailored_20260211_143022.docx",
      "cover_letter_path": "generated_documents/cover_letter_20260211_143025.docx"
    }
  }
]
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. **API Timeout (Resume/Cover Letter)**

```
❌ API request timed out (>120 seconds)
```

**Solution:**
- First request after idle time takes 30-60 seconds (cold start)
- Wait and retry once
- Check internet connection

#### 2. **Playwright Not Installed**

```
❌ Playwright executable not found
```

**Solution:**
```powershell
playwright install
```

#### 3. **User Profile Not Found**

```
❌ User profile file not found: user_profile.json
```

**Solution:**
- Ensure `user_profile.json` exists in the project directory
- Check file path in error message

#### 4. **Form Fields Not Filled**

**Solution:**
- Some websites have complex forms that AI may struggle with
- Review the browser window to see what was filled
- You can manually complete missing fields
- Update `user_profile.json` with more complete information

#### 5. **Browser Opens But Nothing Happens**

**Solution:**
- Check console logs for errors
- Verify job URL is accessible
- Try with a different job posting URL

### Debug Mode

To see more detailed logs, edit `config.py`:

```python
LOG_LEVEL = "DEBUG"  # Changed from "INFO"
```

---

## 🔒 Security

### ⚠️ Important Security Notes

1. **Never commit API keys to Git**
   - API keys are in `config.py` (private repo only!)
   - Use `.env` file for production
   - `.gitignore` already excludes `.env`

2. **Keep user_profile.json private**
   - Contains personal information
   - Don't share publicly
   - Consider encrypting if storing in cloud

3. **Review before submitting**
   - Always review filled forms before submitting
   - Verify uploaded files are correct
   - Check for any incorrect information

4. **API Key Rotation**
   - If keys are accidentally exposed, rotate them immediately
   - Update in `config.py` or `.env`

---

## 🎨 Customization

### Change AI Models

Edit `config.py`:

```python
# Use different Gemini models
SCRAPING_MODEL = "gemini-2.0-flash-exp"      # Fast & cheap
FORM_FILLING_MODEL = "gemini-2.5-pro"        # Accurate & smart
```

### Adjust Browser Settings

Edit `config.py`:

```python
BROWSER_HEADLESS = True   # Run browser in background (no window)
BROWSER_SLOW_MO = 500     # Slow down actions for debugging (ms)
```

### Custom Form Filling Logic

Edit the `fill_application_form()` function in `job_application_automation.py` to customize the form filling instructions.

---

## 🚀 Future Enhancements

Planned features for future versions:

- [ ] **Auto-submit option** (with confirmation)
- [ ] **Batch processing** (multiple jobs at once)
- [ ] **Job board integration** (LinkedIn, Indeed, etc.)
- [ ] **Success tracking** (track responses, interviews)
- [ ] **A/B testing** (try different resume versions)
- [ ] **Email notifications** (when job applied successfully)
- [ ] **Resume templates** (choose different styles)
- [ ] **Application status tracking** (follow up reminders)

---

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the logs in `logs/` directory
3. Verify all configuration in `config.py`
4. Ensure `user_profile.json` is complete

---

## 📄 License

This project is for personal use. Ensure compliance with job board terms of service.

---

## 🙏 Acknowledgments

- **browser-use** - AI-powered browser automation framework
- **LangChain** - AI agent orchestration
- **Google Gemini** - Large language model
- **Resume Optimizer API** - Tailored resume generation

---

## ⚡ Quick Start Checklist

Before running for the first time:

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Playwright installed (`playwright install`)
- [ ] `user_profile.json` updated with your information
- [ ] Job URL set in `job_application_automation.py`
- [ ] API keys verified in `config.py`

Then run:

```powershell
python job_application_automation.py
```

**Good luck with your job applications! 🎉**
