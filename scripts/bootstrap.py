"""Generate ignored local settings. Never overwrite an existing .env."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    print("Existing .env preserved.")
else:
    content = (root / ".env.example").read_text(encoding="utf-8")
    for placeholder in ("REPLACE_WITH_RANDOM_LOCAL_DEV_SECRET", "REPLACE_WITH_ANOTHER_RANDOM_LOCAL_DEV_SECRET", "REPLACE_WITH_OPERATOR_LOCAL_DEV_CODE"):
        content = content.replace(placeholder, secrets.token_urlsafe(32))
    target.write_text(content, encoding="utf-8")
    print("Created ignored .env with random local-only secrets. Operator code is in that file.")
