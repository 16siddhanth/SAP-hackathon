// popup.js - Enhanced popup functionality
class PhishGuardPopup {
    constructor() {
        this.serverUrl = 'http://localhost:5050';
        this.currentTab = null;
        this.mediaElements = [];
        this.init();
    }

    async init() {
        await this.getCurrentTab();
        this.setupEventListeners();
        this.checkServerStatus();
        this.scanPageForMedia();
        this.checkCurrentPageStatus();
    }

    async getCurrentTab() {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        this.currentTab = tab;
    }

    setupEventListeners() {
        // File upload
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        // Button clicks
        document.getElementById('analyzeCurrentPage').addEventListener('click', () => {
            this.analyzeCurrentPage();
        });

        document.getElementById('scanPageMedia').addEventListener('click', () => {
            this.scanPageMediaForDeepfakes();
        });
    }

    async checkServerStatus() {
        try {
            const response = await fetch(`${this.serverUrl}/health`);
            const data = await response.json();
            
            document.getElementById('phishingStatus').textContent = data.phishing_model ? 'Online' : 'Offline';
            document.getElementById('phishingStatus').className = `status-value ${data.phishing_model ? 'online' : 'offline'}`;
            
            document.getElementById('deepfakeStatus').textContent = data.deepfake_detector ? 'Online' : 'Offline';
            document.getElementById('deepfakeStatus').className = `status-value ${data.deepfake_detector ? 'online' : 'offline'}`;
            
        } catch (error) {
            document.getElementById('phishingStatus').textContent = 'Offline';
            document.getElementById('phishingStatus').className = 'status-value offline';
            document.getElementById('deepfakeStatus').textContent = 'Offline';
            document.getElementById('deepfakeStatus').className = 'status-value offline';
        }
    }

    async scanPageForMedia() {
        try {
            const results = await chrome.tabs.sendMessage(this.currentTab.id, {
                action: 'getMediaElements'
            });
            
            this.mediaElements = results.mediaElements || [];
            const count = this.mediaElements.length;
            
            document.getElementById('mediaCount').textContent = 
                count > 0 ? `Found ${count} media element${count !== 1 ? 's' : ''}` : 'No media found';
                
        } catch (error) {
            console.log('Could not scan page for media:', error);
            document.getElementById('mediaCount').textContent = 'Unable to scan page';
        }
    }

    async checkCurrentPageStatus() {
        if (!this.currentTab?.url) return;
        
        try {
            const response = await fetch(`${this.serverUrl}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: this.currentTab.url })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const isPhishy = data.data === 'Phishy URL';
                document.getElementById('pageStatus').textContent = isPhishy ? 'Suspicious' : 'Safe';
                document.getElementById('pageStatus').className = `status-value ${isPhishy ? 'offline' : 'online'}`;
            }
            
        } catch (error) {
            console.log('Could not check page status:', error);
        }
    }

    async analyzeCurrentPage() {
        if (!this.currentTab?.url) return;
        
        this.showLoading('Analyzing current page...');
        
        try {
            const response = await fetch(`${this.serverUrl}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: this.currentTab.url })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const isPhishy = data.data === 'Phishy URL';
                this.showResult({
                    type: isPhishy ? 'fake' : 'real',
                    title: 'URL Analysis',
                    prediction: data.data,
                    confidence: data.confidence,
                    details: `URL: ${this.currentTab.url}`
                });
            } else {
                this.showError('Failed to analyze URL: ' + data.error);
            }
            
        } catch (error) {
            this.showError('Error analyzing page: ' + error.message);
        }
    }

    async scanPageMediaForDeepfakes() {
        if (this.mediaElements.length === 0) {
            this.showError('No media elements found on this page');
            return;
        }
        
        this.showLoading('Scanning media for deepfakes...');
        
        try {
            const response = await fetch(`${this.serverUrl}/scan-page-media`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    page_url: this.currentTab.url,
                    media_sources: this.mediaElements
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.results.length > 0) {
                data.results.forEach(result => {
                    this.showResult({
                        type: result.is_fake ? 'fake' : (result.prediction === 'Error' ? 'error' : 'real'),
                        title: 'Media Analysis',
                        prediction: result.prediction,
                        confidence: result.confidence,
                        details: `Media: ${result.media_url || 'Unknown'}`
                    });
                });
            } else {
                this.showError('No media could be analyzed. Upload files directly for analysis.');
            }
            
        } catch (error) {
            this.showError('Error scanning media: ' + error.message);
        }
    }

    async handleFileUpload(file) {
        if (!file) return;
        
        this.showLoading(`Analyzing ${file.name}...`);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${this.serverUrl}/detect-deepfake`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                const result = data.result;
                this.showResult({
                    type: result.is_fake ? 'fake' : 'real',
                    title: 'File Analysis',
                    prediction: result.prediction,
                    confidence: result.confidence,
                    details: `File: ${data.filename}${result.sample_rate ? ` (${result.sample_rate}Hz)` : ''}`
                });
            } else {
                this.showError('Analysis failed: ' + data.error);
            }
            
        } catch (error) {
            this.showError('Upload failed: ' + error.message);
        }
    }

    showLoading(message) {
        const results = document.getElementById('results');
        results.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>${message}</span>
            </div>
        `;
    }

    showResult(result) {
        const results = document.getElementById('results');
        const resultHtml = `
            <div class="result-item ${result.type}">
                <div class="result-header">
                    <span class="result-prediction">
                        ${result.type === 'fake' ? '🚨' : result.type === 'real' ? '✅' : '⚠️'} 
                        ${result.title}
                    </span>
                    <span class="result-confidence">
                        ${result.confidence ? `${(result.confidence * 100).toFixed(1)}%` : ''}
                    </span>
                </div>
                <div><strong>Result:</strong> ${result.prediction}</div>
                <div style="font-size: 11px; opacity: 0.8; margin-top: 5px;">${result.details}</div>
            </div>
        `;
        
        if (results.querySelector('.loading')) {
            results.innerHTML = resultHtml;
        } else {
            results.insertAdjacentHTML('afterbegin', resultHtml);
        }
    }

    showError(message) {
        this.showResult({
            type: 'error',
            title: 'Error',
            prediction: message,
            confidence: 0,
            details: 'Please try again or check server connection'
        });
    }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PhishGuardPopup();
});
