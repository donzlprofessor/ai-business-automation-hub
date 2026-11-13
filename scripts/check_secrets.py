"""Small, dependency-free pre-publication guard. Never prints credential values.

Default: inspect tracked working files AND staged blobs. --source: inspect source
without Git; explicitly does not verify the Git index or history. This complements
a full secret scanner; it is not a proof that no secret of any kind exists.
"""
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".git", ".venv", "node_modules", "dist", "build", "__pycache__", ".pytest_cache",
    ".ruff_cache", "test-results", "playwright-report", "coverage",
}
PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b"),
]


def private_path(path: Path) -> bool:
    return (
        (path.name == ".env" or path.name.startswith(".env.")) and path.name != ".env.example"
    ) or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"} or path.name in {
        "id_rsa", "id_ed25519", ".npmrc", ".netrc",
    }


def local_secrets() -> list[str]:
    secrets = []
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            key, separator, value = line.partition("=")
            if separator and any(marker in key.upper() for marker in ("PASSWORD", "SECRET", "TOKEN", "KEY")):
                value = value.strip().strip("\"'")
                if len(value) >= 12 and not value.startswith("replace-"):
                    secrets.append(value)
    return secrets


def findings(content: str, secrets: list[str]) -> bool:
    return any(pattern.search(content) for pattern in PATTERNS) or any(
        secret in content for secret in secrets
    )


def source_paths():
    # Prune generated/dependency directories rather than scanning their contents.
    import os

    for directory, names, files in os.walk(ROOT):
        names[:] = [name for name in names if name not in EXCLUDED and not name.endswith(".egg-info")]
        for name in files:
            path = Path(directory) / name
            if not private_path(path):
                yield path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="store_true")
    args = parser.parse_args()
    secrets = local_secrets()
    failures: set[str] = set()
    if args.source:
        paths = list(source_paths())
        print("Source-only audit: Git index and history are NOT verified.")
    else:
        try:
            result = subprocess.run(
                ["git", "ls-files", "--cached", "-z"], cwd=ROOT, capture_output=True, check=False,
            )
        except FileNotFoundError:
            print("Git tracking check unavailable: Git is not installed.")
            return 2
        if result.returncode:
            print("Git tracking check unavailable: this directory is not an accessible Git repository.")
            print("Use --source for a limited source audit; rerun without it before publication.")
            return 2
        paths = [ROOT / name for name in result.stdout.decode().split("\0") if name]
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            if private_path(path):
                failures.add(relative + " (private file is tracked)")
            staged = subprocess.run(
                ["git", "show", f":{relative}"], cwd=ROOT, capture_output=True, check=False,
            )
            if staged.returncode or findings(staged.stdout.decode("utf-8", errors="replace"), secrets):
                failures.add(relative + " (staged content requires review)")
    for path in paths:
        if path.is_file() and findings(path.read_text(encoding="utf-8", errors="replace"), secrets):
            failures.add(path.relative_to(ROOT).as_posix() + " (working content requires review)")
    if failures:
        for failure in sorted(failures):
            print("REVIEW: " + failure)
        return 1
    print(f"No matching credentials detected in {len(paths)} inspected files.")
    print("Check complete; pattern checks do not replace a dedicated history secret scan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
