import os
import sys
import traceback
import joblib
import tempfile
import numpy as np
import soundfile as sf
import librosa
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForSequenceClassification # Changed Wav2Vec2Processor to Wav2Vec2FeatureExtractor

# Attempt to import the optimized feature extractor first
FEATURE_EXTRACTOR_AVAILABLE = False
OPTIMIZED_EXTRACTOR_ERROR = None
try:
    from feature_extractor_optimized import extract_url_features
    FEATURE_EXTRACTOR_AVAILABLE = True
    print("Successfully imported 'feature_extractor_optimized.extract_url_features'")
except ImportError as e_opt:
    OPTIMIZED_EXTRACTOR_ERROR = str(e_opt)
    print(f"Could not import 'feature_extractor_optimized'. Error: {OPTIMIZED_EXTRACTOR_ERROR}")
    # Fallback to the helper if the optimized one is not available
    try:
        from feature_extractor_helper import extract_url_features
        FEATURE_EXTRACTOR_AVAILABLE = True
        print("Successfully imported 'feature_extractor_helper.extract_url_features' as fallback.")
    except ImportError as e_helper:
        print(f"Could not import 'feature_extractor_helper' either. Error: {e_helper}")
        # As a last resort, try the original, potentially problematic one if it exists
        try:
            # This path might be specific and needs to be correct if used
            # For now, let's assume it's not the primary way to get extract_url_features
            # from Phishing_Detection_Using_RandomForest_Algorithms-main.Phishing_Detection_Using_RandomForest_Algorithms-main.feature_extraction.feature_extractor import extract_url_features
            # FEATURE_EXTRACTOR_AVAILABLE = True # Uncomment if this path is valid and tested
            # print("Successfully imported from complex path as last resort.")
            pass # Keep this commented unless absolutely sure about the path and its stability
        except ImportError as e_orig:
            print(f"Could not import from the original complex path either. Error: {e_orig}")
            print("Critical: No feature extractor could be imported. URL phishing detection will fail.")
            # Define a dummy function if none are available to prevent NameError, but log critical failure
            def extract_url_features(url):
                print("CRITICAL ERROR: No feature extractor loaded. Returning None.")
                return None 

app = Flask(__name__)
CORS(app)

# Initialize deepfake detection model
DEEPFAKE_MODEL = None
DEEPFAKE_PROCESSOR = None

