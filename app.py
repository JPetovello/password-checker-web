import hashlib
import os
import random
import requests
from flask import Flask, render_template, request, jsonify
from zxcvbn import zxcvbn

app = Flask(__name__)

# Path to the EFF Large Wordlist
WORDLIST_PATH = os.path.join(os.path.dirname(__file__), 'eff_large_wordlist.txt')

def load_wordlist():
    words = []
    if os.path.exists(WORDLIST_PATH):
        with open(WORDLIST_PATH, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    words.append(parts[1])
    else:
        # Fallback list if the EFF file isn't downloaded yet
        words = ["apple", "banana", "cherry", "delta", "eagle", "forest", "galaxy", "harbor", "igloo", "jungle"]
    return words

WORD_LIST = load_wordlist()

def check_password_leak(password: str) -> int:
    """
    Checks the HIBP k-Anonymity API for password leaks.
    Sends only the first 5 characters of the SHA-1 hash (privacy-safe).
    Returns breach count, 0 if safe, or -1 on network error.
    """
    if not password:
        return 0
        
    sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix = sha1_hash[:5]
    suffix = sha1_hash[5:]
    
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    headers = {"User-Agent": "PasswordCheckerWeb-SelfHosted"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return -1  # Network/timeout safeguard
        
    for line in response.text.splitlines():
        if not line:
            continue
        parts = line.split(":")
        if len(parts) == 2:
            hash_suffix, count = parts
            if hash_suffix == suffix:
                return int(count)
                
    return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check', methods=['POST'])
def check_password():
    data = request.get_json() or {}
    password = data.get('password', '')
    
    # Get original zxcvbn analysis dictionary
    results = zxcvbn(password)
    
    # Run Have I Been Pwned check
    breach_count = check_password_leak(password)
    if breach_count == -1:
        breach_count = 0  # Fallback gracefully if connection drops
        
    # Inject HIBP data into the returned dictionary so your frontend can use it
    results['breach_count'] = breach_count
    results['is_breached'] = breach_count > 0
    
    return jsonify(results)

@app.route('/api/generate', methods=['GET'])
def generate_passphrase():
    try:
        word_count = int(request.args.get('words', 4))
    except ValueError:
        word_count = 4
    
    separator = request.args.get('separator', '-')
    
    # Constrain word count safely between 3 and 8
    word_count = max(3, min(8, word_count))
    
    selected_words = [random.choice(WORD_LIST) for _ in range(word_count)]
    passphrase = separator.join(selected_words)
    
    return jsonify({'passphrase': passphrase})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
