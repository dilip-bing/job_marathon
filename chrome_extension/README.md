# LinkedIn Job Application Automator - Chrome Extension

🤖 Automatically apply to LinkedIn jobs with AI-generated resumes and cover letters

## Features

- ✅ **One-Click Automation**: Start the automation from any LinkedIn job search page
- 📝 **AI-Generated Documents**: Automatically generates tailored resumes and cover letters for each job
- 🎯 **Easy Apply Focus**: Only applies to jobs with LinkedIn's "Easy Apply" feature
- 📊 **Real-time Stats**: Track applications, failures, and progress in real-time
- ⚙️ **Configurable**: Set max applications, skip document generation for testing, and more
- 🔒 **Secure**: API keys stored locally in your browser

## Installation

### Step 1: Prepare the Extension

The extension files are located in the `chrome_extension` folder of this project.

### Step 2: Create Icons (Required)

Create icon files in the `chrome_extension/icons/` folder:
- `icon16.png` (16x16 pixels)
- `icon48.png` (48x48 pixels)
- `icon128.png` (128x128 pixels)

You can use any icon design tool or create simple placeholder icons.

### Step 3: Load Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Select the `chrome_extension` folder
5. The extension should now appear in your extensions list

## Configuration

### First-Time Setup

1. Click the extension icon in your Chrome toolbar
2. Enter your configuration:
   - **Resume API Key**: Your API key for the resume generation service
   - **Resume API URL**: `https://resume-optimizer-api-fvpd.onrender.com` (default)
   - **Max Applications**: How many jobs to apply to (default: 10)
   - **Skip Generation**: Enable for testing without calling the API
3. Click "💾 Save Configuration"

### Getting Your API Key

Your Resume API key should be available in your `config.py` file as `RESUME_API_KEY`.

## Usage

### Basic Workflow

1. **Log in to LinkedIn**: Make sure you're logged into your LinkedIn account
2. **Navigate to Jobs**: Go to [LinkedIn Jobs](https://www.linkedin.com/jobs/search/)
3. **Filter Jobs** (Optional): Use LinkedIn's filters to find relevant jobs
4. **Open Extension**: Click the extension icon in your toolbar
5. **Start Automation**: Click "▶️ Start Automation"
6. **Monitor Progress**: Watch the activity log and stats in real-time
7. **Stop Anytime**: Click "⏹️ Stop Automation" to pause

### What It Does

For each job in the search results, the extension will:

1. ✅ Click on the job to view details
2. ✅ Extract job title, company, location, and description
3. ✅ Check if "Easy Apply" is available
4. ✅ Generate tailored resume and cover letter (if not in test mode)
5. ✅ Click "Easy Apply" button
6. ⚠️ **TODO**: Fill out application form
7. ⚠️ **TODO**: Upload documents
8. ⚠️ **TODO**: Submit application

### Test Mode

Enable "Skip Resume Generation" in the configuration to:
- Test the automation without calling the API
- Save API credits during development
- Still extracts job information and finds Easy Apply buttons
- Doesn't submit actual applications

## Current Limitations

### ⚠️ Work In Progress

This extension is currently in **early development**. The following features are **not yet implemented**:

1. **Application Form Filling**: The extension doesn't yet fill out the application form fields
2. **Document Upload**: Resume and cover letter files are generated but not yet uploaded
3. **Multi-Step Forms**: LinkedIn applications often have multiple steps - not yet handled
4. **Form Field Detection**: Need to handle various input types (text, dropdowns, radio buttons)
5. **Submission**: Applications are not actually submitted yet

### Current Behavior

In the current version, the extension will:
- ✅ Find jobs and extract information
- ✅ Generate documents via API
- ✅ Click "Easy Apply" button
- ❌ **NOT submit applications** (closes the modal instead)

## Development Roadmap

### Phase 1: Core Automation (Current)
- [x] Extension structure and UI
- [x] Job listing detection
- [x] Job information extraction
- [x] API integration for document generation
- [ ] Application form filling
- [ ] Document upload
- [ ] Application submission

### Phase 2: Enhanced Features
- [ ] Multi-step form handling
- [ ] Form field intelligence (auto-detect types)
- [ ] Error recovery and retry logic
- [ ] Detailed application reports
- [ ] Export application history

### Phase 3: Advanced Features
- [ ] Custom templates for different job types
- [ ] A/B testing different approaches
- [ ] Analytics and success tracking
- [ ] Handshake support
- [ ] Indeed support

## Architecture

```
chrome_extension/
├── manifest.json         # Extension configuration
├── popup.html           # Extension popup UI
├── popup.css            # Popup styling
├── popup.js             # Popup controller
├── content.js           # LinkedIn page automation
├── background.js        # API calls and background tasks
└── icons/               # Extension icons (you need to create these)
```

### Component Communication

```
Popup (UI) ←→ Background Script ←→ Content Script (LinkedIn)
     ↓              ↓                      ↓
  Storage      Resume API           DOM Manipulation
```

## Troubleshooting

### Extension Not Working

1. **Check you're on LinkedIn Jobs page**: Navigate to `https://www.linkedin.com/jobs/search/`
2. **Verify API configuration**: Make sure API key and URL are set
3. **Check console for errors**: Open DevTools (F12) and check Console tab
4. **Reload extension**: Go to `chrome://extensions/` and click reload

### No Jobs Found

- Make sure job listings are visible on the page
- Try scrolling down to load more jobs
- LinkedIn may have changed their HTML structure - selectors may need updating

### API Errors

- Verify your API key is correct
- Check that the Resume API is running
- The API may need to "wake up" if it's on a free tier (takes ~30 seconds)

## Security Notes

- API keys are stored in Chrome's `storage.local` (not synced across devices)
- Documents are generated server-side and not persisted by the extension
- All communication with LinkedIn happens in the content script
- No external tracking or analytics

## Contributing

This extension is part of the larger `job_marathon` automation project. Contributions welcome!

### Key Areas Needing Work

1. **Form Filling Logic** (`content.js`): 
   - Detect form fields
   - Fill text inputs, dropdowns, etc.
   - Handle multi-step forms

2. **Document Upload** (`content.js`):
   - Convert base64 documents to File objects
   - Trigger file input upload
   - Handle LinkedIn's file upload UI

3. **Submission Logic** (`content.js`):
   - Detect submit buttons
   - Handle errors and validation
   - Confirm successful submission

4. **Selector Maintenance**:
   - LinkedIn frequently updates their UI
   - Selectors may break and need updates

## License

Part of the job_marathon project. See main repository for license details.

## Disclaimer

This tool is for educational purposes. Use responsibly and in accordance with LinkedIn's Terms of Service. Automated application submission may violate LinkedIn's policies - use at your own risk.
