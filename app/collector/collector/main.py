import time
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.collector.collector.build import build_stop_events
from app.collector.collector.fetch import fetch_vehicle_positions_pb
from app.collector.collector.parse import parse_vehicle_positions
from app.collector.collector.settings import POLL_SECONDS, TZ
from app.collector.collector.static_lookup import StaticStop, fetch_static_for_vp
from app.collector.collector.writer import insert_stop_events
from app.common.app_common.db.meta import get_current_static_hash
from app.common.app_common.db.session import engine


def _now_str(tz: ZoneInfo) -> str:
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def _fetch_stops_by_ids(conn, stop_ids: list[str]) -> dict[str, StaticStop]:
    if not stop_ids:
        return {}
    q = text(
        """
        SELECT stop_id, stop_name
        FROM current_stops
        WHERE stop_id = ANY(:stop_ids)
        """
    )
    rows = conn.execute(q, {"stop_ids": stop_ids}).mappings().all()
    return {r["stop_id"]: StaticStop(stop_id=r["stop_id"], stop_name=r["stop_name"]) for r in rows}


def run_once() -> tuple[int, int]:
    pb = fetch_vehicle_positions_pb()
    feed_ts, items = parse_vehicle_positions(pb)

    trip_ids = [x.trip_id for x in items]
    trip_seq_pairs = [
        (x.trip_id, int(x.stop_sequence)) for x in items if x.stop_sequence is not None
    ]

    with engine.begin() as conn:
        static_hash = get_current_static_hash(conn)
        if not static_hash:
            print("[collector] waiting for importer/static (no gtfs_meta.current_hash yet)")
            return 0, 0
        trips_by_id, stoptimes_by_key, _ = fetch_static_for_vp(
            conn,
            trip_ids=trip_ids,
            stop_ids=[],
            trip_seq_pairs=trip_seq_pairs,
        )

        stop_ids_from_stoptimes = list({st.stop_id for st in stoptimes_by_key.values()})
        stops_by_id = _fetch_stops_by_ids(conn, stop_ids_from_stoptimes)

        built = build_stop_events(
            items=items,
            trips_by_id=trips_by_id,
            stoptimes_by_key=stoptimes_by_key,
            stops_by_id=stops_by_id,
            static_hash=static_hash,
            tz=TZ,
        )

        inserted = insert_stop_events(conn, built)

    return len(built), inserted


def main() -> None:
    print(f"[collector] start {_now_str(TZ)} poll={POLL_SECONDS}s")
    while True:
        t0 = time.time()
        try:
            built_cnt, inserted_cnt = run_once()
            dt = time.time() - t0
            print(
                f"[collector] {_now_str(TZ)} built={built_cnt} inserted={inserted_cnt} dt={dt:.2f}s"
            )
        except Exception as e:
            dt = time.time() - t0
            print(f"[collector] {_now_str(TZ)} ERROR after {dt:.2f}s: {e!r}")

        sleep_s = max(0.0, float(POLL_SECONDS) - (time.time() - t0))
        time.sleep(sleep_s)


if __name__ == "__main__":
    main()
