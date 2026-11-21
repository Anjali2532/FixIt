"""Use timestamp defaults supported by PostgreSQL and SQLite."""

from alembic import op
import sqlalchemy as sa

revision = "a921b5f0d618"
down_revision = "f307c91d5e24"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("users", "issues", "issue_updates"):
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                "created_at",
                existing_type=sa.DateTime(timezone=True),
                server_default=sa.func.current_timestamp(),
                existing_nullable=False,
            )


def downgrade():
    for table in ("users", "issues", "issue_updates"):
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                "created_at",
                existing_type=sa.DateTime(timezone=True),
                server_default=sa.text("(now())"),
                existing_nullable=False,
            )
