"""Session-bound optional cloud AI permissions."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c41a15fa8b20"
down_revision = "b8d1b38c527a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("ai_permissions",
        sa.Column("subject", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("demo_users.id"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("notice_version", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("scopes", postgresql.JSONB(), nullable=False),
        sa.Column("data_mode", sa.String(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision > 0"),
        sa.CheckConstraint("data_mode IN ('DEMO_ONLY','PAID_PRIVATE')"))
    op.create_index("ix_ai_permissions_user_id", "ai_permissions", ["user_id"])


def downgrade():
    op.drop_table("ai_permissions")
