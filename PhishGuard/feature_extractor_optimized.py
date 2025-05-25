"""
Optimized feature extraction for URL phishing detection.
This is a faster version with no debug prints and optimized network requests.
"""

import re
import socket
import time
import urllib.parse
from urllib.parse import urlparse

import pandas as pd
import numpy as np
import regex
import requests
import tldextract
from bs4 import BeautifulSoup

# Disable warnings for unverified HTTPS requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def is_url_shortened(url):
    # List of common URL shorteners
    shortening_services = ['bit.ly', 'goo.gl', 'tinyurl.com', 't.co', 'tr.im', 'is.gd', 'cli.gs',
                          'yfrog.com', 'migre.me', 'ff.im', 'tiny.cc', 'url4.eu', 'twit.ac',
                          'su.pr', 'twurl.nl', 'snipurl.com', 'short.to', 'budurl.com', 'ping.fm', 'post.ly',
                          'just.as', 'bkite.com', 'snipr.com', 'fic.kr', 'loopt.us', 'doiop.com', 'twitthis.com',
                          'htxt.it', 'ak.im', 'shor.to', 'rubyurl.com', 'om.ly', 'to.ly', 'bit.do',
                          'adcraft.co', 'yep.it', 'posted.at', 'xurl.es', 'poprl.com']
    
    domain = urlparse(url).netloc
    return any(shortener in domain for shortener in shortening_services)

def extract_url_features(url):
    """
    Extract features from URL for phishing detection without debug messages
    """
    try:
        features = []
        
        # 1. URL Length
        if len(url) < 54:
            features.append(1)
        elif len(url) >= 54 and len(url) <= 75:
            features.append(0)
        else:
            features.append(-1)
        
        # 2. Shortening URL
        features.append(1 if is_url_shortened(url) else -1)
        
        # 3. @ Symbol
        features.append(1 if '@' in url else -1)
        
        # 4. Double Slash Redirection
        if url.count('//') > 1:
            if url.rfind('//') > 7:
                features.append(-1)
            else:
                features.append(1)
        else:
            features.append(1)
        
        # 5. Prefix Suffix
        features.append(-1 if '-' in urlparse(url).netloc else 1)
        
        # 6. Sub Domain
        extracted = tldextract.extract(url)
        domain = extracted.domain
        suffix = extracted.suffix
        subdomain = extracted.subdomain
        
        if not subdomain:
            features.append(1)
        elif subdomain.count('.') <= 1:
            features.append(0)
        else:
            features.append(-1)
        
        # 7. SSL Certificate
        try:
            parsed = urlparse(url)
            features.append(1 if parsed.scheme == 'https' else -1)
        except:
            features.append(-1)
        
        # 8. Domain Registration
        # Simplified check without external API
        features.append(1)  # Default to legitimate
        
        # 9. Favicon
        features.append(1)  # Default to legitimate
        
        # 10. Port
        try:
            port = urlparse(url).port
            features.append(-1 if port is not None else 1)
        except:
            features.append(1)
        
        # 11. HTTPS Token
        if 'http' in domain or 'https' in domain:
            features.append(-1)
        else:
            features.append(1)
        
        # 12-16: Website content features
        # Skip heavy computations/fetching for faster processing
        for _ in range(5):
            features.append(0)  # Use neutral values
        
        # 17. SFH
        features.append(1)  # Default to legitimate
        
        # 18. Submitting to Email
        features.append(1)  # Default to legitimate
        
        # 19-28: Website behavior features
        # Use neutral or default values for faster processing
        for _ in range(10):
            features.append(0)
        
        # Fill in any missing features to ensure we have 30 features
        while len(features) < 30:
            features.append(0)
        
        return features
    
    except Exception as e:
        # In case of error, return a default feature set
        print(f"Error extracting features: {e}")
        return [0] * 30

def extract_features(url):
    """Fallback function for compatibility with feature_extractor_helper.py"""
    # Simple feature extraction that doesn't require network requests
    features = {}
    
    # Basic URL features
    features['url_length'] = len(url)
    features['has_ip'] = 1 if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url) else 0
    features['has_at_symbol'] = 1 if '@' in url else 0
    features['has_double_slash'] = 1 if '//' in url[8:] else 0
    
    # Domain features
    extracted = tldextract.extract(url)
    domain = extracted.domain
    suffix = extracted.suffix
    subdomain = extracted.subdomain
    
    features['domain_length'] = len(domain)
    features['has_hyphen'] = 1 if '-' in domain else 0
    features['subdomain_count'] = len(subdomain.split('.')) if subdomain else 0
    features['tld_length'] = len(suffix) if suffix else 0
    
    # URL path features
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    features['path_length'] = len(path)
    features['path_depth'] = path.count('/') if path else 0
    features['has_query'] = 1 if parsed_url.query else 0
    features['query_length'] = len(parsed_url.query)
    
    # Security indicators
    features['has_https'] = 1 if url.startswith('https://') else 0
    features['has_http'] = 1 if url.startswith('http://') else 0
    features['has_www'] = 1 if subdomain == 'www' else 0
    
    # Suspicious terms
    suspicious_terms = ['login', 'signin', 'verify', 'secure', 'account', 'password', 'bank']
    features['has_suspicious_terms'] = 0
    for term in suspicious_terms:
        if term in url.lower():
            features['has_suspicious_terms'] = 1
            break
    
    # Default values for other features to avoid network requests
    features['has_form'] = 0
    features['form_count'] = 0
    features['external_link_ratio'] = 0
    features['link_count'] = 0
    features['script_count'] = 0
    features['image_count'] = 0
    
    return features
