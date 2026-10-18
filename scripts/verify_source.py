"""Check deliverable source/evidence for accidental local-secret copies."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
excluded = {"node_modules", ".venv", ".next", ".local", ".git", "__pycache__", ".pytest_cache", "test-results", "playwright-report", "private"}
suffixes = {".py", ".ts", ".tsx", ".json", ".md", ".yaml", ".yml", ".txt", ".css", ".mjs", ".xml"}
secrets = []
if (root / ".env").exists():
    for line in (root / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith(("APP_SESSION_SECRET=", "MOCK_WEBHOOK_SECRET=", "DEMO_OPERATOR_CODE=", "GEMINI_API_KEY=")):
            value = line.split("=", 1)[1]
            if value:
                secrets.append(value)
count = 0
for path in root.rglob("*"):
    if excluded.intersection(path.relative_to(root).parts) or path.name.startswith(".env") or path.suffix not in suffixes or not path.is_file():
        continue
    value = path.read_text(encoding="utf-8-sig", errors="replace")
    assert all(secret not in value for secret in secrets), f"Local secret found in {path.relative_to(root)}"
    count += 1
print(f"Source/evidence scan passed: {count} text files; no copies of local session/webhook/operator/Gemini secrets.")
