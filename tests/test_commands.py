from app.extensions import db
from app.tokens.model import RevokedToken
from app.users.model import User
from app.utils import utc_now


def test_create_admin_command(app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "create-admin",
            "--name",
            "CLI Admin",
            "--email",
            "cli@example.com",
            "--password",
            "CliAdminPass1!",
        ]
    )
    assert result.exit_code == 0
    assert "Admin created" in result.output
    with app.app_context():
        assert User.query.filter_by(email="cli@example.com", role="admin").first() is not None

    duplicate = runner.invoke(
        args=[
            "create-admin",
            "--name",
            "CLI Admin",
            "--email",
            "cli@example.com",
            "--password",
            "CliAdminPass1!",
        ]
    )
    assert duplicate.exit_code != 0
    assert "already exists" in duplicate.output


def test_cleanup_tokens_command(app, user):
    with app.app_context():
        db.session.add(
            RevokedToken(
                jti="expired-jti",
                token_type="access",
                expires_at=utc_now().replace(year=2020),
                user_id=User.query.filter_by(public_id=user).first().id,
            )
        )
        db.session.commit()

    result = app.test_cli_runner().invoke(args=["cleanup-tokens"])
    assert result.exit_code == 0
    assert "Removed 1" in result.output
