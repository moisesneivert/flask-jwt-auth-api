from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete

from app.extensions import db
from app.tokens.model import RevokedToken
from app.users.model import User
from app.utils import utc_now


def revoke_token(user: User, token_payload: dict) -> None:
    expires_at = datetime.fromtimestamp(token_payload["exp"], tz=timezone.utc)
    token = RevokedToken(
        jti=token_payload["jti"],
        token_type=token_payload["type"],
        expires_at=expires_at,
        user_id=user.id,
    )
    db.session.add(token)
    db.session.commit()


def delete_expired_revocations() -> int:
    result = db.session.execute(delete(RevokedToken).where(RevokedToken.expires_at < utc_now()))
    db.session.commit()
    return result.rowcount or 0
