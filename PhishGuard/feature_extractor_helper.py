"""
Feature extraction for URL phishing detection.
This is a backup in case the import from the original project doesn't work.
"""

import re
from urllib.parse import urlparse

import requests
import tldextract
from bs4 import BeautifulSoup


def extract_features(url):
    """Extract features from a URL for phishing detection."""
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
    
    features['domain_length'] = len(domain)
    features['has_hyphen'] = 1 if '-' in domain else 0
    features['subdomain_count'] = len(extracted.subdomain.split('.')) if extracted.subdomain else 0
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
    features['has_www'] = 1 if extracted.subdomain == 'www' else 0
    
    # Suspicious terms
    suspicious_terms = ['login', 'signin', 'verify', 'secure', 'account', 'password', 'bank']
    features['has_suspicious_terms'] = 0
    for term in suspicious_terms:
        if term in url.lower():
            features['has_suspicious_terms'] = 1
            break
    
    # Try to get website content for additional features
    try:
        response = requests.get(url, timeout=3, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Form features
        forms = soup.find_all('form')
        features['has_form'] = 1 if forms else 0
        features['form_count'] = len(forms)
        
        # Link features
        links = soup.find_all('a')
        external_links = 0
        for link in links:
            href = link.get('href', '')
            if href.startswith('http') and domain not in href:
                external_links += 1
        
        features['external_link_ratio'] = external_links / len(links) if links else 0
        features['link_count'] = len(links)
        
        # Script features
        scripts = soup.find_all('script')
        features['script_count'] = len(scripts)
        
        # Image features
        images = soup.find_all('img')
        features['image_count'] = len(images)
        
    except:
        # If we can't fetch content, use default values
        features['has_form'] = 0
        features['form_count'] = 0
        features['external_link_ratio'] = 0
        features['link_count'] = 0
        features['script_count'] = 0
        features['image_count'] = 0
    
    return features
