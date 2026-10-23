import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


BUILDER = Path(__file__).resolve().parents[1] / "scripts/build_source_release.py"


class SourceReleaseTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(BUILDER.is_file(), "A reproducible source release builder is required")
        spec = importlib.util.spec_from_file_location("release_builder", BUILDER)
        self.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.builder)

    def test_selection_excludes_private_and_generated_files(self):
        for name in (".env", "app/.env", "app/.env.production", "app/server.log",
                     "app/__pycache__/main.pyc", "docs/report/report.docx",
                     "seed_outputs/accounts.csv", "desktop/node_modules/x.js",
                     "desktop/src-tauri/target/app.exe", "scripts/seed_public_demo_data.py",
                     "scripts/import_public_snapshot_for_tag_test.py"):
            with self.subTest(name=name):
                self.assertFalse(self.builder.include_path(name))

    def test_selection_keeps_runtime_assets(self):
        for name in ("app/main.py", "app/web/home.html", "frontend_cli/main.py",
                     "sql/views.sql", "sql/migrations/example.sql", ".env.example",
                     "desktop/src-tauri/Cargo.lock", "docker/oracle/startup/01-create-app-user.sh",
                     "scripts/load-seed-data.ps1", "promo/ai-qa-community-logo-aiq.png"):
            with self.subTest(name=name):
                self.assertTrue(self.builder.include_path(name))

    def test_archive_uses_committed_files_and_records_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            def git(*args):
                return subprocess.check_output(["git", "-C", str(repo), *args])
            git("init", "--quiet")
            git("config", "core.autocrlf", "false")
            for name in self.builder.REQUIRED_PATHS:
                target = repo / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"committed content\n")
            (repo / ".env").write_bytes(b"secret must not ship")
            git("add", ".")
            git("-c", "user.name=Release test", "-c", "user.email=test@example.invalid",
                "commit", "--quiet", "-m", "fixture")
            commit = git("rev-parse", "HEAD").decode().strip()
            (repo / "app/main.py").write_bytes(b"uncommitted content")
            git("add", "app/main.py")
            (repo / "app/local_only.py").write_bytes(b"untracked content")
            first = self.builder.build_release(repo, "HEAD", "v0.1.1", Path(temp) / "one")
            git("-c", "user.name=Release test", "-c", "user.email=test@example.invalid",
                "commit", "--quiet", "-m", "newer fixture")
            second = self.builder.build_release(repo, commit, "v0.1.1", Path(temp) / "two")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            prefix = "askwise-community-v0.1.1/"
            with zipfile.ZipFile(first) as archive:
                self.assertIsNone(archive.testzip())
                self.assertNotIn(prefix + ".env", archive.namelist())
                self.assertNotIn(prefix + "app/local_only.py", archive.namelist())
                self.assertEqual(archive.read(prefix + "app/main.py"), b"committed content\n")
                manifest = json.loads(archive.read(prefix + "SOURCE_MANIFEST.json"))
                self.assertEqual(manifest["source_commit"], commit)
                self.assertEqual(archive.read(prefix + "README.md"), b"committed content\n")
                for name, digest in manifest["sha256"].items():
                    self.assertEqual(hashlib.sha256(archive.read(prefix + name)).hexdigest(), digest)
            self.assertEqual(first.with_suffix(".zip.sha256").read_text().split()[0],
                             hashlib.sha256(first.read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):
                self.builder.build_release(repo, "HEAD", "v0.1.1", Path(temp) / "one")
            oid = git("hash-object", ".env").decode().strip()
            git("update-index", "--add", "--cacheinfo", f"120000,{oid},app/unsafe_link.py")
            git("-c", "user.name=Release test", "-c", "user.email=test@example.invalid",
                "commit", "--quiet", "-m", "symlink fixture")
            with self.assertRaisesRegex(ValueError, "Unsupported release entry"):
                self.builder.build_release(repo, "HEAD", "v0.1.1", Path(temp) / "unsafe")

    def test_invalid_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                self.builder.build_release(Path(temp), "HEAD", "../../unsafe", Path(temp))

    def test_incomplete_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "-C", str(repo), "init", "--quiet"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Release test",
                            "-c", "user.email=test@example.invalid", "commit", "--quiet",
                            "--allow-empty", "-m", "empty fixture"], check=True)
            with self.assertRaisesRegex(ValueError, "Missing required release files"):
                self.builder.build_release(repo, "HEAD", "v0.1.1", repo / "output")


if __name__ == "__main__":
    unittest.main()
