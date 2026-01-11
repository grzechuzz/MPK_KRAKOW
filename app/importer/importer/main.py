import shutil
from pathlib import Path

from app.common.app_common.db.meta import get_current_static_hash, set_current_static_hash
from app.common.app_common.db.session import engine
from app.common.app_common.gtfs.hashing import sha256_file
from app.importer.importer.archive import archive_zip_by_hash
from app.importer.importer.download import download_gtfs_zip
from app.importer.importer.extract import extract_gtfs_zip
from app.importer.importer.load import load_static_gtfs

URL = "https://gtfs.ztp.krakow.pl/GTFS_KRK_A.zip"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run() -> int:
    root = _project_root()
    data_dir = root / "data" / "gtfs"
    downloads_dir = data_dir / "downloads"
    archives_dir = data_dir / "archives"

    # 1. download
    zip_path = download_gtfs_zip(
        URL,
        dest_dir=downloads_dir,
        filename="GTFS_KRK_A.zip",
    )

    # 2. hash
    zip_hash = sha256_file(zip_path)

    # 3. archive by hash
    archived_zip = archive_zip_by_hash(
        zip_path,
        archive_dir=archives_dir,
        sha256_hex=zip_hash,
    )

    # 4. extract + load
    extract_root, base_dir = extract_gtfs_zip(archived_zip)
    try:
        with engine.begin() as conn:
            current_hash = get_current_static_hash(conn)
            if current_hash == zip_hash:
                print("Static GTFS unchanged — skipping reload")
                return 0

            load_static_gtfs(conn, base_dir)
            set_current_static_hash(conn, zip_hash)

        print(f"Static GTFS loaded, hash={zip_hash}")
        return 0
    finally:
        shutil.rmtree(extract_root, ignore_errors=True)


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
