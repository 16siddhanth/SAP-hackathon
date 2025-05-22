(function() {
  // Enhanced PhishGuard content script with media detection
  
  // Create Shadow-DOM tooltip container
  const container = document.createElement('div');
  const shadow = container.attachShadow({ mode: 'closed' });
  document.documentElement.appendChild(container);

  const style = document.createElement('style');
  style.textContent = `
    #phish-tooltip {
      position: absolute;
      padding: 12px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      border-radius: 8px;
      font-size: 13px;
      z-index: 2147483647;
      pointer-events: none;
      opacity: 0;
      transition: all 0.3s ease;
      max-width: 320px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      backdrop-filter: blur(10px);
    }
    #phish-tooltip.show {
      pointer-events: auto;
      opacity: 1;
      transform: translateY(-2px);
    }
    #phish-tooltip a {
      color: #fff;
      text-decoration: none;
      display: inline-block;
      margin-top: 8px;
      font-weight: 600;
      opacity: 0.9;
    }
    #phish-tooltip a:hover {
      opacity: 1;
      text-decoration: underline;
    }
    #phish-tooltip .warning {
      color: #ff6b6b;
      font-weight: bold;
      margin-bottom: 8px;
      font-size: 14px;
    }
    #phish-tooltip .safe {
      color: #51cf66;
      font-weight: bold;
      font-size: 14px;
    }
    #phish-tooltip .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 15px;
    }
    #phish-tooltip .confidence {
      font-size: 11px;
      opacity: 0.8;
      margin-top: 5px;
    }
    #phish-tooltip .media-warning {
      background: rgba(255, 107, 107, 0.2);
      padding: 8px;
      border-radius: 4px;
      margin-top: 8px;
      border-left: 3px solid #ff6b6b;
    }
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: white;
      animation: spin 1s ease-in-out infinite;
      margin-right: 8px;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    
    /* Media element highlighting */
    .phishguard-media-highlight {
      outline: 2px solid #ff6b6b !important;
      outline-offset: 2px !important;
      animation: pulse 2s infinite !important;
    }
    @keyframes pulse {
      0% { outline-color: #ff6b6b; }
      50% { outline-color: #ff9999; }
      100% { outline-color: #ff6b6b; }
    }
  `;

  shadow.appendChild(style);

  const tooltip = document.createElement('div');
  tooltip.id = 'phish-tooltip';
  shadow.appendChild(tooltip);

  // Enhanced URL checking with caching
  const urlCache = new Map();
  const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
  
  // Media detection functionality
  class MediaDetector {
    constructor() {
      this.mediaElements = [];
      this.suspiciousMedia = [];
      this.scanInterval = null;
    }
    
    scanForMedia() {
      this.mediaElements = [];
      
      // Scan for audio elements
      document.querySelectorAll('audio').forEach(audio => {
        this.mediaElements.push({
          type: 'audio',
          element: audio,
          src: audio.src || audio.currentSrc,
          sources: Array.from(audio.querySelectorAll('source')).map(s => s.src)
        });
      });
      
      // Scan for video elements
      document.querySelectorAll('video').forEach(video => {
        this.mediaElements.push({
          type: 'video',
          element: video,
          src: video.src || video.currentSrc,
          sources: Array.from(video.querySelectorAll('source')).map(s => s.src)
        });
      });
      
      // Scan for embedded media
      document.querySelectorAll('iframe').forEach(iframe => {
        const src = iframe.src;
        if (src && (src.includes('youtube') || src.includes('vimeo') || src.includes('soundcloud'))) {
          this.mediaElements.push({
            type: 'embedded',
            element: iframe,
            src: src,
            sources: [src]
          });
        }
      });
      
      return this.mediaElements.map(media => ({
        type: media.type,
        src: media.src || '',
        sources: media.sources || []
      }));
    }
    
    highlightSuspiciousMedia(mediaUrls) {
      if (!Array.isArray(mediaUrls)) return;
      
      this.suspiciousMedia = [];
      
      // Find and highlight suspicious media elements
      this.mediaElements.forEach(media => {
        const mediaUrl = media.src || '';
        if (mediaUrls.includes(mediaUrl)) {
          media.element.classList.add('phishguard-media-highlight');
          this.suspiciousMedia.push(media);
        }
      });
    }
    
    clearHighlights() {
      document.querySelectorAll('.phishguard-media-highlight').forEach(el => {
        el.classList.remove('phishguard-media-highlight');
      });
      this.suspiciousMedia = [];
    }
  }
  
  const mediaDetector = new MediaDetector();
  
  async function checkURL(url) {
    if (!url || url.startsWith('javascript:') || url.startsWith('mailto:')) {
      return null;
    }

    // Check cache first
    const cached = urlCache.get(url);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.result;
    }

    try {
      const response = await fetch('http://localhost:5000/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      const result = {
        success: data.success,
        prediction: data.data,
        confidence: data.confidence,
        error: data.error
      };
      
      // Cache the result
      urlCache.set(url, {
        result: result,
        timestamp: Date.now()
      });
      
      return result;
    } catch (error) {
      console.log('PhishGuard: Error checking URL:', error);
      return { success: false, error: error.message };
    }
  }

  let hoverTimer;
  let currentAnchor = null;
  let isChecking = false;

  document.addEventListener('mouseover', e => {
    clearTimeout(hoverTimer);
    const anchor = e.target.closest('a[href]');
    if (!anchor) return hideTooltip();
    
    try {
      const href = anchor.href;
      if (!href || href.startsWith('javascript:') || href.startsWith('#')) {
        return hideTooltip();
      }
      
      currentAnchor = anchor;
      const { hostname } = new URL(href);
      
      // Show loading state after a short delay
      hoverTimer = setTimeout(() => {
        showLoadingTooltip(e.pageX, e.pageY);
        
        // Check URL with background script
        if (!isChecking) {
          isChecking = true;
          chrome.runtime.sendMessage(
            { action: "checkUrl", url: href },
            (response) => {
              isChecking = false;
              if (currentAnchor === anchor) {
                showResultTooltip(e.pageX, e.pageY, hostname, response);
              }
            }
          );
        }
      }, 500); // Longer delay to avoid unnecessary checks
    } catch (err) {
      // Invalid URL, don't show tooltip
      hideTooltip();
    }
  });

  document.addEventListener('mouseout', e => {
    clearTimeout(hoverTimer);
    if (!e.relatedTarget || !tooltip.contains(e.relatedTarget)) {
      hideTooltip();
      currentAnchor = null;
    }
  });
  
  function showLoadingTooltip(x, y) {
    tooltip.innerHTML = `
      <div class="loading">
        <div class="spinner"></div>
        <div>Checking URL safety...</div>
      </div>
    `;
    positionTooltip(x, y);
    tooltip.classList.add('show');
  }

  function showResultTooltip(x, y, host, result) {
    let tooltipContent = '';
    
    if (!result || !result.success) {
      tooltipContent = `
        <div>Could not analyze this URL.</div>
        <div>The PhishGuard server may be offline.</div>
      `;
      tooltip.innerHTML = tooltipContent;
      positionTooltip(x, y);
      return;
    }
    
    const isPhishing = result.prediction === "Phishy URL";
    
    if (isPhishing) {
      tooltipContent = `
        <div class="warning">⚠️ Warning: Possible phishing attempt!</div>
        <div>This domain <b>${host}</b> appears suspicious.</div>
        <div class="confidence">Confidence: ${(result.confidence * 100).toFixed(1)}%</div>
      `;
    } else {
      tooltipContent = `
        <div class="safe">✓ This URL appears legitimate</div>
        <div class="confidence">Confidence: ${(result.confidence * 100).toFixed(1)}%</div>
      `;
    }
    
    tooltip.innerHTML = tooltipContent;
    positionTooltip(x, y);
  }
  
  function positionTooltip(x, y) {
    tooltip.style.top = (y + 12) + 'px';
    tooltip.style.left = (x + 12) + 'px';
    tooltip.classList.add('show');
  }

  function hideTooltip() {
    tooltip.classList.remove('show');
  }
  
  // Handle messages from popup and background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "getMediaElements") {
      const mediaElements = mediaDetector.scanForMedia();
      sendResponse({ mediaElements });
    } else if (message.action === "highlightSuspiciousMedia") {
      mediaDetector.highlightSuspiciousMedia(message.mediaUrls);
      sendResponse({ success: true });
    } else if (message.action === "clearMediaHighlights") {
      mediaDetector.clearHighlights();
      sendResponse({ success: true });
    }
    return true; // Required for async response
  });
  
  // Initial media scan
  mediaDetector.scanForMedia();
  
  console.log("PhishGuard Enhanced content script loaded");
})();