from __future__ import annotations

import subprocess
import sys
import time
import urllib.request


def wait_for_api(url: str, timeout_seconds: int = 40) -> None:
    deadline = time.time() + timeout_seconds
    last_error = ""

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception as exc:
            last_error = str(exc)
            time.sleep(0.5)

    raise RuntimeError(f"Mock enrichment API did not become healthy. Last error: {last_error}")


def main() -> int:
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_enrichment_api.app:app", "--host", "127.0.0.1", "--port", "8900"],
    )

    try:
        wait_for_api("http://127.0.0.1:8900")
        return subprocess.call([sys.executable, "-m", "pipeline.main"])
    finally:
        api.terminate()
        try:
            api.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api.kill()


if __name__ == "__main__":
    raise SystemExit(main())