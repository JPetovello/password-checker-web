import os
import math
import hashlib
import requests
import secrets
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

WORDLIST_PATH = os.path.join(os.path.dirname(__file__), 'eff_large_wordlist.txt')

def load_wordlist():
    try:
        if not os.path.exists(WORDLIST_PATH):
            return []
        with open(WORDLIST_PATH, 'r') as f:
            words = []
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    words.append(parts[1])
                elif parts:
                    words.append(parts[0])
            return words
    except Exception as e:
        app.logger.error(f"Error reading wordlist: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/evaluate', methods=['POST'])
def evaluate_password():
    try:
        data = request.get_json(silent=True)
        if not data or 'password' not in data:
            return jsonify({'error': 'Password required'}), 400
            
        password = data['password']
        if not isinstance(password, str):
            return jsonify({'error': 'Password must be a string'}), 400

        length = len(password)
        
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)
        
        pool_size = 0
        if has_lower: pool_size += 26
        if has_upper: pool_size += 26
        if has_digit: pool_size += 10
        if has_symbol: pool_size += 32
        
        pool_size = max(pool_size, 1)
        entropy = length * math.log2(pool_size) if length > 0 else 0
        
        score = 0
        if length >= 8: score += 1
        if length >= 12: score += 1
        if (has_lower and has_upper) or (has_digit and has_symbol): score += 1
        if entropy > 60: score += 1
        score = min(score, 4)

        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1_hash[:5], sha1_hash[5:]
        
        hibp_found = False
        hibp_count = 0
        try:
            resp = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=3)
            if resp.status_code == 200:
                hashes = (line.split(':') for line in resp.text.splitlines())
                for h, count in hashes:
                    if h == suffix:
                        hibp_found = True
                        hibp_count = int(count)
                        break
        except Exception:
            pass

        response_data = {
            'score': score,
            'entropy': entropy,
            'crack_times_display': {
                'online_throttling_100_per_hour': 'Instant' if entropy < 20 else 'Several hours',
                'offline_fast_hashing_1e10_per_second': 'Instant' if entropy < 30 else 'Centuries',
                'offline_slow_hashing_1e4_per_second': 'Instant' if entropy < 40 else 'Millennia'
            },
            'hibp': {
                'prefix': prefix,
                'found': hibp_found,
                'count': hibp_count
            }
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        app.logger.error(f"Server error in evaluate_password: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/generate', methods=['GET'])
def generate_passphrase():
    try:
        word_count = request.args.get('words', 4)
        try:
            word_count = int(word_count)
            if not (3 <= word_count <= 10):
                raise ValueError()
        except ValueError:
            word_count = 4

        words = load_wordlist()
        if not words:
            return jsonify({'error': 'Wordlist unavailable'}), 500
            
        chosen_words = [secrets.choice(words) for _ in range(word_count)]
        passphrase = '-'.join(chosen_words)
        
        return jsonify({'passphrase': passphrase}), 200
    except Exception as e:
        app.logger.error(f"Server error in generate_passphrase: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
