from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils import ensure_utc, utc_now


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    revoked_tokens = relationship(
        "RevokedToken", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_locked(self) -> bool:
        locked_until = ensure_utc(self.locked_until)
        return locked_until is not None and locked_until > utc_now()

    def to_dict(self, include_private: bool = False) -> dict:
        payload = {
            "id": self.public_id,
            "name": self.name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": ensure_utc(self.created_at).isoformat(),
            "updated_at": ensure_utc(self.updated_at).isoformat(),
        }
        if include_private:
            payload.update(
                {
                    "email": self.email,
                    "last_login_at": (
                        ensure_utc(self.last_login_at).isoformat() if self.last_login_at else None
                    ),
                }
            )
        return payload
