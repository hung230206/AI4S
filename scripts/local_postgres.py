"""Optional Windows PostgreSQL binary fallback; isolated cluster, no existing service changes."""
import os
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
local = root / ".local"
local.mkdir(exist_ok=True)
bin_dir = next((Path(f"C:/Program Files/PostgreSQL/{v}/bin") for v in (18, 17, 16) if Path(f"C:/Program Files/PostgreSQL/{v}/bin/pg_ctl.exe").exists()), None)
if not bin_dir:
    raise SystemExit("Install PostgreSQL 16+ or use docker compose up -d db")
data = local / "pgdata"
flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def run(name, *args, check=True):
    return subprocess.run([str(bin_dir / f"{name}.exe"), *map(str, args)], check=check, **flags)


if not data.exists():
    pwfile = local / "init-password"
    pwfile.write_text("fintech_demo_local_only", encoding="utf-8")
    try:
        run("initdb", "-D", data, "-U", "fintech_demo", "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--pwfile", pwfile, "--encoding=UTF8", "--locale=C")
    finally:
        pwfile.unlink(missing_ok=True)
if run("pg_ctl", "-D", data, "status", check=False).returncode:
    run("pg_ctl", "-D", data, "-l", local / "postgres.log", "-o", "-h 127.0.0.1 -p 5434", "start")
os.environ["PGPASSWORD"] = "fintech_demo_local_only"
for name in ("insurance_payment_demo", "insurance_payment_test"):
    result = subprocess.run([str(bin_dir / "psql.exe"), "-h", "127.0.0.1", "-p", "5434", "-U", "fintech_demo", "-d", "postgres", "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{name}'"], capture_output=True, text=True, check=True, **flags)
    if result.stdout.strip() != "1":
        run("createdb", "-h", "127.0.0.1", "-p", "5434", "-U", "fintech_demo", name)
print("Isolated local PostgreSQL ready on 127.0.0.1:5434")
