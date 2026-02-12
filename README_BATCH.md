# Batch Job Application Automation

## Overview

This system allows you to apply to multiple jobs automatically, processing each one sequentially with detailed logging and fail-proof error handling.

## Features

✅ **Sequential Processing** - Applies to jobs one by one  
✅ **Fail-Proof** - Continues to next job even if one fails  
✅ **Detailed Logging** - Separate log file for each company  
✅ **Summary Report** - Easy-to-read summary of all applications  
✅ **Resume Support** - Can resume from where it left off  
✅ **Test Mode** - Skip document generation for faster testing  

## Quick Start

### 1. Normal Mode (Generate New Documents)
```bash
python batch_apply.py
```
This will:
- Process all jobs in `company_list.json`
- Generate tailored resume/cover letter for each job
- Fill application forms
- Create detailed logs for each company

### 2. Test Mode (Use Existing Documents)
```bash
python batch_apply.py --skip-generation
```
This will:
- Process all jobs using the latest existing resume/cover letter
- Skip API calls for document generation (faster)
- Useful for testing form filling without regenerating documents

### 3. Resume From Previous Run
```bash
python batch_apply.py --resume
```
This will:
- Skip jobs that were already completed
- Skip jobs that already failed
- Only process remaining jobs

### 4. Resume in Test Mode
```bash
python batch_apply.py --resume --skip-generation
```

## File Structure

```
job_marathon/
├── batch_apply.py              # Main batch processing script
├── job_application_automation.py  # Single job automation
├── company_list.json           # List of jobs to apply to
├── user_profile.json           # Your profile data
├── form_responses.yaml         # Form Q&A configuration
├── generated_documents/        # Generated resumes/cover letters
└── logs/
    ├── batch_run_YYYYMMDD_HHMMSS.log    # Detailed batch log
    ├── batch_summary.txt                 # Human-readable summary ⭐
    ├── batch_report.json                 # Machine-readable report
    ├── batch_progress.json               # Progress tracking
    └── company_logs/
        ├── 001_Smith_Nephew_YYYYMMDD_HHMMSS.log
        ├── 002_Quad_YYYYMMDD_HHMMSS.log
        ├── 003_Pluralsight_YYYYMMDD_HHMMSS.log
        └── ...                          # One log per company
```

## Understanding the Logs

### 1. Company Logs (Most Detailed)
Location: `logs/company_logs/`

Each company gets its own log file with complete details:
- Job scraping process
- Document generation (resume/cover letter)
- Form filling steps
- File uploads
- Errors and warnings
- Final status

**Example:** `001_Smith_Nephew_Software_Electrical_R_D_Intern_20260211_143022.log`

### 2. Batch Summary (Quick Review) ⭐
Location: `logs/batch_summary.txt`

**This is what you want to check first!** It contains:
- Overall statistics (success/failure counts)
- List of all jobs with status
- Links to detailed logs
- Time taken

**Example content:**
```
================================================================================
BATCH JOB APPLICATION AUTOMATION - SUMMARY REPORT
================================================================================

📅 Started:  2026-02-11 14:30:00
📅 Finished: 2026-02-11 16:45:30
⏱️  Duration: 2:15:30

================================================================================
STATISTICS
================================================================================
Total Jobs:     37
✅ Successful:  32
❌ Failed:      5
⏭️  Skipped:     0
📊 Success Rate: 86.5%

================================================================================
DETAILED RESULTS
================================================================================

1. ✅ Smith+Nephew - Software/Electrical R&D Intern
   Status: SUCCESS
   URL: https://smithnephew.wd5.myworkdayjobs.com/...
   Log: logs/company_logs/001_Smith_Nephew_20260211_143022.log

2. ❌ Quad - Software Development Intern
   Status: FAILED
   URL: https://www.bequad.com/job/...
   Log: logs/company_logs/002_Quad_20260211_143545.log
   Error: Timeout during form filling

... (continues for all jobs)
```

### 3. Batch Run Log (Technical Details)
Location: `logs/batch_run_YYYYMMDD_HHMMSS.log`

Contains all console output including:
- Progress updates
- High-level status for each job
- System messages

### 4. Batch Report (JSON Format)
Location: `logs/batch_report.json`

Machine-readable report with:
- Statistics
- Full results array
- Timestamps
- Error details

Perfect for parsing with scripts or data analysis.

### 5. Progress Tracker
Location: `logs/batch_progress.json`

Tracks which jobs have been:
- Completed successfully
- Failed
- Currently in progress

Used by `--resume` flag to skip already-processed jobs.

## Error Handling

### What Happens When a Job Fails?

