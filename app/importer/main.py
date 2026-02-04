import time
from pathlib import Path

from app.common.db.connection import get_session
from app.common.db.repositories.gtfs_meta import GtfsMetaRepository
from app.common.feeds import get_all_feed_configs
from app.common.gtfs.hashing import sha256_file
from app.importer.download import download_gtfs_zip
from app.importer.load import load_gtfs_zip


def run_import() -> None:
    """Run GTFS static import for all configured feeds."""
    feed_configs = get_all_feed_configs()

    for feed_config in feed_configs:
        try:
            zip_path = download_gtfs_zip(feed_config)
            new_hash = sha256_file(zip_path)

            with get_session() as session:
                meta_repo = GtfsMetaRepository(session)
                current_hash = meta_repo.get_current_hash(feed_config.agency)

                if current_hash == new_hash:
                    Path(zip_path).unlink()
                    continue

                load_gtfs_zip(session, zip_path, feed_config.agency.value)
                meta_repo.set_current_hash(feed_config.agency, new_hash)

            Path(zip_path).unlink()

        except Exception as e:
            print(f"Failed to import {feed_config.agency.value}: {e}")


def main() -> None:
    """Run import every hour in a loop"""
    while True:
        try:
            run_import()
        except Exception:
            pass

        time.sleep(3600)


if __name__ == "__main__":
    main()
