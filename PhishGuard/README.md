.# PhishGuard: ML-Powered Phishing Detection

A Chrome extension that uses a RandomForest machine learning model to protect users from phishing websites in real-time.

## Overview

PhishGuard consists of two main components:
1. A Chrome browser extension that displays a tooltip when hovering over links
2. A Flask API server that analyzes URLs using the RandomForest algorithm

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- Internet connection (for API communication)

## Step-by-Step Setup Guide

### 1. Install Python Dependencies

Open a command prompt and navigate to the PhishGuard directory:

```
cd PhishGuard
```

Install the required Python packages:

```
pip install flask flask-cors pandas numpy scikit-learn tldextract requests beautifulsoup4
```

Or use the requirements file:

```
pip install -r requirements.txt
```

### 2. Start the Flask API Server

From the same directory, run:

```
python app.py
```

You should see output similar to:
```
Starting PhishGuard API server on http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Keep this window open while using the extension.

### 3. Load the Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in the top-right corner)
3. Click "Load unpacked"
4. Navigate to the PhishGuard directory and select it
5. The PhishGuard extension should now appear in your extensions list

**Important Note:** If you see an error about `__pycache__` or files starting with `_`, you can either:
- Delete the `__pycache__` directory before loading the extension
- Or use the batch file `start_server.bat` to start the server, which will handle this for you

### 4. Verify the Extension is Working

1. Navigate to any website with links
2. Hover over a link and wait for the PhishGuard tooltip to appear
3. The tooltip will show whether the URL is safe or potentially dangerous

## How It Works

1. **URL Detection**: When you hover over a link, the content script sends the URL to the background script
2. **Whitelist Check**: The URL is first checked against a whitelist of trusted domains
3. **API Analysis**: If not in the whitelist, the URL is sent to the Flask API
4. **Machine Learning**: The API extracts features from the URL and uses the RandomForest model to classify it
5. **Result Display**: A tooltip shows the analysis result (safe or phishing)
6. **Fallback Protection**: If the API is unavailable, pattern-based detection is used as a fallback

## Features

- **Machine Learning Detection**: Uses RandomForest algorithm from the `Phishing_Detection_Using_RandomForest_Algorithms` project
- **Real-time Analysis**: Instantly analyzes URLs as you browse
- **Whitelist System**: Maintains a list of trusted domains for quick verification
- **Similar Domain Detection**: Identifies URLs that try to mimic legitimate websites
- **Elegant UI**: Non-intrusive tooltip with clear safety indicators
- **Offline Fallback**: Pattern-based detection when the API is unavailable
- **Result Caching**: Stores results to reduce repeated API calls

## Troubleshooting

- **Extension not loading**: Make sure there are no files or folders starting with `_` in the extension directory
- **API connection errors**: Ensure the Flask server is running at http://127.0.0.1:5000
- **Model not found**: Check that the path to `randomForest.pkl` is correct in `app.py`
- **Dependencies missing**: Run `pip install -r requirements.txt` to install all required packages

## Advanced Configuration

You can modify the `config.json` file to customize:
- Whitelist of trusted domains
- API endpoint settings
- Caching behavior
- Detection thresholds

## Development

To modify the extension:
- `background.js`: Contains the core logic for URL checking
- `content-script.js`: Handles the tooltip UI and user interaction
- `app.py`: Flask server that provides the ML-based detection API
- `feature_extractor_helper.py`: Extracts features from URLs for analysis

## License

Open source under MIT license. See LICENSE file for details.
