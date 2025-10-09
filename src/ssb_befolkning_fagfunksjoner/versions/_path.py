from upath import UPath


def resolve_path(filepath: str | UPath) -> UPath:
    """Normalise the input path string to a form that can be safely passed to UPath.

    Supported formats:
    - 'gs://ssb-<dapla-name>-<bucket>-data-<env>/...' (GCS path with prefix)
    - 'ssb-<dapla-name>-<bucket>-data-<env>/...' (GCS path without prefix)
    - '/buckets/<bucket>/...' (local path on mounted filesystem)
    - UPath objects

    Parameters:
    - filepath (str | UPath): The input path to normalize.

    Returns:
        UPath: Fully resolved GCS path (starting with 'gs://') or an absolute local path.

    Raises:
        ValueError: If the path format is not supported or if a local bucket path is not mounted.
    """
    if isinstance(filepath, UPath):
        return filepath

    if filepath.startswith("gs://"):
        return UPath(filepath)

    elif filepath.startswith("/buckets"):
        try:
            return UPath(filepath)
        except FileNotFoundError as e:
            raise ValueError(
                f"Local bucket path '{filepath}' must be mounted in DaplaLab."
            ) from e

    elif filepath.startswith("ssb-"):
        return UPath(f"gs://{filepath}")

    else:
        raise ValueError(f"Unsupported path format: {filepath}")
