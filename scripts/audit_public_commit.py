"""Fail closed on private paths, binary blobs, and suspicious staged content.

Run after staging, alongside check_secrets.py. Only paths/rule names are printed.
This is a publication guard, not an exhaustive credential or personal-data detector.
"""
import re
import subprocess
from pathlib import Path

from scripts.check_secrets import findings, local_secrets, private_path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "credential assignment": re.compile(
        r'''(?im)^\s*["']?(?:[\w-]*(?:password|passwd|secret|token|api_key|apikey|encryption_key))'''
        r'''["']?\s*[:=]\s*["']?([A-Za-z0-9_+/=-]{16,})'''
    ),
    "credential URL": re.compile(r"[a-z][a-z0-9+.-]*://[^\s/:]+:[^\s/@]+@", re.I),
    "service token": re.compile(
        r"\b(?:ASIA[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{16,}|"
        r"AIza[A-Za-z0-9_-]{35}|glpat-[A-Za-z0-9_-]{20,}|"
        r"eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,})\b"
    ),
    "private key": re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    "database dump": re.compile(r"(?im)^(?:-- PostgreSQL database dump|COPY public\.|INSERT INTO)"),
    "personal local path": re.compile(
        r"(?i)(?:C:\\Users\\(?!Public\b)[^\\\s]+|/home/(?!node\b)[a-z0-9_.-]+)"
    ),
}
PRIVATE_PARTS = {
    ".git", ".aws", ".ssh", ".n8n", ".venv", "venv", "node_modules", "__pycache__",
    "data", "volumes", "backups", "dumps", "secrets", "credentials", "workflows",
    "workflow-exports", "test-results", "playwright-report", "dist", ".codex", ".agents",
}


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, check=True,
    ).stdout


def main() -> int:
    names = [name for name in git("ls-files", "--cached", "-z").decode().split("\0") if name]
    if not names:
        print("FAIL: no staged files")
        return 1
    secrets = local_secrets()
    failures = []
    for name in names:
        path = Path(name)
        if (
            private_path(path) or set(path.parts) & PRIVATE_PARTS
            or path.suffix.lower() in {".sql", ".dump", ".backup", ".db", ".sqlite", ".sqlite3"}
            or (path.suffix == ".json" and any(x in path.name.lower() for x in ("workflow", "credential")))
        ):
            failures.append((name, "private/data/generated path"))
        blob = git("show", f":{name}")
        try:
            content = blob.decode("utf-8")
            if "\0" in content:
                raise UnicodeError
        except UnicodeError:
            failures.append((name, "binary content requires manual review"))
            continue
        if findings(content, secrets):
            failures.append((name, "known local credential or token"))
        for rule, pattern in RULES.items():
            for match in pattern.finditer(content):
                if rule == "credential assignment" and match.group(1).startswith("replace-"):
                    continue
                failures.append((name, rule))
    for name, rule in sorted(set(failures)):
        print(f"REVIEW: {name} ({rule})")
    print(f"Staged audit: {len(names)} files; {len(set(failures))} findings.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
