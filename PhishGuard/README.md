# PhishGuard Enhanced

![PhishGuard Logo](icons/icon128.png)

## 🛡️ Advanced Phishing & Deepfake Detection Extension

PhishGuard Enhanced is a powerful browser extension that protects you from both phishing URLs and deepfake audio/video content, leveraging advanced machine learning models.

## Features

### 🌐 Phishing Protection
- **URL Safety Analysis**: Automatically checks links for phishing attempts
- **Real-time Warnings**: Displays clear alerts when hovering over suspicious links
- **Machine Learning-Powered**: Uses RandomForest ML model for accurate detection

### 🎵 Deepfake Audio/Video Detection
- **Audio Analysis**: Detects synthetic or manipulated voice content
- **Video Support**: Analyzes video files by extracting and examining audio
- **16kHz Processing**: Automatically resamples audio to ensure optimal detection
- **Multiple Format Support**: Handles WAV, MP3, MP4, AVI and many other formats

### ⚙️ Additional Features
- **Page Media Scanning**: Automatically finds and analyzes media elements on websites
- **Visual Highlighting**: Marks suspicious media elements with a warning outline
- **File Upload**: Analyze your own media files for manipulation
- **Context Menu Integration**: Right-click on media to check for deepfakes

## Technology Stack

- **Frontend**: JavaScript browser extension
- **Backend**: Python Flask API
- **ML Models**:
  - RandomForest (URL phishing detection)
  - Wav2Vec2 model fine-tuned for deepfake detection
- **Audio Processing**: librosa, soundfile
- **Media Handling**: ffmpeg for audio extraction

## Getting Started

See the [SETUP_ENHANCED.md](SETUP_ENHANCED.md) file for complete setup instructions.

## How It Works

### Phishing Detection
The extension analyzes URLs using a RandomForest machine learning model trained on features extracted from known phishing and legitimate websites. Features include domain age, URL length, special characters, TLS/SSL certificate information, and more.

### Deepfake Detection
Audio deepfake detection uses a fine-tuned Wav2Vec2 model that analyzes spectral and temporal patterns in speech to identify synthetic or manipulated content. The model has been trained on a large dataset of real and fake audio samples, achieving high accuracy in distinguishing between authentic and synthesized speech.

## Security & Privacy

- All processing happens locally on your machine
- No audio/video content is sent to external servers
- Only uses your local server running on localhost
- No data collection or tracking

## Requirements

- Python 3.8+
- Chrome (v88+) or Firefox (v78+)
- ffmpeg (for video processing)
- 2GB+ RAM
- 1.5GB disk space for models

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Wav2Vec2 base model by Facebook AI Research
- DeepFake-Audio-Rangers for the fine-tuned detection model
- RandomForest phishing detection algorithms