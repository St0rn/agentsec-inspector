"""Link evidence to audits and add scenario expected markers.

Revision ID: 0002_audit_evidence
Revises: 0001_initial
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_audit_evidence"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    scenario_columns = {item["name"] for item in inspector.get_columns("scenarios")}
    if "expected_marker" not in scenario_columns:
        with op.batch_alter_table("scenarios") as batch:
            batch.add_column(sa.Column("expected_marker", sa.String(length=200), nullable=True))
    evidence_columns = {item["name"] for item in inspector.get_columns("evidence")}
    if "audit_run_id" not in evidence_columns:
        with op.batch_alter_table("evidence") as batch:
            batch.add_column(sa.Column("audit_run_id", sa.String(length=36), nullable=True))
            batch.create_foreign_key(
                "fk_evidence_audit_run_id", "audit_runs", ["audit_run_id"], ["id"], ondelete="CASCADE"
            )
            batch.create_index("ix_evidence_audit_run_id", ["audit_run_id"])


def downgrade() -> None:
    with op.batch_alter_table("evidence") as batch:
        batch.drop_index("ix_evidence_audit_run_id")
        batch.drop_constraint("fk_evidence_audit_run_id", type_="foreignkey")
        batch.drop_column("audit_run_id")
    with op.batch_alter_table("scenarios") as batch:
        batch.drop_column("expected_marker")
