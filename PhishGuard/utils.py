"""
Utility script for managing the PhishGuard extension and server.
"""

import argparse
import json
import os
import pickle
import shutil
import sys

import pandas as pd


def check_environment():
    """Check if all required files are present and environment is set up correctly."""
    print("Checking PhishGuard environment...")
    
    # Check if config file exists
    if not os.path.exists('config.json'):
        print("❌ config.json not found")
        return False
    
    # Check if model file exists
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    model_path = config['model']['path']
    if not os.path.exists(model_path):
        print(f"❌ Model file not found at {model_path}")
        return False
    else:
        print(f"✅ Model file found at {model_path}")
    
    # Check if Python requirements are installed
    try:
        import flask
        import flask_cors
        import numpy
        import pandas
        import sklearn
        print("✅ Required Python packages are installed")
    except ImportError as e:
        print(f"❌ Missing Python package: {str(e)}")
        print("Run 'pip install -r requirements.txt' to install required packages")
        return False
    
    # Check if extension files exist
    required_files = ['background.js', 'content-script.js', 'manifest.json']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing extension files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All extension files found")
    
    print("✅ Environment check completed successfully")
    return True

def update_whitelist(domains_to_add=None, domains_to_remove=None):
    """Update the whitelist in config.json."""
    if not os.path.exists('config.json'):
        print("❌ config.json not found")
        return
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    whitelist = config['whitelist']['trusted_domains']
    
    if domains_to_add:
        for domain in domains_to_add:
            if domain not in whitelist:
                whitelist.append(domain)
                print(f"Added {domain} to whitelist")
    
    if domains_to_remove:
        for domain in domains_to_remove:
            if domain in whitelist:
                whitelist.remove(domain)
                print(f"Removed {domain} from whitelist")
    
    config['whitelist']['trusted_domains'] = whitelist
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("✅ Whitelist updated successfully")

def test_model():
    """Test the model with a few sample URLs."""
    model_path = './Phishing_Detection_Using_RandomForest_Algorithms-main/Phishing_Detection_Using_RandomForest_Algorithms-main/trained_models/randomForest.pkl'
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found at {model_path}")
        return
    
    try:
        # Try to load the model
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        print("✅ Model loaded successfully")
        
        # Try feature extraction
        try:
            # First try to use the original feature extractor
            sys.path.append('./Phishing_Detection_Using_RandomForest_Algorithms-main/Phishing_Detection_Using_RandomForest_Algorithms-main/feature_extraction')
            from feature_extractor import extract_features
        except ImportError:
            # Use the backup feature extractor
            from feature_extractor_helper import extract_features
        
        # Test URLs
        test_urls = [
            "https://www.google.com",
            "https://www.paypal.com/signin",
            "http://googlee.com.phishing.example.com"
        ]
        
        print("\nTesting model with sample URLs:")
        for url in test_urls:
            try:
                features = extract_features(url)
                features_df = pd.DataFrame([features])
                prediction = model.predict(features_df)[0]
                confidence = model.predict_proba(features_df)[0].max()
                
                result = "Phishing" if prediction == 1 else "Legitimate"
                print(f"{url}: {result} (confidence: {confidence:.2f})")
            except Exception as e:
                print(f"Error testing {url}: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error testing model: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PhishGuard Utility Script")
    parser.add_argument("--check", action="store_true", help="Check environment setup")
    parser.add_argument("--add-domain", nargs="+", help="Add domains to whitelist")
    parser.add_argument("--remove-domain", nargs="+", help="Remove domains from whitelist")
    parser.add_argument("--test-model", action="store_true", help="Test the model with sample URLs")
    
    args = parser.parse_args()
    
    if args.check:
        check_environment()
    elif args.add_domain:
        update_whitelist(domains_to_add=args.add_domain)
    elif args.remove_domain:
        update_whitelist(domains_to_remove=args.remove_domain)
    elif args.test_model:
        test_model()
    else:
        parser.print_help()
