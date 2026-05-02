"""
app.py

Flask application — production-ready entry point.
Integrates Google OAuth 2.0 and serves as a thin routing layer.
All business logic is delegated to orchestrator.py.

Production: gunicorn app:app
Development: python app.py
"""
import os
import time
import logging
from collections import defaultdict
from functools import wraps

from flask import (Flask, request, jsonify, render_template,
                   session, redirect, url_for, send_from_directory)
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

import orchestrator
from services.civic_api import get_election_info
from services.india_api import get_india_election_info
from services.world_elections import get_world_election_info
from utils.response import build_response

load_dotenv()

# ─── App Setup ────────────────────────────────────────────────────────────
app = Flask(__name__)
# Fix for Google Cloud Run: Ensure url_for generates https:// URLs behind the proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-dev-secret-key")

# Let Flask handle cookies normally behind the proxy
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=86400  # 1 day
)

CORS(app)

# Production-safe logging
log_level = logging.DEBUG if os.getenv("FLASK_ENV") == "development" else logging.INFO
logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─── Rate Limiter ──────────────────────────────────────────────────────────
_request_log: dict = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 30


def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr or "unknown"
        now = time.time()
        _request_log[ip] = [t for t in _request_log[ip] if now - t < 60]
        if len(_request_log[ip]) >= MAX_REQUESTS_PER_MINUTE:
            return jsonify(build_response(
                success=False,
                error="Too many requests. Please wait a moment."
            )), 429
        _request_log[ip].append(now)
        return f(*args, **kwargs)
    return decorated


# ─── Error Handlers ───────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(_):
    return jsonify(build_response(success=False, error="Route not found.")), 404


@app.errorhandler(500)
def server_error(_):
    return jsonify(build_response(success=False, error="Internal server error.")), 500


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error("Unhandled exception: %s", type(e).__name__)
    return jsonify(build_response(success=False, error="Something went wrong. Please try again.")), 500


# ─── Favicon ──────────────────────────────────────────────────────────────
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )


# ─── Main Routes ──────────────────────────────────────────────────────────
@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", user=user)


@app.route("/timeline")
def timeline():
    country = request.args.get("country", "india").lower()
    address = request.args.get("address", "")
    state = request.args.get("state", "")

    if country == "india":
        civic_result = get_india_election_info(state or None)
        election_data = civic_result.get("data", {})
    elif country in ("uk", "australia", "canada"):
        civic_result = get_world_election_info(country)
        election_data = civic_result.get("data", {})
    else:
        country = "us"
        civic_result = get_election_info(address or None)
        election_data = civic_result.get("data", {})

    return render_template("timeline.html", election=election_data, country=country)


@app.route("/chat", methods=["POST"])
@rate_limit
def chat():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(build_response(success=False, error="Invalid JSON payload.")), 400
    result = orchestrator.process_chat(data)
    return jsonify(result)


@app.route("/eligibility", methods=["POST"])
@rate_limit
def eligibility():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(build_response(success=False, error="Invalid JSON payload.")), 400
    result = orchestrator.check_eligibility(data)
    return jsonify(result)


@app.route("/checklist", methods=["POST"])
@rate_limit
def checklist():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(build_response(success=False, error="Invalid JSON payload.")), 400
    result = orchestrator.get_checklist(data)
    return jsonify(result)


@app.route("/reminder", methods=["POST"])
@rate_limit
def reminder():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(build_response(success=False, error="Invalid JSON payload.")), 400
    election_day = data.get("election_day", "2026-11-03")
    election_name = data.get("election_name", "Election Day")
    token = session.get("access_token")
    result = orchestrator._add_calendar_reminder(election_day, election_name, token)
    return jsonify(result)


@app.route("/api/election-info", methods=["GET"])
def election_info_api():
    """JSON API for election data."""
    country = request.args.get("country", "india").lower()
    address = request.args.get("address", "")
    state = request.args.get("state", "")

    if country == "india":
        result = get_india_election_info(state or None)
    elif country in ("uk", "australia", "canada"):
        result = get_world_election_info(country)
    else:
        result = get_election_info(address or None)

    return jsonify(result)


# ─── Google OAuth 2.0 ─────────────────────────────────────────────────────
@app.route("/login")
def login():
    from google_auth_oauthlib.flow import Flow
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        return redirect(url_for("index"))

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    try:
        flow = Flow.from_client_config(
            {"web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [url_for("oauth_callback", _external=True)],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }},
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/calendar.events"
            ]
        )
        redirect_uri = url_for("oauth_callback", _external=True)
        if redirect_uri.startswith("http://") and "localhost" not in redirect_uri and "127.0.0.1" not in redirect_uri:
            redirect_uri = redirect_uri.replace("http://", "https://", 1)
            
        flow.redirect_uri = redirect_uri
        auth_url, state = flow.authorization_url(
            access_type="offline", 
            include_granted_scopes="true"
            # Removed default PKCE requirements that break stateless sessions
        )
        session["oauth_state"] = state
        # Save the code verifier if generated by OAuthlib (PKCE)
        if hasattr(flow, 'code_verifier'):
            session["code_verifier"] = flow.code_verifier
        return redirect(auth_url)
    except Exception as e:
        logger.warning("Login init failed: %s", type(e).__name__)
        return redirect(url_for("index"))


@app.route("/callback")
def oauth_callback():
    # If no code in request, just redirect home (not an error)
    if "code" not in request.args:
        return redirect(url_for("index"))

    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build as build_service

    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        return redirect(url_for("index"))

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    try:
        flow = Flow.from_client_config(
            {"web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [url_for("oauth_callback", _external=True)],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }},
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/calendar.events"
            ],
            state=session.get("oauth_state")
        )
        redirect_uri = url_for("oauth_callback", _external=True)
        if redirect_uri.startswith("http://") and "localhost" not in redirect_uri and "127.0.0.1" not in redirect_uri:
            redirect_uri = redirect_uri.replace("http://", "https://", 1)
            
        flow.redirect_uri = redirect_uri
        
        # Cloud Run proxy fix: Force request.url to https:// so oauthlib doesn't crash with redirect_uri_mismatch
        auth_response_url = request.url
        if auth_response_url.startswith("http://"):
            auth_response_url = auth_response_url.replace("http://", "https://", 1)
            
        # Restore code verifier from session if PKCE is active
        if "code_verifier" in session:
            flow.code_verifier = session["code_verifier"]

        flow.fetch_token(authorization_response=auth_response_url)
        credentials = flow.credentials
        service = build_service("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()
        session["user"] = {
            "name": user_info.get("name", "Voter"),
            "email": user_info.get("email", ""),
            "picture": user_info.get("picture", "")
        }
        # Save the access token for the Calendar API (small enough for cookie)
        session["access_token"] = credentials.token
    except Exception as e:
        logger.error("OAuth callback failed with error: %s", str(e))
        import traceback
        traceback.print_exc()
        return f"OAUTH ERROR: {str(e)} <br> Request URL: {request.url} <br> Redirect URI: {redirect_uri}", 400

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ── Production Entry ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import logging
    # Suppress werkzeug dev warning in local runs
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    is_dev = os.getenv("FLASK_DEBUG", "0") == "1"
    print(f"ElectionGuide running at http://127.0.0.1:{os.getenv('PORT', 5000)}")
    app.run(
        debug=is_dev,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        use_reloader=is_dev
    )
