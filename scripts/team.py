"""Team setup, diagnostics, foreground startup and a secret-free source handoff."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
WIN = os.name == "nt"
PYTHON = ROOT / ("backend/.venv/Scripts/python.exe" if WIN else "backend/.venv/bin/python")
NPM = shutil.which("npm.cmd" if WIN else "npm")
FLAGS = {"creationflags": subprocess.CREATE_NO_WINDOW} if WIN else {}
IGNORED = {".venv", "node_modules", ".next", ".git", ".local", "__pycache__", ".pytest_cache", ".test-results", "test-results", "playwright-report", "coverage", "htmlcov", "private"}


def run(args, cwd=ROOT):
    print("Running " + Path(str(args[0])).name + " " + " ".join(str(x) for x in args[1:3]), flush=True)
    subprocess.run([str(x) for x in args], cwd=cwd, check=True, **FLAGS)


def reachable(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def models_ready():
    return all((ROOT / ".local/ocr-models" / (lang + ".traineddata")).is_file() for lang in ("eng", "vie", "chi_sim"))


def doctor(args):
    checks = {"Python 3.11 or newer": sys.version_info >= (3, 11), "Node.js on PATH": bool(shutil.which("node")), "npm on PATH": bool(NPM), "Local .env exists": (ROOT / ".env").is_file(), "Backend virtual environment": PYTHON.is_file(), "Frontend dependencies": (ROOT / "frontend/node_modules/next").is_dir(), "Local OCR models": models_ready(), "Upload examples": (ROOT / "fixtures/upload_catalog.json").is_file()}
    if not args.offline:
        try:
            with urlopen(args.url.rstrip("/") + "/api/v1/health", timeout=8) as response:
                health = json.load(response)
            checks["Running API and database"] = health.get("status") == "ok"
            checks["Real payments disabled"] = health.get("allow_real_payments") is False
        except Exception:
            checks["Running API and database"] = False
    for label, passed in checks.items():
        print(("PASS " if passed else "MISSING ") + label)
    return 0 if all(checks.values()) else 1


def setup(args):
    if not NPM or not shutil.which("node"):
        raise SystemExit("Install Node.js 22+ (tested host: 24) with npm, then retry.")
    run([sys.executable, ROOT / "scripts/bootstrap.py"])
    if not PYTHON.exists():
        launcher = shutil.which("py") if WIN else None
        command = [launcher, "-3.11"] if launcher else [sys.executable]
        run([*command, "-m", "venv", ROOT / "backend/.venv"])
    if not args.skip_install:
        run([PYTHON, "-m", "pip", "install", "--disable-pip-version-check", "-r", ROOT / "backend/requirements.lock.txt"])
        run([PYTHON, "-m", "pip", "install", "--disable-pip-version-check", "-e", str(ROOT / "backend") + "[dev]"])
        run([NPM, "ci"], ROOT / "frontend")
    if not reachable(5434) and args.database != "existing":
        if args.database == "docker" or (args.database == "auto" and shutil.which("docker")):
            run(["docker", "compose", "up", "-d", "db"])
            for _ in range(40):
                if reachable(5434):
                    break
                time.sleep(.5)
        elif WIN:
            run([PYTHON, ROOT / "scripts/local_postgres.py"])
        else:
            raise SystemExit("Start PostgreSQL with docker compose up -d db, or configure an existing database in .env.")
    if args.lan:
        if WIN:
            run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ROOT / "scripts/configure_lan.ps1"])
        else:
            print("LAN: configure FRONTEND_EXTRA_ORIGINS and frontend/.env.local LAN_ALLOWED_HOSTS for your actual host IP; see TEAM_HANDOFF.md.")
    run([PYTHON, "-m", "alembic", "upgrade", "head"], ROOT / "backend")
    run([PYTHON, "-m", "app.seed"], ROOT / "backend")
    if not models_ready():
        run([PYTHON, ROOT / "scripts/setup_ocr.py"])
    print("SETUP COMPLETE. Existing records and .env preserved. Run: python scripts/team.py start --lan")


def start(args):
    if not PYTHON.exists() or not NPM:
        raise SystemExit("Run python scripts/team.py setup first.")
    if reachable(args.frontend_port) or reachable(args.api_port):
        raise SystemExit("A process already uses a requested port. Reuse the running app, or stop its own terminal before starting. No existing process was stopped.")
    commands = [([str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(args.api_port)], ROOT / "backend"), ([NPM, "run", "dev:lan" if args.lan else "dev", "--", "--port", str(args.frontend_port)], ROOT / "frontend")]
    if args.production:
        commands[1] = ([shutil.which("node"), str(ROOT / "frontend/node_modules/next/dist/bin/next"), "start", "--hostname", "0.0.0.0" if args.lan else "127.0.0.1", "--port", str(args.frontend_port)], ROOT / "frontend")
    children = []
    log_handles = []
    logs = ROOT / ".local/run"
    logs.mkdir(parents=True, exist_ok=True)
    child_env = os.environ.copy()
    child_env["API_PROXY_TARGET"] = f"http://127.0.0.1:{args.api_port}"
    child_env["FRONTEND_ORIGIN"] = f"http://localhost:{args.frontend_port}"
    try:
        if args.production:
            print("Building the production frontend. Log: " + str(logs / "build.log"), flush=True)
            with (logs / "build.log").open("ab") as build_log:
                # The supported webpack builder is predictable for clean Windows extractions.
                building = subprocess.Popen([NPM, "run", "build", "--", "--webpack"], cwd=ROOT / "frontend", env=child_env, stdout=build_log, stderr=subprocess.STDOUT, **FLAGS)
                children.append(building)
                build_code = building.wait()
                if build_code:
                    raise subprocess.CalledProcessError(build_code, [NPM, "run", "build", "--", "--webpack"])
                children.remove(building)
        for (command, directory), label, port in zip(commands, ("api", "web"), (args.api_port, args.frontend_port), strict=True):
            logfile = (logs / f"{label}-{port}.log").open("ab")
            log_handles.append(logfile)
            children.append(subprocess.Popen(command, cwd=directory, env=child_env, stdout=logfile, stderr=subprocess.STDOUT, **FLAGS))
        print("Service logs: " + str(logs), flush=True)
        print(f"Demo: http://localhost:{args.frontend_port}/test-lab | Keep this terminal open. Ctrl+C stops only the processes launched here.", flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(.5)
        raise SystemExit("One service exited. Review its output above.")
    except KeyboardInterrupt:
        print("Stopping this launcher own services.")
    finally:
        for child in children:
            if child.poll() is None:
                if WIN:
                    subprocess.run(["taskkill.exe", "/PID", str(child.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **FLAGS)
                else:
                    child.terminate()
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
        for handle in log_handles:
            handle.close()


def fetch_reference(args):
    catalog = json.loads((ROOT / "fixtures/upload_catalog.json").read_text(encoding="utf-8"))
    item = next((item for item in catalog["public_sources"] if item["id"] == args.source), None)
    if not item or not item["url"].endswith(".pdf"):
        raise SystemExit("Unknown PDF source ID. Supported: bfsu-2025")
    with urlopen(Request(item["url"], headers={"User-Agent": "Demo-Reference-Download"}), timeout=40) as response:
        raw = response.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024 or not raw.startswith(b"%PDF-"):
        raise SystemExit("The publisher did not return an uploadable PDF within 5 MB. Open the original source manually.")
    folder = ROOT / ".local/public-reference"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (args.source + ".pdf")
    target.write_bytes(raw)
    (folder / (args.source + "-source.json")).write_text(json.dumps({"source": item, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "rights": "Original rights retained; downloaded for local reference testing, excluded from handoff package."}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Downloaded original public reference to " + str(target))
    print("Upload under Documents, select PUBLIC_REFERENCE, Chinese and English, and enter the publisher URL from the test lab.")


def package(args):
    roots = {"backend", "frontend", "scripts", "contracts", "database", "fixtures", "docs", "submission", "deploy", "reference"}
    extensions = {".py", ".ts", ".tsx", ".css", ".json", ".yaml", ".yml", ".md", ".txt", ".ini", ".toml", ".sql", ".png", ".jpg", ".jpeg", ".webp", ".pdf", ".docx", ".xml", ".ps1", ".sh", ".mjs", ".cjs", ".html", ".csv", ".webm", ".vtt", ".srt", ".mako"}
    selected = []
    for directory, folders, filenames in os.walk(ROOT):
        current = Path(directory)
        folders[:] = [name for name in folders if name not in IGNORED and not name.endswith(".egg-info") and (current != ROOT or name in roots)]
        for filename in filenames:
            path = current / filename
            relative = path.relative_to(ROOT)
            if not path.resolve().is_relative_to(ROOT.resolve()):
                continue
            if path.name.startswith(".env") and relative.as_posix() != ".env.example":
                continue
            if len(relative.parts) == 1:
                include = path.suffix in {".md", ".yaml"} or path.name in {".env.example", ".gitignore", ".dockerignore", ".gitattributes"}
            else:
                include = relative.parts[0] in roots and (path.suffix.lower() in extensions or path.name.endswith("Dockerfile"))
            if include:
                selected.append(path)
    secrets = []
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key in {"APP_SESSION_SECRET", "MOCK_WEBHOOK_SECRET", "DEMO_OPERATOR_CODE", "GEMINI_API_KEY", "RAG_ADMIN_PASSWORD"} and len(value.strip()) >= 16:
                secrets.append(value.strip().encode())
    records = []
    for path in sorted(selected):
        raw = path.read_bytes()
        if any(secret in raw for secret in secrets):
            raise SystemExit("Packaging stopped: a configured secret was found in " + str(path.relative_to(ROOT)))
        records.append({"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    output = ROOT / "output/Demo_Team_Handoff.zip"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for record, path in zip(records, sorted(selected), strict=True):
            archive.write(path, "Demo/" + record["path"])
        archive.writestr("Demo/HANDOFF_MANIFEST.json", json.dumps({"product": "Demo", "notice": "Source only; local secrets, accounts, database, dependencies, traces and copyrighted public reference originals excluded.", "files": records}, ensure_ascii=False, indent=2))
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise SystemExit("ZIP integrity failed")
    print(f"HANDOFF READY: {len(records)} source/evidence files, {output.stat().st_size} bytes")
    print(str(output))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("doctor", help="Check runtime/setup without printing secrets")
    check.add_argument("--url", default="http://localhost:3000")
    check.add_argument("--offline", action="store_true", help="Do not require running servers")
    install = commands.add_parser("setup", help="Install and migrate without resetting data")
    install.add_argument("--skip-install", action="store_true", help="Dependencies already installed")
    install.add_argument("--database", choices=["auto", "existing", "native", "docker"], default="auto")
    install.add_argument("--lan", action="store_true")
    launch = commands.add_parser("start", help="Run both services until Ctrl+C")
    launch.add_argument("--lan", action="store_true")
    launch.add_argument("--production", action="store_true", help="Build first and serve compiled UI; advanced operator UI stays development-only")
    launch.add_argument("--frontend-port", type=int, default=3000)
    launch.add_argument("--api-port", type=int, default=8000)
    fetch = commands.add_parser("fetch-reference", help="Download an original public PDF for local testing")
    fetch.add_argument("--source", default="bfsu-2025")
    commands.add_parser("package", help="Create a secret-free source ZIP with checksums")
    args = parser.parse_args()
    handlers = {"doctor": doctor, "setup": setup, "start": start, "fetch-reference": fetch_reference, "package": package}
    try:
        result = handlers[args.command](args)
        return result or 0
    except (subprocess.CalledProcessError, OSError) as exc:
        print("Command failed: " + type(exc).__name__ + ". Review the preceding service output; credentials were not exported.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
