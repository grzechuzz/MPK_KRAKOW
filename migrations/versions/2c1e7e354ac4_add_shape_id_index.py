"""add shape id index

Revision ID: 2c1e7e354ac4
Revises: 86828ea9a33c
Create Date: 2026-02-16 14:05:17.502935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c1e7e354ac4'
down_revision: Union[str, Sequence[str], None] = '86828ea9a33c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("idx_current_shapes_shape_seq", "current_shapes", ["shape_id", "shape_pt_sequence"])


def downgrade() -> None:
    op.drop_index("idx_current_shapes_shape_seq", table_name="current_shapes")
