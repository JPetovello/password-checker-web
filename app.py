import os
import secrets
import hashlib
import math
import requests
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import zxcvbn

app = Flask(__name__)

# 1. Restrict maximum request payload size to 1 MB (prevents DoS/memory overload)
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_PAYLOAD_BYTES', 1 * 1024 * 1024))

# 2. Set up Rate Limiting (Supports Redis via env var REDIS_URL, defaults to memory)
REDIS_URL = os.environ.get("REDIS_URL", "memory://")
RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per day;50 per hour")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[RATELIMIT_DEFAULT],
    storage_uri=REDIS_URL
)

# Grab version and install source from environment variables
APP_VERSION = os.environ.get("APP_VERSION", "latest")
INSTALL_SOURCE = os.environ.get("INSTALL_SOURCE", "DockerHub / Manual")

# Load full EFF Large Wordlist into memory at app startup
EFF_WORDS = []
USING_FALLBACK_WORDLIST = False
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
    USING_FALLBACK_WORDLIST = True
    print(f"[Wordlist Warning] {WORDLIST_PATH} not found. Using expanded emergency fallback list.")
    EFF_WORDS = [
        "correct", "horse", "battery", "staple", "dragon", "subway", "security",
        "anchor", "bison", "cobalt", "canyon", "dolphin", "echo", "falcon",
        "glacier", "harbor", "island", "jungle", "kettle", "lantern", "magnet",
        "neutron", "oasis", "pinnacle", "quartz", "radar", "sierra", "timber",
        "uranium", "vortex", "walrus", "xenon", "yellow", "zephyr", "avalanche",
        "blizzard", "compass", "domino", "eclipse", "fossil", "granite", "horizon",
        "igloo", "javelin", "kingdom", "leopard", "monsoon", "nebula", "octopus",
        "pyramid", "quantum", "redwood", "saturn", "tsunami", "umbrella", "volcano",
        "whisper", "zodiac", "alpine", "beacon", "cascade", "dune", "emerald"
    ]

@app.after_request
def apply_security_headers(response):
    """Attach standard production security headers to all responses."""
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';"
    return response

def send_discord_notification():
    import datetime
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return

    FLAG_FILE = os.path.join(os.path.dirname(__file__), "data", ".installed")

    if os.path.exists(FLAG_FILE):
        print("[Discord] First-run flag found. Skipping notification.")
        return

    source_display = "Unraid CA" if INSTALL_SOURCE.lower() == "unraid_ca" else INSTALL_SOURCE
    payload = {
        "content": f"🚀 **PasswordCheckerWeb** `{APP_VERSION}` successfully installed! *(Source: **{source_display}**)*"
    }

    headers = {
        "User-Agent": "PasswordCheckerWeb/1.0 (https://github.com/hardly007/password-checker-web)"
    }

    try:
        pid = os.getpid()
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        resp = requests.post(webhook_url, json=payload, headers=headers, timeout=5)
        print(f"[{now}] [PID {pid}] First-run Discord notification sent! Status: {resp.status_code}")
        
        if resp.status_code in (200, 204):
            os.makedirs(os.path.dirname(FLAG_FILE), exist_ok=True)
            with open(FLAG_FILE, "w") as f:
                f.write("installed")
    except Exception as e:
        print(f"[Discord Webhook Error] {e}")

def check_hibp_by_prefix(prefix, suffix):
    """Check HIBP via k-Anonymity using pre-computed prefix and suffix."""
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

def check_hibp(password):
    """Check password leak count via Have I Been Pwned API using k-Anonymity."""
    sha1_password = hashlib.sha1(password.encode('utf-8'), usedforsecurity=False).hexdigest().upper()
    prefix = sha1_password[:5]
    suffix = sha1_password[5:]
    return check_hibp_by_prefix(prefix, suffix)

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
    return render_template('index.html', app_version=APP_VERSION, is_fallback=USING_FALLBACK_WORDLIST)

@app.route('/api/evaluate', methods=['POST'])
@limiter.limit("15 per minute")
def evaluate_password():
    data = request.get_json() or {}
    
    # Accept client-side hashed SHA-1 prefix/suffix OR raw password fallback
    sha1_prefix = data.get('sha1_prefix', '').strip().upper()
    sha1_suffix = data.get('sha1_suffix', '').strip().upper()
    password = data.get('password', '')

    if not password and not (sha1_prefix and sha1_suffix):
        return jsonify({'error': 'No evaluation data provided'}), 400

    if password:
        results = zxcvbn.zxcvbn(password)
        pwned_count = check_hibp(password)
        entropy_val = calculate_entropy(password)
    else:
        # Zero-knowledge mode (evaluating HIBP via client-side SHA-1 hashes)
        pwned_count = check_hibp_by_prefix(sha1_prefix, sha1_suffix)
        results = {'score': 0, 'feedback': {}, 'crack_times_display': {}}
        entropy_val = 0

    raw_crack_times = results.get('crack_times_display', {})
    capitalized_crack_times = {k: v.title() for k, v in raw_crack_times.items()}

    return jsonify({
        'score': results.get('score', 0),
        'entropy': entropy_val,
        'feedback': results.get('feedback', {}),
        'crack_times_display': capitalized_crack_times,
        'hibp': {
            'found': pwned_count > 0,
            'count': pwned_count
        }
    })

@app.route('/api/generate', methods=['GET'])
@limiter.limit("30 per minute")
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
        'words': selected_words,
        'is_fallback': USING_FALLBACK_WORDLIST
    })

if __name__ == '__main__':
    try:
        send_discord_notification()
    except Exception as e:
        print(f"Startup initialization error: {e}")

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
