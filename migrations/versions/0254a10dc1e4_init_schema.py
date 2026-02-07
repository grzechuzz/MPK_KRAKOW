from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0254a10dc1e4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('gtfs_meta',
        sa.Column('agency', sa.Text(), nullable=False),
        sa.Column('current_hash', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('agency')
    )

    op.create_table(
        "current_routes",
        sa.Column("route_id", sa.Text(), nullable=False),
        sa.Column("agency_id", sa.Text(), nullable=False),
        sa.Column("route_short_name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("route_id")
    )

    op.create_table(
        "current_stops",
        sa.Column("stop_id", sa.Text(), nullable=False),
        sa.Column("stop_name", sa.Text(), nullable=False),
        sa.Column("stop_code", sa.Text(), nullable=True),
        sa.Column("stop_desc", sa.Text(), nullable=True),
        sa.Column("stop_lat", sa.Double(), nullable=True),
        sa.Column("stop_lon", sa.Double(), nullable=True),
        sa.PrimaryKeyConstraint("stop_id")
    )

    op.create_table(
        "current_trips",
        sa.Column("trip_id", sa.Text(), nullable=False),
        sa.Column("route_id", sa.Text(), nullable=False),
        sa.Column("service_id", sa.Text(), nullable=False),
        sa.Column("direction_id", sa.SmallInteger(), nullable=True),
        sa.Column("headsign", sa.Text(), nullable=True),
        sa.Column("shape_id", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("trip_id"),
        sa.ForeignKeyConstraint(["route_id"], ["current_routes.route_id"])
    )
    op.create_index("idx_current_trips_route", "current_trips", ["route_id"])
    op.create_index("idx_current_trips_shape", "current_trips", ["shape_id"])

    op.create_table(
        "current_stop_times",
        sa.Column("trip_id", sa.Text(), nullable=False),
        sa.Column("stop_sequence", sa.Integer(), nullable=False),
        sa.Column("stop_id", sa.Text(), nullable=False),
        sa.Column("arrival_seconds", sa.Integer(), nullable=False),
        sa.Column("departure_seconds", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("trip_id", "stop_sequence"),
        sa.ForeignKeyConstraint(["trip_id"], ["current_trips.trip_id"]),
        sa.ForeignKeyConstraint(["stop_id"], ["current_stops.stop_id"])
    )
    op.create_index("idx_current_stop_times_stop", "current_stop_times", ["stop_id"])

    op.create_table(
        "current_shapes",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("agency_id", sa.Text(), nullable=False),
        sa.Column("shape_id", sa.Text(), nullable=False),
        sa.Column("shape_pt_lat", sa.Double(), nullable=False),
        sa.Column("shape_pt_lon", sa.Double(), nullable=False),
        sa.Column("shape_pt_sequence", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("""
        CREATE TABLE stop_events (
            id BIGINT GENERATED ALWAYS AS IDENTITY,
            agency TEXT NOT NULL,
            trip_id TEXT NOT NULL,
            service_date DATE NOT NULL,
            stop_sequence INTEGER NOT NULL,
            stop_id TEXT NOT NULL,
            line_number TEXT NOT NULL,
            stop_name TEXT NOT NULL,
            stop_desc TEXT,
            direction_id SMALLINT,
            headsign TEXT,
            planned_time TIMESTAMPTZ NOT NULL,
            event_time TIMESTAMPTZ NOT NULL,
            delay_seconds INTEGER NOT NULL,
            vehicle_id TEXT,
            license_plate TEXT,
            detection_method SMALLINT NOT NULL,
            is_estimated BOOLEAN NOT NULL DEFAULT FALSE,
            static_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, service_date)
        ) PARTITION BY RANGE (service_date)
    """)

    op.execute("""
        CREATE TABLE stop_events_2026_02 PARTITION OF stop_events
        FOR VALUES FROM ('2026-02-01') TO ('2026-03-01')
    """)

    op.execute("""
        CREATE TABLE stop_events_2026_03 PARTITION OF stop_events
        FOR VALUES FROM ('2026-03-01') TO ('2026-04-01')
    """)

    op.execute("""
        CREATE TABLE stop_events_2026_04 PARTITION OF stop_events
        FOR VALUES FROM ('2026-04-01') TO ('2026-05-01')
    """)

    op.execute("""
        CREATE UNIQUE INDEX uq_stop_events_trip_date_seq
        ON stop_events (trip_id, service_date, stop_sequence)
    """)

    op.execute("""
        CREATE INDEX idx_stop_events_line_time
        ON stop_events (line_number, event_time)
    """)

    op.execute("""
        CREATE INDEX idx_stop_events_stop_time
        ON stop_events (stop_id, event_time)
    """)


def downgrade() -> None:
    op.drop_table("stop_events_2026_03")
    op.drop_table("stop_events_2026_02")
    op.drop_table("stop_events_2026_01")
    op.drop_table("stop_events")
    op.drop_table("current_shapes")
    op.drop_table("current_stop_times")
    op.drop_table("current_trips")
    op.drop_table("current_stops")
    op.drop_table("current_routes")
    op.drop_table("gtfs_meta")
