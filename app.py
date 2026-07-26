import os
import hashlib
import secrets
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Load wordlist securely with path restriction
WORDLIST_PATH = os.path.join(os.path.dirname(__file__), 'wordlist.txt')

def load_wordlist():
    if not os.path.exists(WORDLIST_PATH):
        return []
    with open(WORDLIST_PATH, 'r') as f:
        return [line.strip() for line in f if line.strip()]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check-password', methods=['POST'])
def check_password():
    data = request.get_json()
    if not data or 'password' not in data:
        return jsonify({'error': 'Invalid input, password required'}), 400
        
    password = data['password']
    
    # Secure SHA-1 hashing example for local checks or k-anonymity
    sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    
    return jsonify({'status': 'checked', 'hash_prefix': sha1_hash[:5]})

@app.route('/api/generate-passphrase', methods=['POST'])
def generate_passphrase():
    data = request.get_json() or {}
    word_count = data.get('words', 4)
    
    # Input validation for word count
    try:
        word_count = int(word_count)
        if not (3 <= word_count <= 10):
            raise ValueError()
    except ValueError:
        return jsonify({'error': 'Word count must be an integer between 3 and 10'}), 400

    words = load_wordlist()
    if not words:
        return jsonify({'error': 'Wordlist unavailable'}), 500
        
    # Cryptographically secure random selection using secrets
    chosen_words = [secrets.choice(words) for _ in range(word_count)]
    passphrase = '-'.join(chosen_words)
    
    return jsonify({'passphrase': passphrase})

if __name__ == '__main__':
    # Pull debug mode safely from environment variables (default to False)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
