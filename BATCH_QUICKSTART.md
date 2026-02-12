# BATCH APPLICATION QUICK START

## 🚀 Run All 37 Jobs in One Command

```bash
# Recommended: Use existing resume/cover letter (faster, no API calls)
python batch_apply.py --skip-generation
```

## 📊 View Results After Completion

```bash
# Quick view
python view_summary.py

# Or manually open
notepad logs\batch_summary.txt
```

## 🔄 Resume Failed Jobs

```bash
python batch_apply.py --resume --skip-generation
```

## 📁 All Logs Saved In

- **Summary:** `logs/batch_summary.txt` ← Read this first!
- **Individual company logs:** `logs/company_logs/*.log`
- **JSON report:** `logs/batch_report.json`

## ⏱️ Expected Time

- **37 jobs × ~2-3 min each** = ~2-3 hours total
- **Progress saved** - can resume if interrupted (Ctrl+C)

## ✅ That's It!

See [README_BATCH.md](README_BATCH.md) for full documentation.
