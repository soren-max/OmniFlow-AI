"""create publish drafts

Revision ID: 20260623_0003
Revises: 20260618_0002
Create Date: 2026-06-23 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260623_0003"
down_revision: str | None = "20260618_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create system-internal publish draft table."""
    op.create_table(
        "publish_drafts",
        sa.Column("draft_id", sa.String(length=32), nullable=False),
        sa.Column("project_id", sa.String(length=32), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("hashtags_json", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("cta", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["project_id"], ["content_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("draft_id"),
    )
    op.create_index("ix_publish_drafts_platform", "publish_drafts", ["platform"])
    op.create_index("ix_publish_drafts_project_id", "publish_drafts", ["project_id"])


def downgrade() -> None:
    """Drop system-internal publish draft table."""
    op.drop_index("ix_publish_drafts_project_id", table_name="publish_drafts")
    op.drop_index("ix_publish_drafts_platform", table_name="publish_drafts")
    op.drop_table("publish_drafts")
