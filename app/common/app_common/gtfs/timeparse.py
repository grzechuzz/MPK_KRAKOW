def parse_gtfs_time_to_seconds(value: str) -> int:
    """
    Returns the number of seconds since midnight of the service day.
    
    Note: GTFS stop_times.txt uses HH:MM:SS format where hours may exceed 24 (e.g. "25:10:00")
    """
    if value is None:
        raise ValueError("GTFS time is None")

    s = value.strip()
    parts = s.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid GTFS time format: {value!r}")

    h_str, m_str, sec_str = parts 
    
    if not (h_str.isdigit() and m_str.isdigit() and sec_str.isdigit()):
        raise ValueError(f"Invalid GTFS time format: {value!r}")

    if len(m_str) != 2 or len(sec_str) != 2:
        raise ValueError(f"Invalid GTFS time format: {value!r}")

    h = int(h_str)
    m = int(m_str)
    sec = int(sec_str)

    if m < 0 or m > 59 or sec < 0 or sec > 59 or h < 0:
        raise ValueError(f"Invalid GTFS time value: {value!r}")

    return h * 3600 + m * 60 + sec

