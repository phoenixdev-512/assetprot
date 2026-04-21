import json
import subprocess


def compute_chromaprint(file_path: str) -> bytes | None:
    result = subprocess.run(
        ["fpcalc", "-json", file_path],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    fingerprint_str = data.get("fingerprint", "")
    if not fingerprint_str:
        return None
    return fingerprint_str.encode("ascii")
