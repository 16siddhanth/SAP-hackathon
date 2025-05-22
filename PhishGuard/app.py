import os
import pickle
import sys

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add paths to import the feature extraction code
try:
    sys.path.append('./Phishing_Detection_Using_RandomForest_Algorithms-main/Phishing_Detection_Using_RandomForest_Algorithms-main/feature_extraction')
    from feature_extractor import extract_features
    print("Successfully imported feature_extractor from the RandomForest project")
except ImportError:
    # Use the backup feature extractor if the import fails
    print("Using backup feature extractor")
    from feature_extractor_helper import extract_features

app = Flask(__name__)
CORS(app)  # Enable CORS for browser extension access

# Load the trained model
MODEL_PATH = './Phishing_Detection_Using_RandomForest_Algorithms-main/Phishing_Detection_Using_RandomForest_Algorithms-main/trained_models/randomForest.pkl'

# Load the model (with error handling)
try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    # If you don't have the model file ready, you'll need to train it
    model = None

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400
    
    try:
        # Extract features from the URL
        features = extract_features(url)
        
        # If model is available, use it for prediction
        if model is not None:
            # Reshape features for prediction
            features_df = pd.DataFrame([features])
            prediction = model.predict(features_df)[0]
            confidence = model.predict_proba(features_df)[0].max()
            
            # Format response for the extension
            result = "Phishy URL" if prediction == 1 else "Legitimate URL"
            
            return jsonify({
                'success': True,
                'data': result,
                'confidence': float(confidence)
            })
        else:
            # Fallback if model isn't loaded
            # Simple heuristic - check if URL is in your phishy.txt
            phishy_urls = []
            phishy_path = './Phishing_Detection_Using_RandomForest_Algorithms-main/Phishing_Detection_Using_RandomForest_Algorithms-main/url_txt_files/phishy.txt'
            if os.path.exists(phishy_path):
                with open(phishy_path, 'r') as f:
                    phishy_urls = f.read().splitlines()
            
            if any(url.strip() == phishy_url.strip() for phishy_url in phishy_urls):
                return jsonify({
                    'success': True,
                    'data': "Phishy URL",
                    'confidence': 0.9
                })
            else:
                return jsonify({
                    'success': True,
                    'data': "Legitimate URL",
                    'confidence': 0.7
                })
    
    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
