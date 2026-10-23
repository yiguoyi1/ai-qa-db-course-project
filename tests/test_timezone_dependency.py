import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TimezoneDependencyTests(unittest.TestCase):
    def test_timezone_data_is_declared(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertTrue(any(line.startswith("tzdata") for line in requirements.splitlines()))

    def test_api_datetime_serializes_without_system_timezone_database(self):
        environment = {**os.environ, "PYTHONTZPATH": "", "PYTHONDONTWRITEBYTECODE": "1"}
        code = (
            "from datetime import datetime, timezone; "
            "from app.schemas.base import _serialize_api_datetime; "
            "assert _serialize_api_datetime(datetime(2026, 10, 23, 0, 0, tzinfo=timezone.utc)) "
            "== '2026-10-23T08:00:00+08:00'"
        )
        result = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT,
                                env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
