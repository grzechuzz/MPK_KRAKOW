"""add gtfs_static and events schemas

Revision ID: 4a8b9c2d3e1f
Revises: 01d4d78ab2b2
Create Date: 2026-03-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = '4a8b9c2d3e1f'
down_revision: Union[str, Sequence[str], None] = '01d4d78ab2b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA gtfs_static")
    op.execute("CREATE SCHEMA events")

    for table in ["gtfs_meta", "current_routes", "current_trips",
                  "current_stop_times", "current_shapes", "current_stops"]:
        op.execute(f"ALTER TABLE {table} SET SCHEMA gtfs_static")

    op.execute("DROP VIEW IF EXISTS stop_events_view")
    op.execute("ALTER TABLE stop_events SET SCHEMA events")

    op.execute("GRANT USAGE ON SCHEMA gtfs_static TO api_reader")
    op.execute("GRANT USAGE ON SCHEMA events TO api_reader")
    op.execute("GRANT ALL ON SCHEMA gtfs_static TO importer")
    op.execute("GRANT ALL ON SCHEMA events TO writer")


def downgrade() -> None:
    op.execute("REVOKE USAGE ON SCHEMA gtfs_static FROM api_reader")
    op.execute("REVOKE USAGE ON SCHEMA events FROM api_reader")
    op.execute("REVOKE ALL ON SCHEMA gtfs_static FROM importer")
    op.execute("REVOKE ALL ON SCHEMA events FROM writer")

    op.execute("ALTER TABLE events.stop_events SET SCHEMA public")

    for table in reversed(["gtfs_meta", "current_routes", "current_trips",
                            "current_stop_times", "current_shapes", "current_stops"]):
        op.execute(f"ALTER TABLE gtfs_static.{table} SET SCHEMA public")

    op.execute("DROP SCHEMA gtfs_static")
    op.execute("DROP SCHEMA events")
