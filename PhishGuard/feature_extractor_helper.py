"""
Feature extraction for URL phishing detection.
This is a backup in case the import from the original project doesn't work.
"""

import re
from urllib.parse import urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available, some features will be limited")

try:
    import tldextract
    TLDEXTRACT_AVAILABLE = True
except ImportError:
    TLDEXTRACT_AVAILABLE = False
    print("Warning: tldextract not available, using basic domain parsing")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("Warning: BeautifulSoup not available, HTML parsing disabled")


def extract_features(url):
    """Extract features from a URL for phishing detection."""
    features = {}
    
    # Basic URL features
    features['url_length'] = len(url)
    features['has_ip'] = 1 if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url) else 0
    features['has_at_symbol'] = 1 if '@' in url else 0
    features['has_double_slash'] = 1 if '//' in url[8:] else 0
    
    # Domain features
    if TLDEXTRACT_AVAILABLE:
        extracted = tldextract.extract(url)
        domain = extracted.domain
        suffix = extracted.suffix
        subdomain = extracted.subdomain
    else:
        # Fallback domain parsing
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        parts = hostname.split('.')
        domain = parts[-2] if len(parts) >= 2 else hostname
        suffix = parts[-1] if len(parts) >= 1 else ''
        subdomain = '.'.join(parts[:-2]) if len(parts) > 2 else ''
    
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
    features['has_www'] = 1 if extracted.subdomain == 'www' else 0
    
    # Suspicious terms
    suspicious_terms = ['login', 'signin', 'verify', 'secure', 'account', 'password', 'bank']
    features['has_suspicious_terms'] = 0
    for term in suspicious_terms:
        if term in url.lower():
            features['has_suspicious_terms'] = 1
            break
    
    # Try to get website content for additional features
    if REQUESTS_AVAILABLE and BS4_AVAILABLE:
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
            
        except Exception as e:
            print(f"Error fetching content for {url}: {e}")
            # Set default values
            features['has_form'] = 0
            features['form_count'] = 0
            features['external_link_ratio'] = 0
            features['link_count'] = 0
            features['script_count'] = 0
            features['image_count'] = 0
    else:
        # If we can't fetch content, use default values
        features['has_form'] = 0
        features['form_count'] = 0
        features['external_link_ratio'] = 0
        features['link_count'] = 0
        features['script_count'] = 0
        features['image_count'] = 0
    
    return features
