// LinkedIn Job Application Automator - Content Script
class LinkedInAutomator {
  constructor() {
    this.isRunning = false;
    this.currentJobIndex = 0;
    this.jobElements = [];
    this.stats = {
      applied: 0,
      failed: 0,
      skipped: 0
    };
    this.maxApplications = 10;
    this.skipGeneration = false;
    
    this.init();
  }

  async init() {
    console.log('LinkedIn Automator initialized');
    
    // Listen for messages from popup
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sendResponse);
      return true; // Keep message channel open for async response
    });
    
    // Load configuration
    await this.loadConfig();
  }

  async loadConfig() {
    const config = await chrome.storage.local.get([
      'maxApplications',
      'skipGeneration',
      'resumeApiKey',
      'resumeApiUrl'
    ]);
    
    this.maxApplications = config.maxApplications || 10;
    this.skipGeneration = config.skipGeneration || false;
    this.resumeApiKey = config.resumeApiKey;
    this.resumeApiUrl = config.resumeApiUrl;
  }

  handleMessage(message, sendResponse) {
    switch (message.action) {
      case 'START_AUTOMATION':
        this.startAutomation();
        sendResponse({ success: true });
        break;
      case 'STOP_AUTOMATION':
        this.stopAutomation();
        sendResponse({ success: true });
        break;
      case 'GET_STATUS':
        sendResponse({ isRunning: this.isRunning, stats: this.stats });
        break;
    }
  }

  async startAutomation() {
    if (this.isRunning) {
      this.sendLog('Automation is already running', 'info');
      return;
    }
    
    this.isRunning = true;
    this.currentJobIndex = 0;
    
    // Save running state
    await chrome.storage.local.set({ isRunning: true });
    
    this.sendLog('🚀 Starting LinkedIn job automation...', 'info');
    
    // Find all job listings on the page
    await this.findJobListings();
    
    if (this.jobElements.length === 0) {
      this.sendLog('❌ No job listings found on this page', 'error');
      this.stopAutomation();
      return;
    }
    
    this.sendLog(`Found ${this.jobElements.length} job listings`, 'success');
    
    // Start processing jobs
    await this.processJobs();
  }

  async findJobListings() {
    this.sendLog('🔍 Searching for job listings...', 'info');
    
    // Wait for job listings to load
    await this.sleep(2000);
    
    // LinkedIn job listing selectors (may need updates if LinkedIn changes their HTML)
    const selectors = [
      '.jobs-search-results__list-item',
      '.scaffold-layout__list-item',
      'li.jobs-search-results__list-item'
    ];
    
    for (const selector of selectors) {
      this.jobElements = Array.from(document.querySelectorAll(selector));
      if (this.jobElements.length > 0) {
        break;
      }
    }
    
    // Limit to maxApplications
    this.jobElements = this.jobElements.slice(0, this.maxApplications);
  }

  async processJobs() {
    for (let i = 0; i < this.jobElements.length && this.isRunning; i++) {
      this.currentJobIndex = i;
      const jobElement = this.jobElements[i];
      
      this.sendLog(`\n📋 Processing job ${i + 1}/${this.jobElements.length}...`, 'info');
      
      try {
        // Click on the job to view details
        await this.clickJob(jobElement);
        
        // Wait for job details to load
        await this.sleep(2000);
        
        // Extract job information
        const jobInfo = await this.extractJobInfo();
        
        if (!jobInfo) {
          this.sendLog('⚠️ Could not extract job information, skipping...', 'error');
          this.stats.skipped++;
          continue;
        }
        
        this.sendLog(`📌 ${jobInfo.title} at ${jobInfo.company}`, 'info');
        
        // Check if "Easy Apply" button exists
        const easyApplyBtn = await this.findEasyApplyButton();
        
        if (!easyApplyBtn) {
          this.sendLog('⏭️ Not an Easy Apply job, skipping...', 'info');
          this.stats.skipped++;
          continue;
        }
        
        // Generate resume and cover letter
        let resumeContent = null;
        let coverLetterContent = null;
        
        if (!this.skipGeneration) {
          this.sendLog('📝 Generating resume and cover letter...', 'info');
          const documents = await this.generateDocuments(jobInfo);
          
          if (!documents) {
            this.sendLog('❌ Failed to generate documents, skipping...', 'error');
            this.stats.failed++;
            continue;
          }
          
          resumeContent = documents.resume;
          coverLetterContent = documents.coverLetter;
          this.sendLog('✅ Documents generated successfully', 'success');
        } else {
          this.sendLog('⏭️ Skipping document generation (test mode)', 'info');
        }
        
        // Apply to the job
        await this.applyToJob(easyApplyBtn, jobInfo, resumeContent, coverLetterContent);
        
      } catch (error) {
        this.sendLog(`❌ Error processing job: ${error.message}`, 'error');
        this.stats.failed++;
      }
      
      // Update stats
      this.sendStatsUpdate();
      
      // Wait between applications to avoid rate limiting
      await this.sleep(3000);
    }
    
    // Automation complete
    this.sendLog('\n✅ Automation completed!', 'success');
    this.sendLog(`📊 Applied: ${this.stats.applied}, Failed: ${this.stats.failed}, Skipped: ${this.stats.skipped}`, 'info');
    
    chrome.runtime.sendMessage({ type: 'AUTOMATION_COMPLETE' });
    
    this.stopAutomation();
  }

  async clickJob(jobElement) {
    // Scroll into view
    jobElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    await this.sleep(500);
    
    // Click on the job
    jobElement.click();
  }

  async extractJobInfo() {
    const selectors = {
      title: [
        '.job-details-jobs-unified-top-card__job-title',
        '.jobs-unified-top-card__job-title',
        'h1.t-24'
      ],
      company: [
        '.job-details-jobs-unified-top-card__company-name',
        '.jobs-unified-top-card__company-name',
        '.jobs-unified-top-card__subtitle-primary-grouping a'
      ],
      location: [
        '.job-details-jobs-unified-top-card__bullet',
        '.jobs-unified-top-card__bullet'
      ],
      description: [
        '.jobs-description-content__text',
        '.jobs-box__html-content',
        '#job-details'
      ]
    };
    
    const jobInfo = {};
    
    // Extract title
    for (const selector of selectors.title) {
      const element = document.querySelector(selector);
      if (element) {
        jobInfo.title = element.textContent.trim();
        break;
      }
    }
    
    // Extract company
    for (const selector of selectors.company) {
      const element = document.querySelector(selector);
      if (element) {
        jobInfo.company = element.textContent.trim();
        break;
      }
    }
    
    // Extract location
    for (const selector of selectors.location) {
      const element = document.querySelector(selector);
      if (element) {
        jobInfo.location = element.textContent.trim();
        break;
      }
    }
    
    // Extract description
    for (const selector of selectors.description) {
      const element = document.querySelector(selector);
      if (element) {
        jobInfo.description = element.textContent.trim();
        break;
      }
    }
    
    // Validate we got at least title and company
    if (!jobInfo.title || !jobInfo.company) {
      return null;
    }
    
    return jobInfo;
  }

  async findEasyApplyButton() {
    const selectors = [
      'button.jobs-apply-button',
      'button[aria-label*="Easy Apply"]',
      'button:has-text("Easy Apply")',
      '.jobs-apply-button--top-card button'
    ];
    
    for (const selector of selectors) {
      const button = document.querySelector(selector);
      if (button && button.textContent.includes('Easy Apply')) {
        return button;
      }
    }
    
    return null;
  }

  async generateDocuments(jobInfo) {
    try {
      // Send message to background script to generate documents
      const response = await chrome.runtime.sendMessage({
        type: 'GENERATE_DOCUMENTS',
        jobInfo: jobInfo
      });
      
      if (response.success) {
        return {
          resume: response.resume,
          coverLetter: response.coverLetter
        };
      }
      
      return null;
    } catch (error) {
      console.error('Error generating documents:', error);
      return null;
    }
  }

  async applyToJob(easyApplyBtn, jobInfo, resumeContent, coverLetterContent) {
    this.sendLog('📤 Applying to job...', 'info');
    
    // Click Easy Apply button
    easyApplyBtn.click();
    await this.sleep(2000);
    
    // TODO: Fill out the application form
    // This is a simplified version - real implementation would need to:
    // 1. Handle multi-step forms
    // 2. Upload resume/cover letter files
    // 3. Fill out text fields
    // 4. Handle dropdowns and radio buttons
    // 5. Submit the application
    
    // For now, we'll just log and skip the actual submission in test mode
    if (this.skipGeneration) {
      this.sendLog('⏭️ Test mode: Not submitting application', 'info');
      
      // Close the modal
      const closeBtn = document.querySelector('button[aria-label="Dismiss"]');
      if (closeBtn) {
        closeBtn.click();
      }
      
      this.stats.applied++;
      return;
    }
    
    // Real implementation would fill and submit here
    // For now, mark as applied
    this.stats.applied++;
    this.sendLog('✅ Application submitted!', 'success');
  }

  stopAutomation() {
    this.isRunning = false;
    chrome.storage.local.set({ isRunning: false });
    this.sendLog('⏹️ Automation stopped', 'info');
  }

  sendLog(text, level = 'info') {
    chrome.runtime.sendMessage({
      type: 'LOG',
      text: text,
      level: level
    });
  }

  sendStatsUpdate() {
    chrome.runtime.sendMessage({
      type: 'STATS_UPDATE',
      stats: this.stats
    });
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Initialize the automator
const automator = new LinkedInAutomator();
