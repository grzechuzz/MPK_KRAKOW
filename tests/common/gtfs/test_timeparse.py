import pytest

from app.common.app_common.gtfs.timeparse import parse_gtfs_time_to_seconds


def test_basic_times():
    assert parse_gtfs_time_to_seconds("00:00:00") == 0
    assert parse_gtfs_time_to_seconds("01:02:03") == 3723


def test_above_24():
    assert parse_gtfs_time_to_seconds("25:10:00") == 25 * 3600 + 10 * 60


@pytest.mark.parametrize("value", ["1:2:3", "aa", "10:70:00", "10:00:70", "", None])
def test_invalid_times(value):
    with pytest.raises(ValueError):
        parse_gtfs_time_to_seconds(value)
