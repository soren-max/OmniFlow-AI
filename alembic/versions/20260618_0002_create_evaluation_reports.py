"""create evaluation reports

Revision ID: 20260618_0002
Revises: 20260618_0001
Create Date: 2026-06-18 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0002"
down_revision: str | None = "20260618_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create rule-based evaluation report table."""
    op.create_table(
        "evaluation_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.String(length=32), nullable=False),
        sa.Column("average_score", sa.Integer(), nullable=False),
        sa.Column("platform_scores_json", sa.JSON(), nullable=False),
        sa.Column("issues_json", sa.JSON(), nullable=False),
        sa.Column("suggestions_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["project_id"], ["content_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evaluation_reports_project_id",
        "evaluation_reports",
        ["project_id"],
    )


def downgrade() -> None:
    """Drop rule-based evaluation report table."""
    op.drop_index("ix_evaluation_reports_project_id", table_name="evaluation_reports")
    op.drop_table("evaluation_reports")
