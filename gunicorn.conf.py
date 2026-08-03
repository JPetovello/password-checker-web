import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5001')}"
workers = int(os.environ.get('GUNICORN_WORKERS', 2))
threads = int(os.environ.get('GUNICORN_THREADS', 4))
worker_class = "gthread"
timeout = 30
keepalive = 2

# Disable Gunicorn 26 control server socket to prevent non-root write errors
control_socket_path = None

# Access and error logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

def on_starting(server):
    """Trigger first-run Discord notification on server start."""
    try:
        from app import send_discord_notification
        send_discord_notification()
    except Exception as e:
        print(f"[WSGI Startup Error] {e}")
