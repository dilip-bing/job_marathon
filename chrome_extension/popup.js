// Popup UI Controller
class PopupController {
  constructor() {
    this.statusDot = document.getElementById('statusDot');
    this.statusText = document.getElementById('statusText');
    this.appliedCount = document.getElementById('appliedCount');
    this.failedCount = document.getElementById('failedCount');
    this.logContainer = document.getElementById('logContainer');
    this.startBtn = document.getElementById('startBtn');
    this.stopBtn = document.getElementById('stopBtn');
    this.saveConfigBtn = document.getElementById('saveConfig');
    
    this.init();
  }

  async init() {
    // Load saved configuration
    await this.loadConfig();
    
    // Set up event listeners
    this.startBtn.addEventListener('click', () => this.startAutomation());
    this.stopBtn.addEventListener('click', () => this.stopAutomation());
    this.saveConfigBtn.addEventListener('click', () => this.saveConfig());
    
    // Listen for status updates from background script
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message);
    });
    
    // Check current status
    await this.updateStatus();
  }

  async loadConfig() {
    const config = await chrome.storage.local.get([
      'resumeApiKey',
      'resumeApiUrl',
      'maxApplications',
      'skipGeneration'
    ]);
    
    if (config.resumeApiKey) {
      document.getElementById('resumeApiKey').value = config.resumeApiKey;
    }
    if (config.resumeApiUrl) {
      document.getElementById('resumeApiUrl').value = config.resumeApiUrl;
    }
    if (config.maxApplications) {
      document.getElementById('maxApplications').value = config.maxApplications;
    }
    if (config.skipGeneration !== undefined) {
      document.getElementById('skipGeneration').checked = config.skipGeneration;
    }
  }

  async saveConfig() {
    const config = {
      resumeApiKey: document.getElementById('resumeApiKey').value,
      resumeApiUrl: document.getElementById('resumeApiUrl').value,
      maxApplications: parseInt(document.getElementById('maxApplications').value),
      skipGeneration: document.getElementById('skipGeneration').checked
    };
    
    await chrome.storage.local.set(config);
    this.addLog('Configuration saved successfully!', 'success');
    
    // Briefly show feedback
    this.saveConfigBtn.textContent = '✅ Saved!';
    setTimeout(() => {
      this.saveConfigBtn.textContent = '💾 Save Configuration';
    }, 2000);
  }

  async startAutomation() {
    // Validate configuration
    const config = await chrome.storage.local.get(['resumeApiKey', 'resumeApiUrl']);
    
    if (!config.skipGeneration && (!config.resumeApiKey || !config.resumeApiUrl)) {
      this.addLog('❌ Please configure API settings first!', 'error');
      return;
    }
    
    // Check if we're on LinkedIn jobs page
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url.includes('linkedin.com/jobs')) {
      this.addLog('❌ Please navigate to LinkedIn Jobs page first!', 'error');
      window.open('https://www.linkedin.com/jobs/search/', '_blank');
      return;
    }
    
    // Send start command to content script
    chrome.tabs.sendMessage(tab.id, { action: 'START_AUTOMATION' }, (response) => {
      if (chrome.runtime.lastError) {
        this.addLog('❌ Failed to start: ' + chrome.runtime.lastError.message, 'error');
        return;
      }
      
      this.setRunning(true);
      this.addLog('▶️ Automation started!', 'info');
    });
  }

  async stopAutomation() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    chrome.tabs.sendMessage(tab.id, { action: 'STOP_AUTOMATION' }, (response) => {
      this.setRunning(false);
      this.addLog('⏹️ Automation stopped!', 'info');
    });
  }

  setRunning(running) {
    if (running) {
      this.statusDot.classList.add('running');
      this.statusText.textContent = 'Running...';
      this.startBtn.disabled = true;
      this.stopBtn.disabled = false;
    } else {
      this.statusDot.classList.remove('running');
      this.statusText.textContent = 'Ready';
      this.startBtn.disabled = false;
      this.stopBtn.disabled = true;
    }
  }

  async updateStatus() {
    const stats = await chrome.storage.local.get(['appliedCount', 'failedCount', 'isRunning']);
    
    this.appliedCount.textContent = stats.appliedCount || 0;
    this.failedCount.textContent = stats.failedCount || 0;
    
    if (stats.isRunning) {
      this.setRunning(true);
    }
  }

  handleMessage(message) {
    switch (message.type) {
      case 'STATUS_UPDATE':
        this.updateStatusFromMessage(message);
        break;
      case 'LOG':
        this.addLog(message.text, message.level);
        break;
      case 'STATS_UPDATE':
        this.updateStats(message.stats);
        break;
      case 'AUTOMATION_COMPLETE':
        this.setRunning(false);
        this.addLog('✅ Automation completed!', 'success');
        break;
      case 'AUTOMATION_ERROR':
        this.setRunning(false);
        this.addLog('❌ Error: ' + message.error, 'error');
        break;
    }
  }

  updateStatusFromMessage(message) {
    this.statusText.textContent = message.status;
  }

  updateStats(stats) {
    this.appliedCount.textContent = stats.applied || 0;
    this.failedCount.textContent = stats.failed || 0;
    
    // Save to storage
    chrome.storage.local.set({
      appliedCount: stats.applied || 0,
      failedCount: stats.failed || 0
    });
  }

  addLog(text, level = 'info') {
    const entry = document.createElement('p');
    entry.className = `log-entry ${level}`;
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${text}`;
    
    this.logContainer.appendChild(entry);
    
    // Auto-scroll to bottom
    this.logContainer.scrollTop = this.logContainer.scrollHeight;
    
    // Keep only last 50 entries
    while (this.logContainer.children.length > 50) {
      this.logContainer.removeChild(this.logContainer.firstChild);
    }
  }
}

// Initialize popup controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new PopupController();
});
