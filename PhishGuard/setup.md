# PhishGuard Enhanced - Setup Guide

This guide will help you set up the PhishGuard Enhanced browser extension with both phishing URL detection and deepfake audio/video detection capabilities.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Chrome browser (v88+) or Firefox (v78+)
- ffmpeg (for audio extraction from videos)

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd PhishGuard
```

## Step 2: Set Up the Python Environment

Create and activate a virtual environment:

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
# Install the enhanced requirements
pip install -r requirements-enhanced.txt
```

## Step 4: Ensure ffmpeg is installed

ffmpeg is required for audio extraction from video files.

### macOS

```bash
brew install ffmpeg
```

### Windows

1. Download from https://ffmpeg.org/download.html
2. Extract the files
3. Add the bin folder to your PATH environment variable

### Linux

```bash
sudo apt update
sudo apt install ffmpeg
```

## Step 5: Start the Backend Server

```bash
# Start the enhanced server
python app_enhanced.py
```

This will start the server at `http://localhost:5000`. You should see the following output:

```
🚀 Starting PhishGuard Enhanced Server...
📊 Phishing Model: ✅
🎵 Deepfake Detector: ✅
🌐 Server running on http://localhost:5000
📱 Extension endpoints available
```

## Step 6: Install the Browser Extension

### Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" by toggling the switch in the top right corner
3. Click "Load unpacked" and select the PhishGuard directory
4. The extension should now be installed and active

### Firefox

1. Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on..." and select the `manifest.json` file from the PhishGuard directory
3. The extension should now be installed and active

## Step 7: Test the Extension

### URL Safety Testing

1. Navigate to any website
2. Hover over links to see the URL safety analysis
3. The extension will show whether the URL is safe or potentially malicious

### Deepfake Audio/Video Detection

1. Click the extension icon to open the popup
2. You can:
   - Upload audio/video files for analysis
   - Scan the current page for media elements
   - Analyze individual media files via right-click context menu

## Advanced Configuration

You can modify the server configuration in `config.json`:

```json
{
  "serverUrl": "http://localhost:5050",
  "deepfakeDetectionEnabled": true,
  "phishingDetectionEnabled": true,
  "mediaHighlightingEnabled": true
}
```

## Troubleshooting

### Server Connection Issues

- Ensure the server is running at http://localhost:5000
- Check the server logs for any errors
- Verify that the required ports are not blocked by a firewall

### Model Loading Issues

- If the models fail to load, check your internet connection as they'll be downloaded from Hugging Face
- Ensure you have sufficient disk space (the models require approximately 1.5GB)

### Audio/Video Processing Issues

- Verify that ffmpeg is correctly installed and in your PATH
- Check the server logs for specific error messages
- Ensure the uploaded media files are not corrupted

### Extension Not Working

- Check the browser console for any JavaScript errors
- Verify that the extension is properly installed and enabled
- Try reloading the extension

## Notes on Model Performance

- The deepfake audio detection model works best on speech content
- Short audio clips (< 3 seconds) may yield less accurate results
- The model is specifically trained for 16kHz audio (conversion happens automatically)
- Very noisy audio may reduce detection accuracy

## Security and Privacy

- All processing happens locally on your machine
- No audio/video data is sent to external servers (only to your local server)
- URL analysis is done using machine learning models running on your computer
