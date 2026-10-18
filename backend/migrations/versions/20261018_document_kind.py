"""Declare uploaded document provenance without claiming issuer verification."""
from alembic import op
import sqlalchemy as sa

revision = "20261018_document_kind"
down_revision = "20261018_self_service"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("policy_documents", sa.Column("document_kind", sa.String(), nullable=False, server_default="USER_PROVIDED"))
    op.create_check_constraint("ck_policy_document_kind", "policy_documents", "document_kind IN ('USER_PROVIDED','PUBLIC_REFERENCE','TEST_FIXTURE')")


def downgrade():
    op.drop_constraint("ck_policy_document_kind", "policy_documents", type_="check")
    op.drop_column("policy_documents", "document_kind")
