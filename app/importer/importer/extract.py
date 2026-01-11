import shutil
import tempfile
from pathlib import Path
from zipfile import BadZipFile, ZipFile


class ExtractError(RuntimeError):
    pass


REQUIRED_FILES = ("routes.txt", "stops.txt", "trips.txt", "stop_times.txt")


def extract_gtfs_zip(zip_path: str | Path, work_dir: str | Path | None = None) -> tuple[Path, Path]:
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise ExtractError(f"ZIP not found: {zip_path}")

    if work_dir:
        root_dir = Path(work_dir)
        root_dir.mkdir(parents=True, exist_ok=True)
        should_cleanup = False
    else:
        root_dir = Path(tempfile.mkdtemp(prefix="gtfs_extract_"))
        should_cleanup = True

    try:
        with ZipFile(zip_path) as zf:
            zf.extractall(root_dir)

        base_dir = _find_base_dir(root_dir)
        _validate_gtfs(base_dir)
        return root_dir, base_dir

    except ExtractError:
        if should_cleanup:
            shutil.rmtree(root_dir, ignore_errors=True)
        raise

    except (BadZipFile, OSError) as e:
        if should_cleanup:
            shutil.rmtree(root_dir, ignore_errors=True)
        raise ExtractError(f"Extraction failed for {zip_path}: {e}") from e


def _find_base_dir(root_dir: Path) -> Path:
    if _has_required_files(root_dir):
        return root_dir

    subdirs = [p for p in root_dir.iterdir() if p.is_dir()]
    if len(subdirs) == 1 and _has_required_files(subdirs[0]):
        return subdirs[0]

    return root_dir


def _has_required_files(directory: Path) -> bool:
    return all((directory / f).exists() for f in REQUIRED_FILES)


def _validate_gtfs(directory: Path) -> None:
    missing = [f for f in REQUIRED_FILES if not (directory / f).exists()]
    if missing:
        raise ExtractError(f"Missing required GTFS files: {missing} in {directory}")
