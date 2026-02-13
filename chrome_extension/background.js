// Background Service Worker for LinkedIn Job Automator

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('LinkedIn Job Automator installed');
  
  // Set default configuration
  chrome.storage.local.set({
    maxApplications: 10,
    skipGeneration: false,
    appliedCount: 0,
    failedCount: 0,
    isRunning: false,
    resumeApiUrl: 'https://resume-optimizer-api-fvpd.onrender.com'
  });
});

// Listen for messages from content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleMessage(message, sender, sendResponse);
  return true; // Keep message channel open for async responses
});

async function handleMessage(message, sender, sendResponse) {
  switch (message.type) {
    case 'GENERATE_DOCUMENTS':
      await generateDocuments(message.jobInfo, sendResponse);
      break;
    case 'LOG':
      // Forward log to popup if it's open
      forwardToPopup(message);
      break;
    case 'STATS_UPDATE':
      // Forward stats update to popup
      forwardToPopup(message);
      break;
    case 'AUTOMATION_COMPLETE':
    case 'AUTOMATION_ERROR':
      // Forward to popup
      forwardToPopup(message);
      break;
  }
}

async function generateDocuments(jobInfo, sendResponse) {
  try {
    // Get API configuration
    const config = await chrome.storage.local.get(['resumeApiKey', 'resumeApiUrl']);
    
    if (!config.resumeApiKey || !config.resumeApiUrl) {
      sendResponse({
        success: false,
        error: 'API configuration not found'
      });
      return;
    }
    
    // Prepare job description for API
    const jobDescription = `
Job Title: ${jobInfo.title}
Company: ${jobInfo.company}
Location: ${jobInfo.location || 'Not specified'}

Job Description:
${jobInfo.description}
    `.trim();
    
    console.log('Calling Resume API...');
    
    // Call the Resume API
    const response = await fetch(`${config.resumeApiUrl}/api/v1/optimize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': config.resumeApiKey
      },
      body: JSON.stringify({
        job_description: jobDescription,
        return_format: 'base64'
      })
    });
    
    if (!response.ok) {
      throw new Error(`API returned status ${response.status}`);
    }
    
    const data = await response.json();
    
    console.log('Resume API response received');
    
    sendResponse({
      success: true,
      resume: data.resume,
      coverLetter: data.cover_letter
    });
    
  } catch (error) {
    console.error('Error generating documents:', error);
    sendResponse({
      success: false,
      error: error.message
    });
  }
}

function forwardToPopup(message) {
  // Try to send message to popup
  chrome.runtime.sendMessage(message).catch(() => {
    // Popup might not be open, ignore error
  });
}

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  // Open popup (default behavior)
});

console.log('Background service worker loaded');
