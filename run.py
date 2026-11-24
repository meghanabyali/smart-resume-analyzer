"""Entry point.

Development:  python run.py
Production:   gunicorn run:app
"""
import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402  (env must be loaded first)

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="127.0.0.1", port=port, debug=debug)
