import os

from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///database.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-me")
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME = 30 * 24 * 60 * 60

    SESSION_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE"), default=False)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session")

    REMEMBER_COOKIE_DURATION = 30 * 24 * 60 * 60
    REMEMBER_COOKIE_SECURE = _as_bool(os.getenv("REMEMBER_COOKIE_SECURE"), default=SESSION_COOKIE_SECURE)
    REMEMBER_COOKIE_HTTPONLY = True

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    GOOGLE_DISCOVERY_URL = os.getenv(
        "GOOGLE_DISCOVERY_URL",
        "https://accounts.google.com/.well-known/openid-configuration",
    ).strip()
    GOOGLE_OAUTH_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
