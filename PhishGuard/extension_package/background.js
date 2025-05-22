// PhishGuard Enhanced - Background Service Worker
console.log("PhishGuard Enhanced background script loaded");

// Default config
let config = {
  serverUrl: 'http://localhost:5050',
  deepfakeDetectionEnabled: true,
  phishingDetectionEnabled: true,
  mediaHighlightingEnabled: true
};

// Load configuration
chrome.storage.local.get('config', (data) => {
  if (data.config) {
    config = { ...config, ...data.config };
  } else {
    // Store default config
    chrome.storage.local.set({ config });
  }
});

// Context menu setup for media analysis
chrome.contextMenus.create({
  id: 'analyzeMedia',
  title: 'Analyze Media for Deepfakes',
  contexts: ['audio', 'video']
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'analyzeMedia') {
    const mediaUrl = info.srcUrl;
    
    if (mediaUrl) {
      // Notify the user that we're analyzing
      chrome.tabs.sendMessage(tab.id, { 
        action: 'showNotification', 
        message: 'Analyzing media for deepfakes...'
      });
      
      // Send request to server
      fetch(`${config.serverUrl}/detect-deepfake-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: mediaUrl })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          const result = data.result;
          const isFake = result.is_fake;
          
          // Create notification
          chrome.notifications.create({
            type: 'basic',
            iconUrl: isFake ? 'icons/icon_warning.png' : 'icons/icon_safe.png',
            title: isFake ? 'Potential Deepfake Detected!' : 'Media Appears Authentic',
            message: `The ${result.prediction} (${(result.confidence * 100).toFixed(1)}% confidence)`
          });
          
          // If it's fake, highlight it in the page
          if (isFake) {
            chrome.tabs.sendMessage(tab.id, {
              action: 'highlightSuspiciousMedia',
              mediaUrls: [mediaUrl]
            });
          }
        } else {
          chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: 'Analysis Failed',
            message: data.error || 'Could not analyze this media file'
          });
        }
      })
      .catch(error => {
        console.error('Error analyzing media:', error);
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'icons/icon48.png',
          title: 'Error',
          message: 'Failed to connect to the PhishGuard server'
        });
      });
    }
  }
});

// Handle URL checking messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "checkUrl") {
    checkUrl(message.url)
      .then(result => {
        sendResponse(result);
      })
      .catch(error => {
        console.error("Error checking URL:", error);
        sendResponse({ success: false, error: error.message });
      });
    
    return true; // Required for async response
  }
});

// URL checking function
async function checkUrl(url) {
  if (!config.phishingDetectionEnabled) {
    return { success: false, message: "URL checking disabled" };
  }
  
  try {
    const response = await fetch(`${config.serverUrl}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error in checkUrl:", error);
    throw error;
  }
}

// Check server status periodically
function checkServerStatus() {
  fetch(`${config.serverUrl}/health`, { method: 'GET' })
    .then(response => response.text())
    .then(text => {
      let data;
      try {
        data = JSON.parse(text);
      } catch (jsonError) {
        console.error('Invalid JSON from server:', jsonError);
        chrome.storage.local.set({
          serverStatus: {
            serverAvailable: false,
            phishingDetection: false,
            deepfakeDetection: false,
            lastChecked: Date.now(),
            error: 'Invalid JSON from server'
          }
        });
        return;
      }
      const status = {
        serverAvailable: true,
        phishingDetection: data.phishing_model || false,
        deepfakeDetection: data.deepfake_detector || false,
        lastChecked: Date.now()
      };
      chrome.storage.local.set({ serverStatus: status });
    })
    .catch(error => {
      console.error("Server status check failed:", error);
      chrome.storage.local.set({
        serverStatus: {
          serverAvailable: false,
          phishingDetection: false,
          deepfakeDetection: false,
          lastChecked: Date.now(),
          error: error.message
        }
      });
    });
}

// Initial check and schedule periodic checks
checkServerStatus();
setInterval(checkServerStatus, 5 * 60 * 1000); // Check every 5 minutes