1. **Error is logged** to company-specific log file
2. **Error is noted** in batch summary
3. **Process continues** to next job automatically
4. **No interruption** to batch processing

### Common Failure Reasons

- ❌ Job posting expired/removed
- ❌ Application requires manual steps
- ❌ Form structure not recognized
- ❌ API timeout (for document generation)
- ❌ File upload issues

### Retry Failed Jobs

After reviewing `batch_summary.txt`, you can:

1. **Check individual company logs** to see why each failed
2. **Fix issues** (update form_responses.yaml, check URLs, etc.)
3. **Re-run with --resume** to only process failed jobs again

Or manually apply to failed jobs later.

## Workflow Example

### Day 1: Initial Batch Run
```bash
# Start processing all 37 jobs
python batch_apply.py
```

**Result:** 32 success, 5 failed

### Review Results
```bash
# Read the summary on terminal or open the file
cat logs/batch_summary.txt

# Or on Windows PowerShell:
Get-Content logs/batch_summary.txt
```

**Ouptut shows:**
- ✅ 32 jobs completed
- ❌ 5 jobs failed
- See individual company logs for details

### Day 2: Fix Issues and Resume
```bash
# After fixing issues in form_responses.yaml or company_list.json
python batch_apply.py --resume
```

**Result:** Only processes the 5 failed jobs, skips the 32 completed ones

## Tips

### 1. Test First
Before running on all 37 jobs, test with a smaller list:
```bash
# Edit company_list.json to include just 2-3 jobs
python batch_apply.py --skip-generation
```

### 2. Monitor Progress
The batch process logs to console in real-time. You can see:
- Which job is being processed (e.g., "Processing 5/37")
- Status updates
- Errors as they happen

### 3. Interrupt Safely
If you need to stop:
- Press `Ctrl+C`
- Progress is automatically saved
- Resume later with `--resume` flag

### 4. Delay Between Jobs
The script waits 5 seconds between jobs to:
- Avoid overwhelming job sites
- Give AI models time to reset
- Prevent rate limiting

You can adjust this in `batch_apply.py` by changing `delay_seconds`.

### 5. Review Before Final Submission
Current configuration fills forms but **submits them**. If you want to review first:
- The individual job automation pauses after filling
- You can manually review and click Submit
- Or update `job_application_automation.py` to not auto-submit

## Troubleshooting

### "Company list file not found"
**Solution:** Make sure `company_list.json` exists in the same directory

### "User profile not found"
**Solution:** Make sure `user_profile.json` exists

### "No resume files found"
**Solution:** Run in normal mode first (without `--skip-generation`) to generate documents

### All jobs failing
**Solutions:**
1. Check internet connection
2. Verify API keys in `job_application_automation.py`
3. Test with single job first: `python job_application_automation.py --url "https://job-url"`
4. Check company logs for specific errors

### Jobs timing out
**Solutions:**
1. Increase timeout in `job_application_automation.py`
2. Use `--skip-generation` to skip document generation (faster)
3. Check if job sites are blocking automation

## Advanced Usage

### Custom Company List
Create your own JSON file:
```json
[
  {
    "name": "Company Name - Job Title",
    "apply_link": "https://...",
    "date_posted": "Feb 11"
  }
]
```

Then edit `batch_apply.py` to point to your file:
```python
COMPANY_LIST_FILE = BASE_DIR / "my_custom_list.json"
```

### Parallel Processing
**Not recommended** because:
- Job sites may detect bot behavior
- Browser automation works better sequentially
- Easier to debug when things go wrong

But if you want to try, you'd need to modify `batch_apply.py` to use `asyncio.gather()` with multiple agents.

## Support

For issues or questions:
1. Check individual company logs in `logs/company_logs/`
2. Check batch summary in `logs/batch_summary.txt`
3. Review the main batch log in `logs/batch_run_*.log`
4. Update `form_responses.yaml` for form-related issues
5. Update `user_profile.json` for profile-related issues

## Summary

**Key Files to Check:**
- 📊 `logs/batch_summary.txt` - Quick overview (START HERE!)
- 📝 `logs/company_logs/*.log` - Detailed per-company logs
- 🔄 `logs/batch_progress.json` - Resume tracking

**Key Commands:**
```bash
# Normal run
python batch_apply.py

# Test mode
python batch_apply.py --skip-generation

# Resume after interruption
python batch_apply.py --resume

# View summary (Windows PowerShell)
Get-Content logs/batch_summary.txt

# View summary (Git Bash / Linux)
cat logs/batch_summary.txt
```

Good luck with your job applications! 🚀
