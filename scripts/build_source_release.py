"""Build a curated source ZIP from committed Git objects, not the working tree."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile


PACKAGE_README = "docs/releases/source_readme.md"
ROOT_FILES = {".env.example", ".gitignore", "LICENSE", "compose.yaml", "requirements.txt"}
RUNTIME_DIRS = {"app", "frontend_cli", "desktop", "docker", "sql"}
SCRIPT_NAMES = {
    "govern_historical_tags.py", "grant-admin.ps1", "load-oracle-schema.ps1",
    "load-seed-data.ps1", "reclassify_question_categories.py", "start-business-test.ps1",
    "start-oracle26ai.ps1", "start_business_test.py", "test-admin-api.ps1",
    "validate-oracle-schema.ps1", "validate_chat_followup.py",
}
PROMO_NAMES = {
    "ai-qa-community-logo-aiq.png", "ai-qa-community-enterprise-saas-promo.mp4",
    "ai-qa-community-enterprise-saas-promo-poster.png",
}
REQUIRED_PATHS = ROOT_FILES | {
    PACKAGE_README, "app/main.py", "app/web/home.html", "frontend_cli/main.py",
    "sql/create_tables.sql", "sql/procedures.sql", "sql/triggers.sql", "sql/views.sql",
    "sql/seed_data.sql", "scripts/start-oracle26ai.ps1", "scripts/load-oracle-schema.ps1",
    "scripts/load-seed-data.ps1", "docker/oracle/startup/01-create-app-user.sh",
    "desktop/package.json", "desktop/package-lock.json", "desktop/src-tauri/Cargo.lock",
    "desktop/src/index.html",
} | {f"promo/{name}" for name in PROMO_NAMES}


def include_path(name: str) -> bool:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        return False
    if set(path.parts) & {".git", ".venv", "node_modules", "__pycache__", "target", "gen", "dist"}:
        return False
    if path.name.startswith(".env") and name != ".env.example":
        return False
    if path.suffix.lower() in {".log", ".pyc", ".pyo", ".db", ".sqlite", ".tmp"}:
        return False
    if name in ROOT_FILES:
        return True
    if path.parts[0] in RUNTIME_DIRS:
        return path.suffix.lower() != ".md"
    if path.parts[0] == "scripts":
        return len(path.parts) == 2 and path.name in SCRIPT_NAMES
    return name in {f"promo/{item}" for item in PROMO_NAMES}


def build_release(repo: Path, ref: str, version: str, output: Path) -> Path:
    if not re.fullmatch(r"v\d+\.\d+\.\d+", version):
        raise ValueError("Version must use vMAJOR.MINOR.PATCH format")

    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(repo), *args])

    commit = git("rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    timestamp = int(git("show", "-s", "--format=%ct", commit))
    tree = {}
    for entry in git("ls-tree", "-rz", commit).split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        name = path.decode("utf-8")
        if include_path(name) or name == PACKAGE_README:
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise ValueError(f"Unsupported release entry: {name}")
            tree[name] = (mode, oid)
    missing = REQUIRED_PATHS - tree.keys()
    if missing:
        raise ValueError(f"Missing required release files: {', '.join(sorted(missing))}")

    payload, modes = {}, {}
    for name, (mode, oid) in sorted(tree.items()):
        target = "README.md" if name == PACKAGE_README else name
        payload[target] = git("cat-file", "blob", oid)
        modes[target] = int(mode, 8)
    manifest = {
        "version": version,
        "source_repository": "https://github.com/yiguoyi1/ai-qa-db-course-project",
        "source_commit": commit,
        "readme_source": PACKAGE_README,
        "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payload.items())},
    }
    payload["SOURCE_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / f"askwise-community-{version}-source.zip"
    checksum_path = archive_path.with_suffix(".zip.sha256")
    if archive_path.exists() or checksum_path.exists():
        raise FileExistsError(f"Refusing to overwrite an existing release: {archive_path}")

    # A fixed commit timestamp and sorted paths make repeated builds byte-identical.
    date_time = datetime.fromtimestamp(max(timestamp, 315532800), timezone.utc).timetuple()[:6]
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(f"askwise-community-{version}/{name}", date_time=date_time)
            info.create_system = 3
            info.external_attr = modes.get(name, 0o100644) << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="ascii")
    return archive_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--ref", default="HEAD", help="Committed Git ref to package")
    parser.add_argument("--output", type=Path, default=Path("dist/releases"))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    print(build_release(repo, args.ref, args.version, args.output).resolve())


if __name__ == "__main__":
    main()