# Construct the absolute path to the directory containing app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_deepfake_model():
    """Load the deepfake detection model"""
    global DEEPFAKE_MODEL, DEEPFAKE_PROCESSOR
    try:
        print("Loading deepfake detection model...")
        # Set cache directory explicitly to avoid permission issues
        cache_dir = os.path.join(BASE_DIR, "model_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        model_name = "DeepFake-Audio-Rangers/DeepfakeDetect_wav2vec2"
        
        # Load feature extractor instead of processor
        DEEPFAKE_PROCESSOR = Wav2Vec2FeatureExtractor.from_pretrained( # Changed here
            model_name,
            cache_dir=cache_dir,
            local_files_only=False 
        )
        
        # Load the deepfake detection model
        DEEPFAKE_MODEL = Wav2Vec2ForSequenceClassification.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            local_files_only=False # Set to True after first download if desired
        )
        
        # Test the model with a small audio sample to verify it works
        print("Verifying deepfake model with a test inference...")
        test_audio = np.random.rand(16000).astype(np.float32)  # 1 second of random noise at 16kHz
        test_inputs = DEEPFAKE_PROCESSOR(test_audio, sampling_rate=16000, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = DEEPFAKE_MODEL(test_inputs.input_values).logits
        # Test inference successful if no exception
        print(f"Test inference produced logits: {logits.shape}")
        print("Deepfake detection model loaded and verified successfully!")
        return True
    except Exception as e:
        print(f"Error loading deepfake model: {e}")
        traceback.print_exc()
        return False

def detect_deepfake_audio(audio_path):
    """Detect if audio is deepfake using the actual model"""
    try:
        if DEEPFAKE_MODEL is None or DEEPFAKE_PROCESSOR is None:
            print("Deepfake model not loaded.")
            return {
                'prediction': 'Error',
                'confidence': 0.0,
                'is_fake': False,
                'error': 'Deepfake model not loaded'
            }
        
        # Read audio file
        audio_input, sample_rate = sf.read(audio_path)

        # If stereo, convert to mono by averaging channels
        if audio_input.ndim > 1 and audio_input.shape[1] > 1:
            audio_input = np.mean(audio_input, axis=1)
        
        # Always resample to 16kHz as required by the model
        if sample_rate != 16000:
            print(f"Resampling audio from {sample_rate} Hz to 16000 Hz")
            audio_input = librosa.resample(y=audio_input.astype(np.float32), orig_sr=sample_rate, target_sr=16000)
            sample_rate = 16000
        
        # Ensure the audio is long enough for the model
        min_samples = 24000  # 1.5 seconds
        if len(audio_input) < min_samples:
            print(f"Audio input length {len(audio_input)} is less than min_samples {min_samples}. Padding...")
            audio_input = np.pad(audio_input, (0, max(0, min_samples - len(audio_input))), mode='constant')
            print(f"Padded audio to {len(audio_input)} samples.")
        
        # Process audio
        inputs = DEEPFAKE_PROCESSOR(
            audio_input, 
            sampling_rate=sample_rate,
            return_tensors="pt", 
            padding=True
        )
        
        with torch.no_grad():
            logits = DEEPFAKE_MODEL(inputs.input_values).logits
        
        predicted_class_id = torch.argmax(logits, dim=-1).item()
        labels = DEEPFAKE_MODEL.config.id2label
        prediction = labels[predicted_class_id]
        
        probabilities = torch.softmax(logits, dim=-1)
        confidence = float(probabilities[0][predicted_class_id])
        
        is_fake = 'fake' in prediction.lower() or 'spoof' in prediction.lower()
        
        print(f"Deepfake detection result: Prediction={prediction}, Confidence={confidence:.4f}, IsFake={is_fake}")
        return {
            'prediction': prediction,
            'confidence': confidence,
            'is_fake': is_fake,
            'sample_rate': sample_rate
        }
        
    except Exception as e:
        print(f"Error detecting deepfake: {e}")
        traceback.print_exc()
        return {
            'prediction': 'Error',
            'confidence': 0.0,
            'is_fake': False,
            'error': str(e)
        }

# Load the phishing detection model
# Construct the absolute path to the model file
MODEL_PATH = os.path.join(BASE_DIR, 'Phishing_Detection_Using_RandomForest_Algorithms-main', 'Phishing_Detection_Using_RandomForest_Algorithms-main', 'trained_models', 'randomForest.pkl')

try:
    model = joblib.load(MODEL_PATH)
    print("Phishing detection model loaded successfully!")
except Exception as e:
    print(f"Error loading phishing model: {e}")
    model = None

# Load deepfake model on startup
deepfake_available = load_deepfake_model()

@app.route('/')
def index():
    return "PhishGuard Enhanced Server is running"

@app.route('/health')
def health_check():
    return jsonify({
        'phishing_model': model is not None,
        'deepfake_detector': deepfake_available and DEEPFAKE_MODEL is not None
    })

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
    
    try:
        if model is None:
            return jsonify({'success': False, 'error': 'Phishing model not loaded'}), 500

        if FEATURE_EXTRACTOR_AVAILABLE:
            print(f"Extracting features for URL: {url} using primary extractor")
            features = extract_url_features(url)
        else:
            print(f"Extracting features for URL: {url} using backup extractor")
            features = extract_url_features(url)

        if features is None:
             return jsonify({'success': False, 'error': 'Could not extract features for the URL.'}), 500

        if isinstance(features, list) and (not features or not isinstance(features[0], list)):
            features_for_prediction = [features]
        else:
            features_for_prediction = features
            
        prediction = model.predict(features_for_prediction)
        probabilities = model.predict_proba(features_for_prediction)
        
        is_phishing = bool(prediction[0])
        confidence_score = float(probabilities[0][prediction[0]]) * 100 # Get confidence for the predicted class
        
        print(f"Prediction for {url}: {'Phishing' if is_phishing else 'Benign'}, Confidence: {confidence_score:.2f}%")
        return jsonify({'success': True, 'url': url, 'is_phishing': is_phishing, 'confidence': confidence_score})
    
    except Exception as e:
        print(f"Error during prediction for URL {url}: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# Deepfake Detection Endpoints
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4', 'avi', 'mov', 'flac', 'ogg', 'm4a', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_audio_from_video(video_path, output_path):
    """Extract audio from video file using librosa"""
    try:
        # Load video and extract audio, resample to 16kHz directly
        audio, sr = librosa.load(video_path, sr=16000, mono=True) 
        
        # Ensure the audio is at least 1.5 seconds long (24000 samples at 16kHz)
        min_samples = 24000 
        if len(audio) < min_samples:
            audio = np.pad(audio, (0, max(0, min_samples - len(audio))), mode='constant')
            print(f"Extracted audio was too short, padded to {min_samples} samples")
        
        # Save as wav file
        sf.write(output_path, audio, sr) # sr will be 16000
        print(f"Audio extracted successfully to {output_path}, sr={sr}, length={len(audio)}")
        return True, sr
    except Exception as e:
        print(f"Error extracting audio: {e}")
        traceback.print_exc()
        return False, None

@app.route('/detect-deepfake', methods=['POST'])
def detect_deepfake():
    """Deepfake detection endpoint for uploaded files"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part in the request'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not supported'}), 400
        
        upload_dir = tempfile.mkdtemp()
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        print(f"File saved to temporary path: {filepath}")
        
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        analysis_path = filepath
        original_sample_rate = None

        if file_ext in ['mp4', 'avi', 'mov', 'webm']:
            print(f"Video file detected: {filename}. Extracting audio...")
            audio_path = os.path.join(upload_dir, f"extracted_audio_{os.path.splitext(filename)[0]}.wav")
            success, extracted_sr = extract_audio_from_video(filepath, audio_path)
            if not success:
                # Clean up temp dir
                if os.path.exists(filepath): os.remove(filepath)
                if os.path.exists(audio_path): os.remove(audio_path)
                os.rmdir(upload_dir)
                return jsonify({'success': False, 'error': 'Failed to extract audio from video'}), 500
            analysis_path = audio_path
            # original_sample_rate will be None here, as extract_audio_from_video resamples to 16k
        else: # It's an audio file
            # For audio files, we might want to know their original sample rate before our processing
            try:
                with sf.SoundFile(filepath) as f_info:
                    original_sample_rate = f_info.samplerate
                print(f"Audio file detected: {filename}, original_sample_rate: {original_sample_rate}")
            except Exception as e:
                print(f"Could not read original sample rate for {filename}: {e}")

        print(f"Performing deepfake detection on: {analysis_path}")
        result = detect_deepfake_audio(analysis_path)
        
        # Add file info to the result, if not already there from detect_deepfake_audio
        result['filename'] = filename
        result['file_type'] = file_ext
        if original_sample_rate and 'original_sample_rate' not in result:
            result['original_sample_rate'] = original_sample_rate
        if 'sample_rate' not in result and 'extracted_sr' in locals():
            result['processed_sample_rate'] = extracted_sr

        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
        if 'audio_path' in locals() and os.path.exists(audio_path):
            if analysis_path != filepath and os.path.exists(analysis_path):
                os.remove(analysis_path)
        os.rmdir(upload_dir)
        print(f"Cleaned up temporary files and directory: {upload_dir}")
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        print(f"Error in /detect-deepfake endpoint: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/scan-page-media', methods=['POST'])
def scan_page_media():
    """Scan media elements found on a webpage"""
    try:
        data = request.get_json()
        page_url = data.get('page_url', '')
        media_sources = data.get('media_sources', [])
        
        if not media_sources:
            return jsonify({'success': False, 'error': 'No media sources provided'}), 400
        
        results = []
        for media_url in media_sources:
            # For remote media, we can't analyze directly without downloading
            result = {
                'media_url': media_url,
                'prediction': 'Cannot analyze remote media directly - upload file for analysis',
                'confidence': 0.0,
                'is_fake': False
            }
            results.append(result)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/detect_deepfake_url', methods=['POST'])
def detect_deepfake_url():
    """Endpoint called by background.js for media URL analysis"""
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        # For demonstration, we can't directly analyze remote media URLs
        # In a real implementation, you might download and analyze the file
        result = {
            'prediction': 'Cannot analyze remote media directly',
            'confidence': 0.0,
            'is_fake': False,
            'note': 'Use file upload for accurate deepfake detection'
        }
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting PhishGuard Enhanced Server...")
    print(f"📊 Phishing Model: {'✅' if model is not None else '❌'}")
    print(f"🎵 Deepfake Detector: {'✅' if deepfake_available else '❌'}")
    print("🌐 Server running on http://localhost:5000")
    print("📱 Extension endpoints available")
    app.run(debug=True, port=5000)
