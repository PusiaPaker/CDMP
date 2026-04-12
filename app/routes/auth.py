import re
import secrets

from flask import Blueprint, current_app, render_template, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from app.core import db, oauth
from app.src.google_calendar import encrypt_google_refresh_token
from app.tables import GoogleAuthIdentity, GoogleCalendarToken, User

AuthBP = Blueprint('authentication', __name__)


def _google_enabled() -> bool:
    return current_app.config.get("GOOGLE_OAUTH_ENABLED", False) and hasattr(oauth, "google")


def _safe_next_url(candidate: str | None) -> str:
    if candidate and candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return url_for("dashboard.main")


def _build_unique_username(email: str) -> str:
    base = email.split("@", 1)[0].strip().lower()
    base = re.sub(r"[^a-z0-9._-]+", "-", base).strip(".-_") or "user"
    candidate = base[:40]
    suffix = 1

    while db.session.query(User).filter_by(username=candidate).first():
        suffix += 1
        candidate = f"{base[:32]}-{suffix}"

    return candidate


def _is_strong_password(password: str) -> bool:
    return (
        len(password) >= 10
        and any(character.isdigit() for character in password)
        and any(character.islower() for character in password)
        and any(character.isupper() for character in password)
        and any(not character.isalnum() for character in password)
    )

@AuthBP.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("authentication.login"))

@AuthBP.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db.session.query(User).filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return render_template("auth/login.html", error="Bad username or password", google_sign_in_enabled=_google_enabled()), 401

        remember = request.form.get("remember_me") == "true"
        next_url = _safe_next_url(request.args.get("next"))

        session.clear()
        session.permanent = remember
        session["user_id"] = user.id

        return redirect(next_url)

    return render_template("auth/login.html", google_sign_in_enabled=_google_enabled())


@AuthBP.route("/login/google")
def login_google():
    if not _google_enabled():
        return redirect(url_for("authentication.login"))

    session.clear()
    session["auth_next"] = _safe_next_url(request.args.get("next"))
    session["google_oidc_nonce"] = secrets.token_urlsafe(24)

    return oauth.google.authorize_redirect(
        url_for("authentication.google_callback", _external=True),
        nonce=session["google_oidc_nonce"],
        prompt="consent select_account",
        access_type="offline",
        include_granted_scopes="true",
    )


@AuthBP.route("/login/google/callback")
def google_callback():
    if not _google_enabled():
        return redirect(url_for("authentication.login"))

    next_url = _safe_next_url(session.pop("auth_next", None))

    try:
        token = oauth.google.authorize_access_token()
        userinfo = oauth.google.parse_id_token(
            token,
            nonce=session.pop("google_oidc_nonce", None),
        )
    except Exception:
        session.pop("google_oidc_nonce", None)
        return render_template(
            "auth/login.html",
            error="Google sign-in could not be completed. Please try again.",
            google_sign_in_enabled=_google_enabled(),
        ), 401

    if not userinfo:
        return render_template(
            "auth/login.html",
            error="Google sign-in returned incomplete identity data.",
            google_sign_in_enabled=_google_enabled(),
        ), 401

    google_sub = (userinfo.get("sub") or "").strip()
    email = (userinfo.get("email") or "").strip().lower()
    email_verified = bool(userinfo.get("email_verified"))
    full_name = (userinfo.get("name") or "").strip() or None
    picture_url = (userinfo.get("picture") or "").strip() or None
    refresh_token = (token.get("refresh_token") or "").strip() or None
    granted_scope = (token.get("scope") or "").strip() or None

    if not google_sub or not email or not email_verified:
        return render_template(
            "auth/login.html",
            error="Google sign-in requires a verified Google email address.",
            google_sign_in_enabled=_google_enabled(),
        ), 401

    identity = db.session.query(GoogleAuthIdentity).filter_by(google_sub=google_sub).first()
    if identity:
        user = db.session.get(User, identity.user_id)
        if not user:
            return render_template(
                "auth/login.html",
                error="Your Google sign-in is linked to an invalid local account.",
                google_sign_in_enabled=_google_enabled(),
            ), 401

        identity.email = email
        identity.email_verified = email_verified
        identity.full_name = full_name
        identity.picture_url = picture_url
    else:
        existing_user = db.session.query(User).filter_by(email=email).first()
        if existing_user:
            return render_template(
                "auth/login.html",
                error="That email is already tied to an existing local account. Sign in with your password for now.",
                google_sign_in_enabled=_google_enabled(),
            ), 401

        user = User(
            username=_build_unique_username(email),
            password=generate_password_hash(secrets.token_urlsafe(48)),
            email=email,
        )
        db.session.add(user)
        db.session.flush()

        db.session.add(
            GoogleAuthIdentity(
                user_id=user.id,
                google_sub=google_sub,
                email=email,
                email_verified=email_verified,
                full_name=full_name,
                picture_url=picture_url,
            )
        )

    existing_calendar_token = db.session.query(GoogleCalendarToken).filter_by(user_id=user.id).first()
    if refresh_token:
        if existing_calendar_token:
            existing_calendar_token.refresh_token_encrypted = encrypt_google_refresh_token(refresh_token)
            existing_calendar_token.scopes = granted_scope
        else:
            db.session.add(
                GoogleCalendarToken(
                    user_id=user.id,
                    refresh_token_encrypted=encrypt_google_refresh_token(refresh_token),
                    scopes=granted_scope,
                )
            )
    elif existing_calendar_token and granted_scope:
        existing_calendar_token.scopes = granted_scope

    db.session.commit()

    session.clear()
    session["user_id"] = user.id
    return redirect(next_url)

@AuthBP.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip().lower()

        if not full_name:
            return render_template(
                "auth/register.html",
                error="Full name is required.",
                google_sign_in_enabled=_google_enabled(),
            ), 400
        if not _is_strong_password(password):
            return render_template(
                "auth/register.html",
                error="Password must be 10+ characters and include uppercase, lowercase, number, and special character.",
                google_sign_in_enabled=_google_enabled(),
            ), 400

        user = db.session.query(User).filter_by(username=username).first()
        if user:
            return render_template("auth/register.html", error="Username is taken.", google_sign_in_enabled=_google_enabled()), 401
        
        email_in_use = db.session.query(User).filter_by(email=email).first()
        if email_in_use:
            return render_template("auth/register.html", error="Email is already in use.", google_sign_in_enabled=_google_enabled()), 401
        

        new_user = User(
            username=username,
            full_name=full_name,
            password=generate_password_hash(password),
            email=email,
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("authentication.login"))

    return render_template("auth/register.html", google_sign_in_enabled=_google_enabled())
