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
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    # The earliest migration uses current Base.metadata; fresh installations may
    # already include the new columns. Some legacy test databases deliberately
    # contain only the tables affected by the v1.1 migration.
    if "findings" not in inspector.get_table_names():
        return
    columns = {item["name"] for item in inspector.get_columns("findings")}
    indexes = {item["name"] for item in inspector.get_indexes("findings")}
    constraints = {item["name"] for item in inspector.get_unique_constraints("findings")}
    new_columns = [
        ("target_id", sa.String(36)),
        ("fingerprint", sa.String(64)),
        ("first_seen", sa.DateTime(timezone=True)),
        ("last_seen", sa.DateTime(timezone=True)),
        ("occurrence_count", sa.Integer()),
    ]
    if any(name not in columns for name, _type in new_columns) or (
        "ix_findings_target_id" not in indexes
        or "uq_findings_project_fingerprint" not in constraints
    ):
        with op.batch_alter_table("findings") as batch:
            for name, column_type in new_columns:
                if name not in columns:
                    batch.add_column(sa.Column(name, column_type, nullable=True))
            if "ix_findings_target_id" not in indexes:
                batch.create_index("ix_findings_target_id", ["target_id"])
            if "uq_findings_project_fingerprint" not in constraints:
                batch.create_unique_constraint(
                    "uq_findings_project_fingerprint", ["project_id", "fingerprint"]
                )
    # Backfill only the pre-existing rows; new records receive Python defaults.
    op.execute(
        "UPDATE findings SET first_seen = COALESCE(first_seen, created_at), "
        "last_seen = COALESCE(last_seen, updated_at), "
        "occurrence_count = COALESCE(occurrence_count, 1)"
    )
    if {"first_seen", "last_seen", "occurrence_count"} - columns:
        with op.batch_alter_table("findings") as batch:
            batch.alter_column("first_seen", nullable=False)
            batch.alter_column("last_seen", nullable=False)
            batch.alter_column("occurrence_count", nullable=False)
    if "finding_occurrences" not in sa.inspect(conn).get_table_names():
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
    inspector = sa.inspect(op.get_bind())
    if "finding_occurrences" in inspector.get_table_names():
        for index in inspector.get_indexes("finding_occurrences"):
            op.drop_index(index["name"], "finding_occurrences")
        op.drop_table("finding_occurrences")
    if "findings" not in inspector.get_table_names():
        return
    with op.batch_alter_table("findings") as batch:
        batch.drop_constraint("uq_findings_project_fingerprint", type_="unique")
        batch.drop_index("ix_findings_target_id")
        batch.drop_column("occurrence_count")
        batch.drop_column("last_seen")
        batch.drop_column("first_seen")
        batch.drop_column("fingerprint")
        batch.drop_column("target_id")
