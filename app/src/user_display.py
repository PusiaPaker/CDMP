from app.core import db
from app.tables import GoogleAuthIdentity, User


def get_user_display_name(user: User | None, *, default: str = "User") -> str:
    if user is None:
        return default

    full_name = (user.full_name or "").strip()
    if full_name:
        return full_name

    google_full_name = (
        db.session.query(GoogleAuthIdentity.full_name)
        .filter_by(user_id=user.id)
        .scalar()
    )
    google_full_name = (google_full_name or "").strip()
    if google_full_name:
        return google_full_name

    username = (user.username or "").strip()
    return username or default
