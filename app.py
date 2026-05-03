"""
app.py

Flask application — production-ready entry point.
Integrates Google OAuth 2.0 and serves as a thin routing layer.
All business logic is delegated to orchestrator.py.

Production: gunicorn app:app
Development: python app.py
"""

import os
import logging
from typing import Any

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for,
    send_from_directory,
    Response,
)
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build as build_service

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import orchestrator
from config import Config
from utils.validators import sanitize_text
from services.civic_api import get_election_info
from services.india_api import get_india_election_info
from services.world_elections import get_world_election_info
from utils.response import build_response
from flask_limiter.errors import RateLimitExceeded

# ─── App Setup ────────────────────────────────────────────────────────────
app = Flask(__name__)
# Fix for Google Cloud Run: Ensure url_for generates https:// URLs behind the proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = Config.FLASK_SECRET_KEY

# Let Flask handle cookies normally behind the proxy
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    PERMANENT_SESSION_LIFETIME=86400,  # 1 day
)

CORS(app)

# Production-safe logging
log_level = logging.DEBUG if Config.is_development() else logging.INFO
logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─── Rate Limiter ──────────────────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "30 per minute"],
    storage_uri="memory://",
)


@app.after_request
def security_headers(response: Response) -> Response:
    """Add secure HTTP response headers."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    # No-cache to force browser to see current version during testing
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' http: https: 'unsafe-inline' 'unsafe-eval' data: blob: *.google.com *.googleapis.com *.gstatic.com;"
    )
    return response


# ─── Error Handlers ───────────────────────────────────────────────────────
@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(e: RateLimitExceeded) -> tuple[Response, int]:
    """Handle rate limit exceeded errors."""
    return (
        jsonify(
            build_response(
                success=False, error="Too many requests. Please wait a moment."
            )
        ),
        429,
    )


@app.errorhandler(404)
def not_found(_: Any) -> tuple[Response, int]:
    """Handle 404 Not Found errors."""
    return jsonify(build_response(success=False, error="Route not found.")), 404


@app.errorhandler(500)
def server_error(_: Any) -> tuple[Response, int]:
    """Handle 500 Internal Server errors."""
    return jsonify(build_response(success=False, error="Internal server error.")), 500


@app.errorhandler(Exception)
def handle_exception(e: Exception) -> tuple[Response, int]:
    """Handle unhandled exceptions globally."""
    logger.error("Unhandled exception: %s", type(e).__name__)
    return (
        jsonify(
            build_response(
                success=False, error="Something went wrong. Please try again."
            )
        ),
        500,
    )


# ─── Favicon ──────────────────────────────────────────────────────────────
@app.route("/favicon.ico")
def favicon() -> Response:
    """Serve the application favicon."""
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# ─── Main Routes ──────────────────────────────────────────────────────────
@app.route("/")
def index() -> str:
    """Render the main landing page."""
    user = session.get("user")
    return render_template("index.html", user=user)


@app.route("/timeline")
def timeline() -> str:
    """Render the localized election timeline page."""
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
@limiter.limit("10 per minute")
def chat() -> Response:
    """Handle chat interactions with the Gemini logic engine."""
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify(build_response(success=False, error="Invalid JSON payload.")),
            400,
        )
    message = sanitize_text(data.get("message", ""))
    if not message or len(message) > 500:
        return jsonify(build_response(success=False, error="Invalid message")), 400
    data["message"] = message
    result = orchestrator.process_chat(data)
    return jsonify(result)


@app.route("/eligibility", methods=["POST"])
@limiter.limit("10 per minute")
def eligibility() -> Response:
    """Handle deterministic eligibility checks."""
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify(build_response(success=False, error="Invalid JSON payload.")),
            400,
        )
    if not data.get("age"):
        return jsonify(build_response(success=False, error="Invalid input")), 400
    result = orchestrator.check_eligibility(data)
    return jsonify(result)


@app.route("/checklist", methods=["POST"])
@limiter.limit("10 per minute")
def checklist() -> Response:
    """Handle deterministic voter checklist generation."""
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify(build_response(success=False, error="Invalid JSON payload.")),
            400,
        )
    status = sanitize_text(data.get("status", ""))
    if status and len(status) > 50:
        return jsonify(build_response(success=False, error="Invalid status")), 400
    result = orchestrator.get_checklist(data)
    return jsonify(result)


@app.route("/reminder", methods=["POST"])
@limiter.limit("10 per minute")
def reminder() -> Response:
    """Add a calendar reminder via OAuth."""
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify(build_response(success=False, error="Invalid JSON payload.")),
            400,
        )
    election_day = sanitize_text(data.get("election_day", "2026-11-03"))
    election_name = sanitize_text(data.get("election_name", "Election Day"))
    if not election_day or len(election_day) > 20:
        return (
            jsonify(build_response(success=False, error="Invalid election date")),
            400,
        )
    token = session.get("access_token")
    result = orchestrator._add_calendar_reminder(election_day, election_name, token)
    return jsonify(result)


@app.route("/api/election-info", methods=["GET"])
def election_info_api() -> Response:
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
def login() -> Response:
    """Initiate Google OAuth 2.0 login flow."""
    client_id = Config.GOOGLE_OAUTH_CLIENT_ID
    client_secret = Config.GOOGLE_OAUTH_CLIENT_SECRET
    if not client_id or not client_secret:
        return redirect(url_for("index"))

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": [url_for("oauth_callback", _external=True)],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/calendar.events",
            ],
        )
        redirect_uri = url_for("oauth_callback", _external=True)
        if (
            redirect_uri.startswith("http://")
            and "localhost" not in redirect_uri
            and "127.0.0.1" not in redirect_uri
        ):
            redirect_uri = redirect_uri.replace("http://", "https://", 1)

        flow.redirect_uri = redirect_uri
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            # Removed default PKCE requirements that break stateless sessions
        )
        session["oauth_state"] = state
        # Save the code verifier if generated by OAuthlib (PKCE)
        if hasattr(flow, "code_verifier"):
            session["code_verifier"] = flow.code_verifier
        return redirect(auth_url)
    except Exception as e:
        logger.warning("Login init failed: %s", type(e).__name__)
        return redirect(url_for("index"))


@app.route("/callback")
def oauth_callback() -> Response:
    """Handle OAuth 2.0 callback and fetch tokens."""
    # If no code in request, just redirect home (not an error)
    if "code" not in request.args:
        return redirect(url_for("index"))

    client_id = Config.GOOGLE_OAUTH_CLIENT_ID
    client_secret = Config.GOOGLE_OAUTH_CLIENT_SECRET
    if not client_id or not client_secret:
        return redirect(url_for("index"))

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": [url_for("oauth_callback", _external=True)],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/calendar.events",
            ],
            state=session.get("oauth_state"),
        )
        redirect_uri = url_for("oauth_callback", _external=True)
        if (
            redirect_uri.startswith("http://")
            and "localhost" not in redirect_uri
            and "127.0.0.1" not in redirect_uri
        ):
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
            "picture": user_info.get("picture", ""),
        }
        # Save the access token for the Calendar API (small enough for cookie)
        session["access_token"] = credentials.token
    except Exception as e:
        logger.error("OAuth callback failed with error: %s", str(e))
        import traceback

        traceback.print_exc()

    return redirect(url_for("index"))


@app.route("/logout")
def logout() -> Response:
    """Clear session data."""
    session.clear()
    return redirect(url_for("index"))


# ── Production Entry ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import logging

    # Suppress werkzeug dev warning in local runs
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    logger.info("ElectionGuide running at http://127.0.0.1:%s", Config.PORT)
    app.run(
        debug=Config.FLASK_DEBUG,
        host="0.0.0.0",
        port=Config.PORT,
        use_reloader=Config.FLASK_DEBUG,
    )
