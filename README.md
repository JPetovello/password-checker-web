# Password Checker Web

A lightweight, secure web application for evaluating password strength, calculating entropy, checking against known data breaches via the Have I Been Pwned API, and generating secure passphrases. Built with Flask, Python, and Tailwind CSS, featuring local k-Anonymity privacy protection.

## Features

* **Password Strength Evaluation:** Powered by zxcvbn for robust, pattern-based strength checks.
* **Breach Detection:** Checks passwords securely using the Have I Been Pwned (HIBP) API via k-Anonymity (only the first 5 characters of the SHA-1 hash are sent).
* **Entropy Calculation:** Real-time mathematical entropy calculation based on character set size and length.
* **Secure Passphrase Generator:** Generates memorable, high-entropy passphrases using the EFF Large Wordlist.
* **Privacy-First:** No passwords ever leave your instance unhashed, and telemetry can be opted out.

## Installation

### Standard Docker / Docker Desktop

Run the container using Docker CLI:

    docker run -d \
      --name password-checker-web \
      -p 5000:5000 \
      -e APP_SOURCE="docker_standalone" \
      hardly007/password-checker-web:latest

### Unraid (Community Applications)

Search for Password Checker Web in the Unraid Community Applications tab and install it directly using the official template. The deployment source will automatically register as unraid_ca.

## Environment Variables

* PORT: Port the web server listens on (default: 5000).
* APP_SOURCE: Identifies where the container was deployed (default: docker_standalone).
* DISABLE_TELEMETRY: Set to true to opt out of anonymous startup telemetry.

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the LICENSE file for details.
