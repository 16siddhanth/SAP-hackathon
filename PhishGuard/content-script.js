(function() {
  // Create Shadow-DOM tooltip container
  const container = document.createElement('div');
  const shadow = container.attachShadow({ mode: 'closed' });
  document.documentElement.appendChild(container);

  const style = document.createElement('style');
  style.textContent = `
    #phish-tooltip {
      position: absolute;
      padding: 8px;
      background: #fff;
      border: 1px solid #ccc;
      box-shadow: 0 2px 6px rgba(0,0,0,0.2);
      border-radius: 4px;
      font-size: 12px;
      z-index: 2147483647;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.2s;
      max-width: 300px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    #phish-tooltip.show {
      pointer-events: auto;
      opacity: 1;
    }
    #phish-tooltip a {
      color: #0070f3;
      text-decoration: none;
      display: inline-block;
      margin-top: 5px;
      font-weight: bold;
    }
    #phish-tooltip .warning {
      color: #d32f2f;
      font-weight: bold;
      margin-bottom: 5px;
    }
    #phish-tooltip .safe {
      color: #388e3c;
      font-weight: bold;
    }
    #phish-tooltip .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px;
    }
    .spinner {
      width: 20px;
      height: 20px;
      border: 2px solid #f3f3f3;
      border-top: 2px solid #3498db;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-right: 10px;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  shadow.appendChild(style);

  const tooltip = document.createElement('div');
  tooltip.id = 'phish-tooltip';
  shadow.appendChild(tooltip);

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
    
    if (result.isPhishing) {
      if (result.similarTrusted) {
        chrome.storage.local.get('whitelist', (data) => {
          const whitelist = data.whitelist || {};
          const realUrl = whitelist[result.similarTrusted];
          
          tooltipContent = `
            <div class="warning">⚠️ Warning: Possible phishing attempt!</div>
            <div>This domain <b>${host}</b> is not verified.</div>
            <div>It looks similar to: <b>${result.similarTrusted}</b></div>
            <div>Go to the official site instead:</div>
            <a href="${realUrl}" target="_blank" rel="noopener">${new URL(realUrl).hostname}</a>
          `;
          
          tooltip.innerHTML = tooltipContent;
        });
      } else {
        tooltipContent = `
          <div class="warning">⚠️ ${result.message}</div>
          <div>This website has been flagged as potentially dangerous.</div>
          <div>If you're looking for a popular service, try one of these:</div>
        `;
        
        // Show a few trusted alternatives
        chrome.storage.local.get('whitelist', (data) => {
          const whitelist = data.whitelist || {};
          const trustedSites = Object.entries(whitelist).slice(0, 3);
          
          trustedSites.forEach(([domain, url]) => {
            tooltipContent += `<a href="${url}" target="_blank" rel="noopener">${new URL(url).hostname}</a><br>`;
          });
          
          tooltip.innerHTML = tooltipContent;
        });
      }
    } else {
      tooltipContent = `
        <div class="safe">✓ ${result.message}</div>
      `;
      tooltip.innerHTML = tooltipContent;
    }
    
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
})();