# 🚀 QUICK START GUIDE

## For Absolute Beginners - Step by Step

### ⚡ 5-Minute Setup

#### Step 1: Open PowerShell in this directory
```powershell
cd C:\Users\dilip\job_marathon
```

#### Step 2: Create and activate virtual environment
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

**💡 If you get an error about execution policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 3: Install packages
```powershell
pip install -r requirements.txt
playwright install
```

**⏱️ This takes 2-3 minutes**

#### Step 4: Verify setup
```powershell
python verify_setup.py
```

**✅ You should see "ALL CHECKS PASSED!"**

#### Step 5: Update your profile

1. Open `user_profile.json`
2. Update YOUR information:
   - Name, email, phone
   - Address
   - Work experience
   - Skills
   - Education

**⚠️ This is IMPORTANT - the form will be filled with this data!**

#### Step 6: Set your job URL

1. Open `job_application_automation.py`
2. Find the `main()` function at the bottom
3. Replace the example URL:

```python
# Replace this line:
JOB_URL = "https://www.example.com/jobs/12345"

# With your actual job URL:
JOB_URL = "https://company.com/careers/job/123"
```

#### Step 7: Run it!

```powershell
python job_application_automation.py
```

### 📺 What You'll See

1. **Browser Opens** - You'll see a Chrome window open
2. **Job Scraping** - The AI navigates to the job and extracts description
3. **Documents Generating** - Console shows "⏳ Sending request to API..."
4. **Form Filling** - Browser navigates back and fills the application
5. **Done!** - Form is filled but NOT submitted (you review it first)

### ⏱️ How Long Does It Take?

- **First time**: 2-3 minutes (API cold start)
- **Subsequent runs**: 30-60 seconds

### ⚠️ Important Notes

1. **Don't close the browser window** - Let the AI control it
2. **First API call is slow** - The API "wakes up" (30-60 seconds)
3. **Review before submitting** - Always check the filled form
4. **Keep logs** - Check `logs/` folder for detailed information

### 🐛 Something Not Working?

**Issue:** Python not found
```powershell
# Install Python from python.org
# Make sure to check "Add to PATH" during installation
```

**Issue:** ModuleNotFoundError
```powershell
# Make sure you activated virtual environment
.\venv\Scripts\Activate.ps1

# Then install packages again
pip install -r requirements.txt
```

**Issue:** Playwright browsers not found
```powershell
playwright install
```

**Issue:** API timeout
```
# First request is slow (cold start)
# Just wait 60 seconds and it will complete
# Or run again - second try is faster
```

### 📖 Full Documentation

For complete documentation, see [README.md](README.md)

### 💡 Pro Tips

1. **Test with one job first** - Don't run on 10 jobs immediately
2. **Check generated documents** - Look in `generated_documents/` folder
3. **Read the logs** - Check `logs/` for detailed information
4. **Update profile regularly** - Keep `user_profile.json` current

### ✅ You're Ready!

If `verify_setup.py` passed, you're good to go! 

Just:
1. ✅ Update `user_profile.json`
2. ✅ Set `JOB_URL` in the main script
3. ✅ Run `python job_application_automation.py`

**Good luck! 🎉**
