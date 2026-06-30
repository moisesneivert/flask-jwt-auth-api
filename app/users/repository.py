from __future__ import annotations

from sqlalchemy import func, select

from app.extensions import db
from app.users.model import User


class UserRepository:
    @staticmethod
    def get_by_email(email: str) -> User | None:
        return db.session.scalar(select(User).where(User.email == email))

    @staticmethod
    def get_by_public_id(public_id: str) -> User | None:
        return db.session.scalar(select(User).where(User.public_id == public_id))

    @staticmethod
    def add(user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def save() -> None:
        db.session.commit()

    @staticmethod
    def list_paginated(page: int, per_page: int, search: str | None = None):
        statement = select(User)
        count_statement = select(func.count()).select_from(User)

        if search:
            pattern = f"%{search.lower()}%"
            condition = func.lower(User.name).like(pattern) | func.lower(User.email).like(pattern)
            statement = statement.where(condition)
            count_statement = count_statement.where(condition)

        total = db.session.scalar(count_statement) or 0
        items = db.session.scalars(
            statement.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        ).all()
        return items, total
