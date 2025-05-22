# PhishGuard Detailed Setup Guide

This guide provides in-depth instructions for setting up and running the PhishGuard extension with the RandomForest phishing detection model.

## System Requirements

- Windows, macOS, or Linux
- Python 3.8 or higher
- Google Chrome or Chromium-based browser
- At least 500MB of free disk space
- 4GB of RAM recommended

## Installation Steps

### 1. Python Environment Setup

First, ensure you have Python 3.8+ installed. You can check your Python version with:

```
python --version
```

#### Install Required Python Packages

Navigate to the PhishGuard directory:

```
cd PhishGuard
```

Install dependencies using pip:

```
pip install flask flask-cors pandas numpy scikit-learn tldextract requests beautifulsoup4
```

If you encounter permission issues, try:

```
pip install --user flask flask-cors pandas numpy scikit-learn tldextract requests beautifulsoup4
```

Or if you have both Python 2 and 3 installed:

```
pip3 install flask flask-cors pandas numpy scikit-learn tldextract requests beautifulsoup4
```

### 2. Flask API Server Configuration

The API server uses the RandomForest model to analyze URLs. The model should be located at:

```
Phishing_Detection_Using_RandomForest_Algorithms-main/Phishing_Detection_Using_RandomForest_Algorithms-main/trained_models/randomForest.pkl
```

If the model file is missing, you can train it using the scripts in the RandomForest project:

```
cd Phishing_Detection_Using_RandomForest_Algorithms-main/Phishing_Detection_Using_RandomForest_Algorithms-main
python main.py
```

This will train a new model and save it to the correct location.

### 3. Starting the API Server

From the PhishGuard directory, run:

```
python app.py
```

Alternatively, you can use the batch file:

```
start_server.bat
```

Verify the server is running by opening http://127.0.0.1:5000 in your browser. You should see a JSON response indicating the API is active.

### 4. Extension Directory Preparation

Before loading the extension, make sure there are no `__pycache__` directories in the extension folder:

```
rmdir /s /q __pycache__
```

### 5. Loading the Extension in Chrome

1. Open Chrome
2. Navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top-right corner
4. Click "Load unpacked"
5. Select the PhishGuard directory
6. The extension should appear with its icon

If you encounter an error about `__pycache__` or files starting with `_`, you can create a clean extension directory:

```
mkdir PhishGuardExt
copy PhishGuard\background.js PhishGuardExt\
copy PhishGuard\content-script.js PhishGuardExt\
copy PhishGuard\manifest.json PhishGuardExt\
mkdir PhishGuardExt\icons
copy PhishGuard\icons\*.* PhishGuardExt\icons\
```

Then load the extension from this clean directory.

## Testing the Extension

1. After loading the extension, navigate to any website with external links
2. Hover over a link and wait for the PhishGuard tooltip to appear (about 0.5 seconds)
3. The tooltip will indicate whether the link is safe or potentially dangerous

Test with known safe sites:
- https://www.google.com
- https://www.microsoft.com
- https://www.github.com

To test phishing detection, you can use these patterns (don't actually visit these!):
- URLs with IP addresses (http://192.168.1.1/login)
- Misspelled domains (googgle.com, paypal-secure.com)
- URLs with excessive subdomains (login.account.secure.bank.example.com)
- URLs with suspicious TLDs (.tk, .ml, .cf)

## Troubleshooting

### Flask Server Issues

If the Flask server won't start:

1. **ModuleNotFoundError**: Install the missing package with `pip install <package_name>`
2. **Address already in use**: Another process is using port 5000. Find and close it, or modify the port in `app.py`
3. **Model loading error**: Check the path to the model file in `app.py` and make sure it exists

### Extension Loading Issues

If the extension won't load:

1. **Cannot load extension with file or directory name __pycache__**: Remove all `__pycache__` directories
2. **Manifest file missing or invalid**: Check that your `manifest.json` is properly formatted
3. **Could not load background script**: Verify that `background.js` has no syntax errors

### Extension Not Working

If the extension loads but doesn't work:

1. **No tooltip appears**: Check the browser console for errors in the content script
2. **API connection error**: Make sure the Flask server is running and check for CORS issues
3. **Incorrect results**: Verify the model is loaded correctly and test the API directly

## Advanced Configuration

### Customizing the Whitelist

Edit the defaultWhitelist in `background.js` to add trusted domains:

```javascript
const defaultWhitelist = {
  "paypal.com": "https://www.paypal.com/signin",
  "bankxyz.com": "https://online.bankxyz.com/login",
  "google.com": "https://accounts.google.com/signin",
  "yourbank.com": "https://secure.yourbank.com/login"
};
```

### Modifying API Endpoint

If you want to run the API on a different machine or port, change the fetch URL in `background.js`:

```javascript
fetch('http://your-api-server:port/predict', {
```

### Adjusting Cache Duration

The result cache can be modified in `background.js` to change how long results are remembered:

```javascript
// Add cache expiration logic
setInterval(() => {
  const now = Date.now();
  for (const url in resultCache) {
    if (now - resultCache[url].timestamp > 3600000) { // 1 hour
      delete resultCache[url];
    }
  }
}, 300000); // Check every 5 minutes
```

## Security Considerations

- The extension requires permissions to read content on all sites to detect links
- API communication is done over HTTP for local testing; use HTTPS for production
- The whitelist feature is critical for protecting trusted domains

## Additional Resources

- For more details on the RandomForest algorithm, check the `/Phishing_Detection_Using_RandomForest_Algorithms-main` directory
- Chrome extension documentation: https://developer.chrome.com/docs/extensions/
- Flask documentation: https://flask.palletsprojects.com/
