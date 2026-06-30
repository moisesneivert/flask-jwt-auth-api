from __future__ import annotations

import click
from flask import Flask

from app.extensions import db
from app.users.model import User, UserRole


def register_commands(app: Flask) -> None:
    @app.cli.command("create-admin")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(name: str, email: str, password: str) -> None:
        normalized_email = email.strip().lower()
        if User.query.filter_by(email=normalized_email).first():
            raise click.ClickException("A user with this email already exists.")

        user = User(name=name.strip(), email=normalized_email, role=UserRole.ADMIN.value)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin created: {user.email}")

    @app.cli.command("cleanup-tokens")
    def cleanup_tokens() -> None:
        from app.tokens.service import delete_expired_revocations

        removed = delete_expired_revocations()
        click.echo(f"Removed {removed} expired revoked token records.")
