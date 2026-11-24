"""Gunicorn production settings (used by Render: `gunicorn run:app`)."""
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
# spaCy's model uses ~100 MB per worker; 2 workers fit Render's 512 MB free tier.
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = 2
timeout = 120          # first request loads the NLP model
preload_app = True     # load spaCy once, share memory between workers
accesslog = "-"
errorlog = "-"
