import os
import uuid
import secrets
import hashlib
import math
import requests
from flask import Flask, render_template, request, jsonify
import zxcvbn

app = Flask(__name__)

# Grab version from environment variable set by Docker build args, default to v1.1.8
APP_VERSION = os.environ.get("APP_VERSION", "v1.1.8")

# Load full EFF Large Wordlist, preserving original casing
EFF_WORDS = []
WORDLIST_PATH = os.path.join(os.path.dirname(__file__), 'eff_large_wordlist.txt')

if os.path.exists(WORDLIST_PATH):
    with open(WORDLIST_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) >= 2:
                EFF_WORDS.append(parts[1])
            elif parts:
                EFF_WORDS.append(parts[0])
    print(f"[Wordlist] Loaded {len(EFF_WORDS)} words from {WORDLIST_PATH}")
else:
    print(f"[Wordlist Warning] {WORDLIST_PATH} not found. Using fallback list.")
    EFF_WORDS = ["correct", "horse", "battery", "staple", "dragon", "subway", "security"]

def send_telemetry():
    if os.getenv("DISABLE_TELEMETRY", "false").lower() == "true":
        print("[Telemetry] Opt-out enabled. Skipping ping.")
        return

    project_token = "phc_oVCjbdLFur2Qq8cvj8jsJeeLGxVPCTTLxePGfMpQH4Vm"
    instance_id = str(uuid.uuid4())

    payload = {
        "api_key": project_token,
        "event": "container_started",
        "distinct_id": instance_id,
        "properties": {
            "app_version": APP_VERSION,
            "$process_person_profile": False
        }
    }

    try:
        response = requests.post(
            "https://eu.i.posthog.com/i/v0/e/", 
            json=payload, 
            timeout=5
        )
        if response.status_code == 200:
            print("[Telemetry] Anonymous startup event logged to EU servers.")
    except Exception as e:
        print(f"[Telemetry] Ping skipped: {e}")

send_telemetry()

def check_hibp(password):
    """Check password leak count via Have I Been Pwned API using k-Anonymity with required User-Agent."""
    sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1_password[:5]
    suffix = sha1_password[5:]

    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    headers = {'User-Agent': 'PasswordCheckerWeb-Homelab-App'}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            return 0

        for line in res.text.splitlines():
            if ':' in line:
                h, count = line.split(':', 1)
                if h.strip() == suffix:
                    return int(count)
    except Exception as e:
        print(f"[HIBP Error] {e}")
        return 0

    return 0

def calculate_entropy(password):
    charset_size = 0
    if any(c.islower() for c in password): charset_size += 26
    if any(c.isupper() for c in password): charset_size += 26
    if any(c.isdigit() for c in password): charset_size += 10
    if any(not c.isalnum() for c in password): charset_size += 32
    
    if charset_size == 0 or len(password) == 0:
        return 0
    
    return round(len(password) * math.log2(charset_size))

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', app_version=APP_VERSION)

@app.route('/api/evaluate', methods=['POST'])
def evaluate_password():
    data = request.get_json() or {}
    password = data.get('password', '')

    if not password:
        return jsonify({'error': 'No password provided'}), 400

    results = zxcvbn.zxcvbn(password)
    pwned_count = check_hibp(password)
    entropy_val = calculate_entropy(password)

    # Capitalize the crack times display strings (e.g., "centuries" -> "Centuries", "4 years" -> "4 Years")
    raw_crack_times = results.get('crack_times_display', {})
    capitalized_crack_times = {k: v.title() for k, v in raw_crack_times.items()}

    return jsonify({
        'score': results['score'],
        'entropy': entropy_val,
        'feedback': results['feedback'],
        'crack_times_display': capitalized_crack_times,
        'hibp': {
            'found': pwned_count > 0,
            'count': pwned_count
        }
    })

@app.route('/api/generate', methods=['GET'])
def generate_passphrase():
    try:
        num_words = int(request.args.get('words', 4))
    except (ValueError, TypeError):
        num_words = 4

    num_words = max(3, min(num_words, 10))

    if not EFF_WORDS:
        return jsonify({'error': 'Wordlist empty'}), 500

    selected_words = [secrets.choice(EFF_WORDS) for _ in range(num_words)]
    passphrase = "-".join(selected_words)

    return jsonify({
        'passphrase': passphrase,
        'words': selected_words
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
