"""create core persistence tables

Revision ID: 20260618_0001
Revises:
Create Date: 2026-06-18 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create project, publish, and trace tables."""
    op.create_table(
        "content_projects",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agent_runs",
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=32), nullable=False),
        sa.Column("workflow_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("output_snapshot", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index("ix_agent_runs_project_id", "agent_runs", ["project_id"])
    op.create_table(
        "platform_contents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.String(length=32), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("platform_display_name", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("preview_json", sa.JSON(), nullable=False),
        sa.Column("validation_json", sa.JSON(), nullable=False),
        sa.Column("rendered_html", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("estimated_read_time_min", sa.Integer(), nullable=False),
        sa.Column("warnings_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["project_id"], ["content_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_platform_contents_platform", "platform_contents", ["platform"])
    op.create_index("ix_platform_contents_project_id", "platform_contents", ["project_id"])
    op.create_table(
        "publish_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.String(length=32), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["project_id"], ["content_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_publish_tasks_project_id", "publish_tasks", ["project_id"])
    op.create_table(
        "agent_steps",
        sa.Column("step_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("node_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("output_snapshot", sa.JSON(), nullable=True),
        sa.Column("tool_calls", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("step_id"),
    )
    op.create_index("ix_agent_steps_run_id", "agent_steps", ["run_id"])
    op.create_table(
        "publish_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("platform_display_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("mock_url", sa.String(length=2048), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["publish_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_publish_results_task_id", "publish_results", ["task_id"])


def downgrade() -> None:
    """Drop project, publish, and trace tables."""
    op.drop_index("ix_publish_results_task_id", table_name="publish_results")
    op.drop_table("publish_results")
    op.drop_index("ix_agent_steps_run_id", table_name="agent_steps")
    op.drop_table("agent_steps")
    op.drop_index("ix_publish_tasks_project_id", table_name="publish_tasks")
    op.drop_table("publish_tasks")
    op.drop_index("ix_platform_contents_project_id", table_name="platform_contents")
    op.drop_index("ix_platform_contents_platform", table_name="platform_contents")
    op.drop_table("platform_contents")
    op.drop_index("ix_agent_runs_project_id", table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_table("content_projects")
