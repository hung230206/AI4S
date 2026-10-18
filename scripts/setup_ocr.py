"""Download public OCR language models once; never sends user documents anywhere."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
target = root / ".local" / "ocr-models"
target.mkdir(parents=True, exist_ok=True)
def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "BaoAn-OCR-Setup"}), timeout=90) as response:
        return response.read()
commit = "87416418657359cb625c412a48b6e1d6d41c29bd"
manifest = {"repository": "https://github.com/tesseract-ocr/tessdata_fast", "commit": commit, "license": "Apache-2.0", "files": {}}
for language in ("eng", "chi_sim", "vie"):
    path = target / f"{language}.traineddata"
    raw = fetch(f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{commit}/{path.name}")
    path.write_bytes(raw)
    manifest["files"][path.name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    print(f"Downloaded {language}: {len(raw)} bytes")
(target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("Local OCR models ready; runtime OCR uses no external service.")
