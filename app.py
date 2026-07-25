import os
import random
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check', methods=['POST'])
def check_password():
    data = request.get_json() or {}
    password = data.get('password', '')
    results = zxcvbn(password)
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
