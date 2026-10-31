"""Track distinct recurring security findings without losing their audit evidence.

Revision ID: 0003_finding_dedup
Revises: 0002_audit_evidence
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_finding_dedup"
down_revision: str | None = "0002_audit_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("findings") as batch:
        batch.add_column(sa.Column("target_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("fingerprint", sa.String(64), nullable=True))
        batch.add_column(sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("occurrence_count", sa.Integer(), nullable=True))
        batch.create_index("ix_findings_target_id", ["target_id"])
        batch.create_unique_constraint("uq_findings_project_fingerprint", ["project_id", "fingerprint"])
    op.execute(
        "UPDATE findings SET first_seen = created_at, last_seen = updated_at, "
        "occurrence_count = 1 WHERE occurrence_count IS NULL"
    )
    with op.batch_alter_table("findings") as batch:
        batch.alter_column("first_seen", nullable=False)
        batch.alter_column("last_seen", nullable=False)
        batch.alter_column("occurrence_count", nullable=False)
    op.create_table(
        "finding_occurrences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("finding_id", sa.String(36), sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("audit_run_id", sa.String(36), sa.ForeignKey("audit_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_sha256", sa.String(64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("finding_id", "audit_run_id", name="uq_finding_occurrence_audit"),
    )
    op.create_index("ix_finding_occurrences_finding_id", "finding_occurrences", ["finding_id"])
    op.create_index("ix_finding_occurrences_audit_run_id", "finding_occurrences", ["audit_run_id"])


def downgrade() -> None:
    op.drop_index("ix_finding_occurrences_audit_run_id", "finding_occurrences")
    op.drop_index("ix_finding_occurrences_finding_id", "finding_occurrences")
    op.drop_table("finding_occurrences")
    with op.batch_alter_table("findings") as batch:
        batch.drop_constraint("uq_findings_project_fingerprint", type_="unique")
        batch.drop_index("ix_findings_target_id")
        batch.drop_column("occurrence_count")
        batch.drop_column("last_seen")
        batch.drop_column("first_seen")
        batch.drop_column("fingerprint")
        batch.drop_column("target_id")
