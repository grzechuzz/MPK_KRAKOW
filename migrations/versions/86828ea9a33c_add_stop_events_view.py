"""add stop_events view

Revision ID: 86828ea9a33c
Revises: 0254a10dc1e4
Create Date: 2026-02-09 01:47:18.558296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86828ea9a33c'
down_revision: Union[str, Sequence[str], None] = '0254a10dc1e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
               CREATE VIEW stop_events_view AS
               SELECT id, agency, service_date, stop_sequence, line_number, stop_name, stop_desc, headsign,
                      planned_time AT TIME ZONE 'Europe/Warsaw' AS planned_time,
                      event_time AT TIME ZONE 'Europe/Warsaw' AS event_time,
                      delay_seconds, license_plate, detection_method, is_estimated,
                      created_at AT TIME ZONE 'Europe/Warsaw'   AS created_at
               FROM stop_events
               """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS stop_events_view")
