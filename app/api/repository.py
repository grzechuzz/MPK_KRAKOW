from datetime import date, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.constants import MIN_DELAY_SECONDS


def resolve_date_range(period: str) -> tuple[date, date]:
    """Convert period string to (start_date, end_date)"""
    today = date.today()
    if period == "today":
        return today, today
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        return start, today
    else:
        start = today.replace(day=1)
        return start, today


class StatsRepository:
    def __init__(self, session: Session):
        self._session = session

    def max_delay_between_stops(self, line_number: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Generated delay = delay at stop N+1 - delay at stop N."""
        result = self._session.execute(
            text("""
                WITH max_seqs AS (
                    SELECT trip_id, service_date, MAX(stop_sequence) AS max_seq FROM stop_events
                    WHERE line_number = :line_number AND service_date BETWEEN :start_date AND :end_date
                    GROUP BY trip_id, service_date
                ),
                filtered AS (
                    SELECT e.trip_id, e.service_date, e.stop_sequence, e.stop_name, e.headsign, e.delay_seconds,
                    e.line_number, e.license_plate, e.planned_time, e.event_time
                    FROM stop_events e
                    JOIN max_seqs m USING (trip_id, service_date)
                    WHERE e.line_number = :line_number AND e.service_date BETWEEN :start_date AND :end_date
                    AND e.stop_sequence > 1 AND e.stop_sequence < m.max_seq
                ),
                consecutive AS (
                    SELECT trip_id, service_date, stop_sequence, stop_name, headsign, line_number, license_plate,
                    delay_seconds, planned_time, event_time,
                    delay_seconds - LAG(delay_seconds) OVER w AS generated_delay,
                    LAG(delay_seconds) OVER w AS prev_delay,
                    LAG(stop_name) OVER w AS prev_stop_name,
                    LAG(stop_sequence) OVER w AS prev_stop_sequence,
                    LAG(planned_time) OVER w AS prev_planned_time,
                    LAG(event_time) OVER w AS prev_event_time
                    FROM filtered WINDOW w AS (
                        PARTITION BY trip_id, service_date
                        ORDER BY stop_sequence
                    )
                )
                SELECT trip_id, service_date, line_number, license_plate AS vehicle_number, prev_stop_name AS from_stop,
                stop_name AS to_stop, prev_stop_sequence AS from_sequence, stop_sequence AS to_sequence,
                prev_planned_time AT TIME ZONE 'Europe/Warsaw' AS from_planned_time,
                prev_event_time AT TIME ZONE 'Europe/Warsaw' AS from_event_time,
                planned_time AT TIME ZONE 'Europe/Warsaw' AS to_planned_time,
                event_time AT TIME ZONE 'Europe/Warsaw' AS to_event_time,
                generated_delay AS delay_generated_seconds, headsign
                FROM consecutive
                WHERE generated_delay IS NOT NULL
                  AND prev_delay >= :min_delay
                ORDER BY generated_delay DESC
                LIMIT 10
            """),
            {
                "line_number": line_number,
                "start_date": start_date,
                "end_date": end_date,
                "min_delay": MIN_DELAY_SECONDS,
            },
        )
        return [dict(r) for r in result.mappings().all()]

    def trips_count(self, line_number: str, start_date: date, end_date: date) -> int:
        """Count distinct trips for a line in the given period."""
        result = self._session.execute(
            text("""
                SELECT COUNT(DISTINCT (trip_id, service_date)) FROM stop_events
                WHERE line_number = :line_number AND service_date BETWEEN :start_date AND :end_date
            """),
            {
                "line_number": line_number,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        return result.scalar() or 0

    def max_route_delay(self, line_number: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """
        Route delay = delay at second-to-last stop - delay at second stop.
        First and last stops excluded due to garbage data.
        Trips where start_delay < MIN_DELAY_SECONDS are filtered.
        """
        result = self._session.execute(
            text("""
                WITH max_seqs AS (
                    SELECT trip_id, service_date, MAX(stop_sequence) AS max_seq FROM stop_events
                    WHERE line_number = :line_number AND service_date BETWEEN :start_date AND :end_date
                    GROUP BY trip_id, service_date
                ),
                filtered AS (
                    SELECT e.trip_id, e.service_date, e.stop_sequence, e.stop_name, e.headsign, e.delay_seconds,
                    e.line_number, e.license_plate
                    FROM stop_events e
                    JOIN max_seqs m USING (trip_id, service_date)
                    WHERE e.line_number = :line_number AND e.service_date BETWEEN :start_date AND :end_date
                    AND e.stop_sequence > 1 AND e.stop_sequence < m.max_seq
                ),
                trip_bounds AS (
                    SELECT trip_id, service_date, headsign, line_number, license_plate,
                    FIRST_VALUE(stop_name) OVER w AS first_stop,
                    LAST_VALUE(stop_name) OVER (
                        PARTITION BY trip_id, service_date
                        ORDER BY stop_sequence
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                    ) AS last_stop,
                    FIRST_VALUE(delay_seconds) OVER w AS start_delay,
                    LAST_VALUE(delay_seconds) OVER (
                        PARTITION BY trip_id, service_date
                        ORDER BY stop_sequence
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                    ) AS end_delay
                    FROM filtered
                    WINDOW w AS (
                        PARTITION BY trip_id, service_date
                        ORDER BY stop_sequence
                    )
                )
                SELECT DISTINCT ON (trip_id, service_date) trip_id, service_date, line_number,
                license_plate AS vehicle_number, first_stop, last_stop,
                start_delay AS start_delay_seconds, end_delay AS end_delay_seconds,
                (end_delay - start_delay) AS delay_generated_seconds, headsign
                FROM trip_bounds
                WHERE start_delay >= :min_delay
                ORDER BY trip_id, service_date, delay_generated_seconds DESC
            """),
            {
                "line_number": line_number,
                "start_date": start_date,
                "end_date": end_date,
                "min_delay": MIN_DELAY_SECONDS,
            },
        )
        rows = [dict(r) for r in result.mappings().all()]
        rows.sort(key=lambda r: r["delay_generated_seconds"], reverse=True)
        return rows[:10]

    def lines_summary(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Summary stats for all lines: avg delay, max delay, max generated delay."""
        result = self._session.execute(
            text("""
                WITH max_seqs AS (
                    SELECT trip_id, service_date, MAX(stop_sequence) AS max_seq
                    FROM stop_events
                    WHERE service_date BETWEEN :start_date AND :end_date
                    GROUP BY trip_id, service_date
                ),
                per_stop AS (
                    SELECT e.line_number, e.trip_id, e.service_date, e.stop_sequence, e.delay_seconds,
                    e.delay_seconds - LAG(e.delay_seconds) OVER (
                        PARTITION BY e.trip_id, e.service_date
                        ORDER BY e.stop_sequence
                    ) AS generated_delay,
                    LAG(e.delay_seconds) OVER (
                        PARTITION BY e.trip_id, e.service_date
                        ORDER BY e.stop_sequence
                    ) AS prev_delay
                    FROM stop_events e
                    JOIN max_seqs m USING (trip_id, service_date)
                    WHERE e.service_date BETWEEN :start_date AND :end_date
                    AND e.stop_sequence > 1 AND e.stop_sequence < m.max_seq
                )
                SELECT line_number, COUNT(DISTINCT (trip_id, service_date)) AS trips_count,
                ROUND(AVG(delay_seconds)::numeric, 1) AS avg_delay_seconds, MAX(delay_seconds) AS max_delay_seconds,
                COALESCE(MAX(CASE WHEN prev_delay >= :min_delay THEN generated_delay END), 0)
                    AS max_delay_between_stops_seconds
                FROM per_stop
                GROUP BY line_number
                ORDER BY max_delay_seconds DESC
            """),
            {
                "start_date": start_date,
                "end_date": end_date,
                "min_delay": MIN_DELAY_SECONDS,
            },
        )
        return [dict(r) for r in result.mappings().all()]

    def punctuality(self, line_number: str, start_date: date, end_date: date) -> dict[str, Any]:
        """
        Punctuality breakdown. Uses avg delay per trip (from stops 2 to n-1).
        Thresholds: on_time <= 120s, slightly_delayed 120-360s, delayed > 360s.
        """
        result = self._session.execute(
            text("""
                WITH max_seqs AS (
                    SELECT trip_id, service_date, MAX(stop_sequence) AS max_seq FROM stop_events
                    WHERE line_number = :line_number AND service_date BETWEEN :start_date AND :end_date
                    GROUP BY trip_id, service_date
                ),
                trip_avg AS (
                    SELECT e.trip_id, e.service_date, AVG(e.delay_seconds) AS avg_delay
                    FROM stop_events e
                    JOIN max_seqs m USING (trip_id, service_date)
                    WHERE e.line_number = :line_number AND e.service_date BETWEEN :start_date AND :end_date
                    AND e.stop_sequence > 1 AND e.stop_sequence < m.max_seq
                    AND e.delay_seconds >= :min_delay
                    GROUP BY e.trip_id, e.service_date
                )
                SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE avg_delay <= 120) AS on_time,
                COUNT(*) FILTER (WHERE avg_delay > 120 AND avg_delay <= 360) AS slightly_delayed,
                COUNT(*) FILTER (WHERE avg_delay > 360) AS delayed
                FROM trip_avg
            """),
            {
                "line_number": line_number,
                "start_date": start_date,
                "end_date": end_date,
                "min_delay": MIN_DELAY_SECONDS,
            },
        )
        row = result.mappings().first()
        return dict(row) if row else {"total": 0, "on_time": 0, "slightly_delayed": 0, "delayed": 0}

    def trend(self, line_number: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """Average delay per day for a line."""
        result = self._session.execute(
            text("""
                WITH max_seqs AS (
                    SELECT trip_id, service_date, MAX(stop_sequence) AS max_seq FROM stop_events
                    WHERE line_number = :line_number AND service_date BETWEEN :start_date AND :end_date
                    GROUP BY trip_id, service_date
                )
                SELECT e.service_date AS "date", ROUND(AVG(e.delay_seconds)::numeric, 1) AS avg_delay_seconds,
                COUNT(DISTINCT (e.trip_id, e.service_date)) AS trips_count
                FROM stop_events e
                JOIN max_seqs m USING (trip_id, service_date)
                WHERE e.line_number = :line_number AND e.service_date BETWEEN :start_date AND :end_date
                AND e.stop_sequence > 1 AND e.stop_sequence < m.max_seq
                AND e.delay_seconds >= :min_delay
                GROUP BY e.service_date
                ORDER BY e.service_date
            """),
            {
                "line_number": line_number,
                "start_date": start_date,
                "end_date": end_date,
                "min_delay": MIN_DELAY_SECONDS,
            },
        )
        return [dict(r) for r in result.mappings().all()]
