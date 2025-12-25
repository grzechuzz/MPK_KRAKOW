from pathlib import Path
import requests


class DownloadError(RuntimeError):
    pass


def download_gtfs_zip(url: str, dest_dir: str | Path, filename: str = "GTFS_KRK_A.zip", timeout_seconds: int = 30) -> Path:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    final_path = dest_dir / filename
    temp_path = dest_dir / f"{filename}.part"

    try:
        with requests.get(url, stream=True, timeout=timeout_seconds) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        temp_path.replace(final_path)
        return final_path

    except (requests.exceptions.RequestException, OSError) as e:
        temp_path.unlink(missing_ok=True)
        raise DownloadError(f"Failed to download GTFS zip from {url!r}: {e}") from e
