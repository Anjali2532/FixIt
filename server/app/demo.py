"""Optional sample records for local development and demonstrations."""

from datetime import timedelta

import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from .auth import signup_errors
from .extensions import db
from .issues import CATEGORIES, STATUSES
from .models import Issue, IssueUpdate, StaffContact, User
from .security.access import utc_now
from .security.password import hash_password


@click.command("seed-demo")
@click.option("--reports", default=100, type=click.IntRange(1, 200), show_default=True)
@click.password_option()
@with_appcontext
def seed_demo(reports, password):
    """Add labeled sample data once, without replacing existing records."""
    if current_app.config["PRODUCTION"] or not current_app.config["ALLOW_DEMO_DATA"]:
        raise click.ClickException(
            "Demo data is disabled. Enable it only for local development."
        )
    url = make_url(current_app.config["SQLALCHEMY_DATABASE_URI"])
    if url.get_backend_name() != "sqlite" and url.host not in {
        "localhost",
        "127.0.0.1",
    }:
        raise click.ClickException("Demo data may only be added to a local database.")
    errors = signup_errors(
        dict(
            name="Demo",
            email="demo@example.test",
            password=password,
            confirm_password=password,
        )
    )
    if errors:
        raise click.ClickException(" ".join(errors.values()))
    emails = [f"demo.resident{i}@example.test" for i in range(1, 4)] + [
        f"demo.admin{i}@example.test" for i in range(1, 3)
    ]
    names = [f"Demo Technician {i}" for i in range(1, 6)]
    if db.session.scalar(
        db.select(User.id).where(User.email.in_(emails)).limit(1)
    ) or db.session.scalar(
        db.select(StaffContact.id).where(StaffContact.full_name.in_(names)).limit(1)
    ):
        raise click.ClickException(
            "Demo accounts or contacts already exist. No records were added."
        )

    now = utc_now()
    users = []
    try:
        for index, email in enumerate(emails):
            resident = index < 3
            user = User(
                full_name=f"Demo {'Resident' if resident else 'Administrator'} {index + 1 if resident else index - 2}",
                email=email,
                role="Resident" if resident else "Administrator",
                password_hash=hash_password(password),
            )
            db.session.add(user)
            users.append(user)
        contacts = [StaffContact(full_name=name, team="Maintenance") for name in names]
        db.session.add_all(contacts)
        db.session.flush()
        for index in range(reports):
            created = now - timedelta(days=1 + index % 14, minutes=index)
            status = STATUSES[index % len(STATUSES)]
            contact = contacts[index % len(contacts)] if status != "Reported" else None
            issue = Issue(
                user_id=users[index % 3].id,
                title=f"Demo: {CATEGORIES[index % len(CATEGORIES)]} issue {index + 1}",
                description="Sample report for checking dashboard filters, sorting and pagination.",
                location=f"Demo Building {chr(65 + index % 3)}, hallway",
                category=CATEGORIES[index % len(CATEGORIES)],
                priority=("Low", "Normal", "High")[index % 3],
                status=status,
                created_at=created,
                updated_at=created,
                assigned_to=contact,
            )
            db.session.add(issue)
            db.session.flush()
            db.session.add(
                IssueUpdate(
                    issue_id=issue.id,
                    actor_id=issue.user_id,
                    action="Created",
                    status="Reported",
                    new_value="Reported",
                    note="Demonstration report submitted.",
                    created_at=created,
                )
            )
            issue.version = 1
            if contact:
                assigned_at = created + timedelta(minutes=15)
                db.session.add_all(
                    [
                        IssueUpdate(
                            issue_id=issue.id,
                            actor_id=users[3].id,
                            action="Assigned",
                            status="Assigned",
                            new_value=contact.full_name,
                            note="Assigned for a demonstration.",
                            created_at=assigned_at,
                        ),
                        IssueUpdate(
                            issue_id=issue.id,
                            actor_id=users[3].id,
                            action="StatusChanged",
                            status="Assigned",
                            old_value="Reported",
                            new_value="Assigned",
                            note="Assignment accepted.",
                            created_at=assigned_at,
                        ),
                    ]
                )
                issue.version = 2
                issue.updated_at = assigned_at
            if status in {"In Progress", "Resolved"}:
                issue.updated_at = created + timedelta(minutes=30)
                issue.version = 3
                db.session.add(
                    IssueUpdate(
                        issue_id=issue.id,
                        actor_id=users[4].id,
                        action="StatusChanged",
                        status="In Progress",
                        old_value="Assigned",
                        new_value="In Progress",
                        note="Demonstration inspection started.",
                        created_at=issue.updated_at,
                    )
                )
            if status == "Resolved":
                issue.updated_at = created + timedelta(minutes=45)
                issue.version = 4
                db.session.add(
                    IssueUpdate(
                        issue_id=issue.id,
                        actor_id=users[4].id,
                        action="StatusChanged",
                        status="Resolved",
                        old_value="In Progress",
                        new_value="Resolved",
                        note="Demonstration repair completed.",
                        created_at=issue.updated_at,
                    )
                )
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise click.ClickException(
            "Could not save the sample data. The changes were rolled back."
        ) from error
    click.echo(
        f"Added {reports} labeled demo reports, 3 residents, 2 administrators and 5 contacts."
    )
    click.echo("Resident login: demo.resident1@example.test")
    click.echo("Administrator login: demo.admin1@example.test")
    click.echo("Use the password you entered. Existing records were retained.")
