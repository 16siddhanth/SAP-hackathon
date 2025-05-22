// Background script for PhishGuard extension

self.addEventListener('install', () => {
  console.log('PhishGuard Hover Tooltip installed');
});

// Initialize whitelist with default values
chrome.storage.local.get('whitelist', (result) => {
  if (!result.whitelist) {
    const defaultWhitelist = {
      "paypal.com": "https://www.paypal.com/signin",
      "bankxyz.com": "https://online.bankxyz.com/login",
      "google.com": "https://accounts.google.com/signin"
    };
    chrome.storage.local.set({ whitelist: defaultWhitelist });
  }
});

// Cache for phishing detection results to avoid repeated API calls
let resultCache = {};

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "checkUrl") {
    const url = request.url;
    
    // Check cache first
    if (resultCache[url]) {
      sendResponse(resultCache[url]);
      return true;
    }
    
    // Check against whitelist first (quick check)
    chrome.storage.local.get('whitelist', (result) => {
      const whitelist = result.whitelist || {};
      const hostname = new URL(url).hostname.replace(/^www\./, "");
      
      // If domain is in whitelist, it's safe
      for (const trusted in whitelist) {
        if (hostname === trusted || hostname.endsWith('.' + trusted)) {
          const response = { isPhishing: false, message: "Legitimate URL\nSafe to browse" };
          resultCache[url] = response;
          sendResponse(response);
          return;
        }
      }
      
      // If not in whitelist, check with the ML model API
      fetch('http://127.0.0.1:5000/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url }),
      })
      .then(response => response.json())
      .then(data => {
        const result = {
          isPhishing: data.data.includes("Phishy"),
          message: data.data,
          similarTrusted: findSimilarTrustedDomain(hostname, whitelist)
        };
        
        // Cache the result
        resultCache[url] = result;
        sendResponse(result);
      })
      .catch(error => {
        console.error('Error checking URL:', error);
        // Fall back to basic pattern matching if API is unavailable
        const result = fallbackUrlCheck(url, hostname, whitelist);
        resultCache[url] = result;
        sendResponse(result);
      });
    });
    
    return true; // Required for async sendResponse
  }
});

// Find similar trusted domains for potential phishing attempts
function findSimilarTrustedDomain(hostname, whitelist) {
  let bestMatch = '';
  let highestSimilarity = 0;
  
  for (const trusted in whitelist) {
    // Check for domain similarity using basic pattern matching
    if (hostname.includes(trusted) && hostname !== trusted) {
      // Simple similarity score based on length of common substring
      const similarity = trusted.length / hostname.length;
      if (similarity > highestSimilarity) {
        highestSimilarity = similarity;
        bestMatch = trusted;
      }
    }
  }
  
  return highestSimilarity > 0.5 ? bestMatch : '';
}

// Fallback check when API is unavailable
function fallbackUrlCheck(url, hostname, whitelist) {
  // Check for suspicious patterns in the URL
  const suspiciousPatterns = [
    /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/,  // IP address
    /^https?:\/\/[^\/]+\.[^\/]+\/.*\@/,    // @ symbol in path
    /^https?:\/\/[^\/]+\.[^\/]+\/.*\//,    // Multiple redirects
    /\.(tk|ml|ga|cf|gq|top|xyz|pw)\/$/i,      // Suspicious TLDs
    /https?:\/\/[^\/]*https?/i,              // HTTPS in domain
    /\.(php|html)\?[^=]*=[^&]*&[^=]*=[^&]*/   // Multiple parameters
  ];
  
  for (const pattern of suspiciousPatterns) {
    if (pattern.test(url)) {
      return {
        isPhishing: true,
        message: "Phishy URL\nBe cautious",
        similarTrusted: findSimilarTrustedDomain(hostname, whitelist)
      };
    }
  }
  
  return {
    isPhishing: false,
    message: "Likely legitimate\nUse caution"
  };
}