"""Add staff assignments, report versions and history details."""

from alembic import op
import sqlalchemy as sa

revision = "f307c91d5e24"
down_revision = "e8c42b1a7501"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "staff_contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("team", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.UniqueConstraint("full_name", "team", name="unique_staff_contact"),
        sa.CheckConstraint("length(trim(full_name)) > 0", name="staff_name_not_blank"),
    )
    with op.batch_alter_table("issues") as batch:
        batch.drop_constraint("valid_issue_status", type_="check")
        batch.create_check_constraint(
            "valid_issue_status",
            "status IN ('Reported', 'Assigned', 'In Progress', 'Resolved')",
        )
        batch.add_column(sa.Column("assigned_to_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "issue_assignee_fk", "staff_contacts", ["assigned_to_id"], ["id"]
        )
        batch.create_index("ix_issues_assigned_to_id", ["assigned_to_id"])
        batch.add_column(
            sa.Column("version", sa.Integer(), server_default="1", nullable=False)
        )
        batch.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.current_timestamp(),
                nullable=False,
            )
        )
    with op.batch_alter_table("issue_updates") as batch:
        batch.add_column(
            sa.Column("action", sa.String(30), server_default="Created", nullable=False)
        )
        batch.add_column(sa.Column("old_value", sa.String(200), nullable=True))
        batch.add_column(sa.Column("new_value", sa.String(200), nullable=True))
    op.execute(
        sa.text(
            "UPDATE issue_updates SET action = 'StatusChanged', new_value = status WHERE note <> 'Report submitted.'"
        )
    )


def downgrade():
    op.execute(
        sa.text("UPDATE issues SET status = 'Reported' WHERE status = 'Assigned'")
    )
    with op.batch_alter_table("issue_updates") as batch:
        batch.drop_column("new_value")
        batch.drop_column("old_value")
        batch.drop_column("action")
    with op.batch_alter_table("issues") as batch:
        batch.drop_constraint("valid_issue_status", type_="check")
        batch.create_check_constraint(
            "valid_issue_status", "status IN ('Reported', 'In Progress', 'Resolved')"
        )
        batch.drop_constraint("issue_assignee_fk", type_="foreignkey")
        batch.drop_index("ix_issues_assigned_to_id")
        batch.drop_column("assigned_to_id")
        batch.drop_column("version")
        batch.drop_column("updated_at")
    op.drop_table("staff_contacts")
