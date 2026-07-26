import os
import hashlib
import secrets
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Load wordlist securely with path restriction
WORDLIST_PATH = os.path.join(os.path.dirname(__file__), 'wordlist.txt')

def load_wordlist():
    try:
        if not os.path.exists(WORDLIST_PATH):
            return []
        with open(WORDLIST_PATH, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        app.logger.error(f"Error reading wordlist: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check-password', methods=['POST'])
def check_password():
    try:
        data = request.get_json(silent=True)
        if not data or 'password' not in data:
            return jsonify({'error': 'Invalid input, password required'}), 400
            
        password = data['password']
        if not isinstance(password, str):
            return jsonify({'error': 'Password must be a string'}), 400

        # Secure SHA-1 hashing example for local checks or k-anonymity
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        
        return jsonify({'status': 'checked', 'hash_prefix': sha1_hash[:5]}), 200
    except Exception as e:
        app.logger.error(f"Server error in check_password: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/generate-passphrase', methods=['POST'])
def generate_passphrase():
    try:
        data = request.get_json(silent=True) or {}
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
        
        return jsonify({'passphrase': passphrase}), 200
    except Exception as e:
        app.logger.error(f"Server error in generate_passphrase: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
