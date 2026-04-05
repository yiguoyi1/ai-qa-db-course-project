from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib import error, request


REPO_ROOT = Path(__file__).resolve().parents[1]


def is_api_healthy(base_url: str) -> bool:
    try:
        with request.urlopen(f"{base_url}/health", timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("status") == "ok"
    except (error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False


def wait_for_api(base_url: str, timeout_seconds: int = 30) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_api_healthy(base_url):
            return True
        time.sleep(1)
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start the business-test entrypoint for the AI QA platform."
    )
    parser.add_argument("--host", default="127.0.0.1", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument(
        "--skip-api-start",
        action="store_true",
        help="Reuse an already running API instead of starting uvicorn",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    base_url = f"http://{args.host}:{args.port}"
    started_process: subprocess.Popen[str] | None = None

    try:
        if not args.skip_api_start:
            if is_api_healthy(base_url):
                print(f"Detected running API at {base_url}, reusing it.", flush=True)
            else:
                print(f"Starting API at {base_url} ...", flush=True)
                started_process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "app.main:app",
                        "--host",
                        args.host,
                        "--port",
                        str(args.port),
                    ],
                    cwd=REPO_ROOT,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )

                if not wait_for_api(base_url, timeout_seconds=30):
                    print("API did not become healthy within 30 seconds.", file=sys.stderr)
                    return 1
        elif not is_api_healthy(base_url):
            print(
                f"--skip-api-start was set, but the API is not reachable at {base_url}.",
                file=sys.stderr,
            )
            return 1

        print("Opening business test menu ...", flush=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "frontend_cli.main",
                "--base-url",
                base_url,
                "menu",
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        return int(result.returncode)
    finally:
        if started_process is not None and started_process.poll() is None:
            print("Stopping API process started by this script ...", flush=True)
            started_process.terminate()
            try:
                started_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                started_process.kill()
                started_process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
