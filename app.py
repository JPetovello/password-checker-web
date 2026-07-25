from flask import Flask, render_template, request, jsonify
import zxcvbn
import random
import os

app = Flask(__name__)

# Load EFF large wordlist for passphrase generation
WORDLIST_PATH = os.path.join(os.path.dirname(__file__), 'eff_large_wordlist.txt')

def load_wordlist():
    words = []
    if os.path.exists(WORDLIST_PATH):
        with open(WORDLIST_PATH, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    words.append(parts[1])
    return words

EFF_WORDS = load_wordlist()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check', methods=['POST'])
def check_password():
    data = request.get_json()
    password = data.get('password', '')
    
    # Run zxcvbn evaluation
    results = zxcvbn.zxcvbn(password)
    
    # Extract crack times and ensure they are converted to strings to avoid timedelta serialization errors
    crack_times = results.get('crack_times_display', {})
    
    response_data = {
        'score': results.get('score'),
        'entropy': round(results.get('guesses_log10', 0) * 3.32, 2), # Approximate bits of entropy
        'online_attack': str(crack_times.get('online_throttling_100_per_hour', 'N/A')),
        'fast_hash': str(crack_times.get('offline_fast_hashing_1e10_per_second', 'N/A')),
        'slow_hash': str(crack_times.get('offline_slow_hashing_1e4_per_second', 'N/A'))
    }
    
    return jsonify(response_data)

@app.route('/api/generate', methods=['POST'])
def generate_passphrase():
    if not EFF_WORDS:
        passphrase = "correct horse battery staple"
    else:
        # Generate a 4-word EFF passphrase
        passphrase = " ".join(random.choices(EFF_WORDS, k=4))
    
    # Evaluate the generated passphrase using zxcvbn
    results = zxcvbn.zxcvbn(passphrase)
    crack_times = results.get('crack_times_display', {})
    
    response_data = {
        'passphrase': passphrase,
        'score': results.get('score'),
        'entropy': round(results.get('guesses_log10', 0) * 3.32, 2),
        'online_attack': str(crack_times.get('online_throttling_100_per_hour', 'N/A')),
        'fast_hash': str(crack_times.get('offline_fast_hashing_1e10_per_second', 'N/A')),
        'slow_hash': str(crack_times.get('offline_slow_hashing_1e4_per_second', 'N/A'))
    }
    
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
