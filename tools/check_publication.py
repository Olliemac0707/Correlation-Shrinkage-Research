"""Verify the portable protocol, copied evidence, source archives and local links."""

import hashlib
import json
import re
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_HASH = "72a337fd2b8093952cfc3cd00d82f35bb03c7d0bd4a1aaa9b4e0c4d960fa53da"
ROOT_FILES = {
    "README.md",
    "RESEARCH-REPORT.md",
    "AGENTS.md",
    "pyproject.toml",
    "requirements-lock.txt",
    ".gitignore",
    ".python-version",
}
DIRECTORIES = {".github", "protocol", "docs", "reports", "src", "tests", "tools"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    frozen = ROOT / "protocol/frozen/v1.0"
    assert sha(frozen / "manifest.json") == PROTOCOL_HASH
    manifest = json.loads((frozen / "manifest.json").read_text())
    for item in manifest["files"]:
        path = frozen / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert sha(path) == item["sha256"], item["path"]
    receipt = json.loads((ROOT / "docs/PUBLICATION-RECEIPT.json").read_text())
    for item in receipt["evidence"]:
        assert sha(ROOT / item["public_copy"]) == item["sha256"], item["public_copy"]
    archive_files = 0
    for category in ("synthetic", "historical"):
        folder = ROOT / "docs/results" / category
        run = json.loads((folder / "run-manifest.json").read_text())
        recorded = json.loads((folder / "artifact-manifest.json").read_text())
        for name in ("REPORT.md", "summary.json", "run-manifest.json"):
            assert sha(folder / name) == recorded[name], (category, name)
        for path in (folder / "figures").iterdir():
            assert sha(path) == recorded["figures/" + path.name], path.name
        with tarfile.open(folder / "source-archive.tar.gz", "r:gz") as archive:
            members = {member.name: member for member in archive.getmembers() if member.isfile()}
            assert set(members) == {"source/" + name for name in run["source_hashes"]}
            for name, expected in run["source_hashes"].items():
                stream = archive.extractfile(members["source/" + name])
                assert stream is not None
                assert hashlib.sha256(stream.read()).hexdigest() == expected, name
                archive_files += 1
        assert json.loads((folder / "audit.json").read_text())["status"] == "passed"
    summary = json.loads((ROOT / "docs/results/historical/summary.json").read_text())
    assert summary["targets"] == summary["expected_targets"] == 4780
    assert summary["matrix_failures"] == 0
    assert summary["complete_monthly_weight_pairs"] == 94
    paths = [ROOT / name for name in ROOT_FILES]
    for directory in DIRECTORIES:
        paths.extend(
            path
            for path in (ROOT / directory).rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    for path in paths:
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (path.parent / target.split("#", 1)[0]).resolve()
                assert resolved.is_relative_to(ROOT), (path.name, target)
                assert resolved.exists(), (path.relative_to(ROOT), target)
    if (ROOT / ".git").exists():
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        for name in filter(None, tracked):
            assert name in ROOT_FILES or Path(name).parts[0] in DIRECTORIES, name
            assert "__pycache__" not in Path(name).parts and not name.endswith(".pyc"), name
    print(
        f"Verified frozen protocol, copied evidence, {archive_files} archived source files "
        "and all public Markdown links."
    )


if __name__ == "__main__":
    check()
