from pathlib import Path

from app.common.app_common.gtfs.hashing import sha256_file


def test_sha256_file(tmp_path: Path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"abc")
    assert sha256_file(p) == ("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
