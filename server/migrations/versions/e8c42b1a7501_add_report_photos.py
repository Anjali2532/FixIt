"""Add report photos and submission keys."""

from alembic import op
import sqlalchemy as sa

revision = "e8c42b1a7501"
down_revision = "db260a31f793"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("issues") as batch:
        batch.add_column(sa.Column("photo_name", sa.String(36), nullable=True))
        batch.add_column(sa.Column("submission_key", sa.String(36), nullable=True))
        batch.create_unique_constraint(
            "unique_report_submission", ["user_id", "submission_key"]
        )
    issues = sa.table("issues", sa.column("category", sa.String()))
    for old, new in [("Electrical", "Lighting"), ("Cleaning", "Trash & Recycling")]:
        op.execute(issues.update().where(issues.c.category == old).values(category=new))


def downgrade():
    with op.batch_alter_table("issues") as batch:
        batch.drop_constraint("unique_report_submission", type_="unique")
        batch.drop_column("submission_key")
        batch.drop_column("photo_name")
