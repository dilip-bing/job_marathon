# Form Responses Configuration Guide

## Overview

The `form_responses.yaml` file contains standardized responses for common job application form questions. This makes it easy to update your answers without modifying the main automation code.

## File Location

```
job_marathon/
├── form_responses.yaml   ← Configuration file
├── user_profile.json     ← Personal details
└── job_application_automation.py
```

## Structure

The YAML file is organized into categories:

### 1. Work Authorization

Responses for visa, sponsorship, and work authorization questions:

```yaml
work_authorization:
  legally_authorized_us:
    answer: "YES"
  visa_status:
    answer: "F-1 Student Visa"
  require_sponsorship:
    answer: "YES"
```

**How to Update:**
- Change `answer` field for each question type
- Add `alternatives` array if you want to provide multiple acceptable answers
- Use `note` field for your reference (not shown to forms)

### 2. Demographics

```yaml
demographics:
  veteran_status:
    answer: "I am not a veteran"
    alternatives: ["No", "Not a veteran"]
  disability_status:
    answer: "No disability"
```

**Update these based on your situation**

### 3. Job Source / Referral

Controls how you answer "How did you hear about us?"

```yaml
job_source:
  primary_sources:
    - "LinkedIn"
    - "Social Media"
    - "Company Website"
  default_primary: "LinkedIn"
```

**Tips:**
- Most forms accept "LinkedIn" or "Social Media"
- Avoid leaving "Select" as value
- Update `default_primary` for your preferred answer

### 4. File Uploads

Maps upload fields to file indices:

```yaml
file_uploads:
  resume:
    file_index: 0  # Always resume
  cover_letter:
    file_index: 1  # Cover letter
  additional_documents:
    file_index: 1  # Use cover letter for "additional documents" too
```

**How It Works:**
- `index: 0` = Resume file
- `index: 1` = Cover letter file
- If a form asks for "additional documents", the cover letter is uploaded

### 5. Additional Questions

Common application questions:

```yaml
additional_questions:
  why_interested:
    strategy: "Extract from cover letter or generate based on job description"
  biggest_strength:
    default: "Problem-solving and technical expertise"
```

**Customization:**
- Update `default` values with your own responses
- These are used when forms ask open-ended questions

## How to Add New Responses

### Example: Adding a new question type

```yaml
certifications:
  have_certifications:
    question_keywords: ["certifications", "professional certifications"]
    answer: "Yes"
    details: "AWS Certified Solutions Architect"
```

### Example: Adding security clearance

```yaml
background_check:
  security_clearance:
    question_keywords: ["security clearance", "clearance level"]
    answer: "None"
    note: "Update if you have clearance"
```

## Field Explanations

| Field | Purpose | Example |
|-------|---------|---------|
| `question_keywords` | Words that identify this question | `["visa", "sponsorship"]` |
| `answer` | Your response | `"YES"` or `"No"` |
| `alternatives` | Other acceptable answers | `["No", "Not applicable"]` |
| `note` | Internal note (not used in forms) | `"F-1 students need sponsorship"` |
| `strategy` | How to generate dynamic answers | `"Extract from cover letter"` |
| `default` | Fallback answer | `"Negotiable"` |

## Common Updates

### Change Visa Status
```yaml
work_authorization:
  visa_status:
    answer: "H-1B"  # Change from F-1 to H-1B
```

### Update Salary Expectations
```yaml
compensation:
  salary_expectations:
    answer: "$90,000 - $110,000"  # Specific range
```

### Modify Job Source
```yaml
job_source:
  default_primary: "Company Website"  # Changed from LinkedIn
```

### Add Certifications
```yaml
certifications:
  aws_certified:
    question_keywords: ["AWS", "cloud certification"]
    answer: "AWS Certified Solutions Architect - Associate"
```

## Integration with User Profile

The automation combines:
- **user_profile.json** → Personal data (name, email, address, work history)
- **form_responses.yaml** → Question responses (work auth, demographics, preferences)

Both files work together:
```
Form Field: "Email" → user_profile.json → personal_info.email
Form Field: "Veteran Status?" → form_responses.yaml → demographics.veteran_status.answer
```

## Testing Your Changes

1. Edit `form_responses.yaml`
2. Save the file
3. Run automation in test mode:
   ```bash
   python job_application_automation.py --skip-generation
   ```
4. Check the logs to see if your responses are being used

## Tips

✅ **DO:**
- Keep answers concise and professional
- Use consistent formatting
- Add notes for your reference
- Test changes with `--skip-generation` flag

❌ **DON'T:**
- Leave fields blank unless intentional
- Use special characters that might break YAML
- Forget to update both `user_profile.json` AND `form_responses.yaml`

## Example: Full Customization

```yaml
# My Custom Responses
work_authorization:
  visa_status:
    answer: "Green Card Holder"
  require_sponsorship:
    answer: "NO"

demographics:
  veteran_status:
    answer: "US Navy Veteran (2010-2014)"
  disability_status:
    answer: "No"

compensation:
  salary_expectations:
    answer: "$120,000 - $150,000"

job_source:
  default_primary: "Referral"
  default_secondary: "Employee Referral - John Doe"
```

## Troubleshooting

**Problem:** Answers not showing up in forms
- **Solution:** Check YAML syntax (indentation is 2 spaces, not tabs)

**Problem:** Agent picks wrong answer
- **Solution:** Update `question_keywords` to match form's exact wording

**Problem:** File won't load
- **Solution:** Validate YAML at http://www.yamllint.com/

## Need More Help?

Check these files:
- `user_profile.json` - For personal data updates
- `job_application_automation.py` - Main automation logic
- `logs/` - Detailed execution logs
