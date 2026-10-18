"""Consented provider scenarios and durable delayed delivery."""
from alembic import op
import sqlalchemy as sa

revision = "20261018_self_service"
down_revision = "9f40f776cbf8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("payment_orders", sa.Column("sandbox_scenario", sa.String(), nullable=False, server_default="MANUAL"))
    op.create_check_constraint("ck_order_sandbox_scenario", "payment_orders", "sandbox_scenario IN ('MANUAL','SUCCESS','DECLINED')")
    op.add_column("mock_provider_outbox", sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))


def downgrade():
    op.drop_column("mock_provider_outbox", "available_at")
    op.drop_constraint("ck_order_sandbox_scenario", "payment_orders", type_="check")
    op.drop_column("payment_orders", "sandbox_scenario")
