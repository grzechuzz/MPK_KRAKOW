import shutil
from pathlib import Path


class ArchiveError(RuntimeError):
    pass


def archive_zip_by_hash(
    downloaded_zip: str | Path, archive_dir: str | Path, sha256_hex: str
) -> Path:
    downloaded_zip = Path(downloaded_zip)
    archive_dir = Path(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)

    archived = archive_dir / f"{sha256_hex}.zip"

    try:
        if archived.exists():
            downloaded_zip.unlink(missing_ok=True)
            return archived

        shutil.move(str(downloaded_zip), str(archived))
        return archived

    except OSError as e:
        raise ArchiveError(f"Failed to archive zip {downloaded_zip} as {archived}: {e}") from e
