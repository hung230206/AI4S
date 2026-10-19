"""Package the exact tracked, deployed consumer samples; JSON is developer-only."""
import hashlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "fixtures/china_upload_samples"
destination = ROOT / "output/Demo_Upload_China_Samples.zip"
destination.parent.mkdir(parents=True, exist_ok=True)
assert len([p for p in source.iterdir() if p.suffix in (".png", ".pdf")]) == 10
with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
    for path in sorted(source.iterdir()):
        if path.is_file(): archive.writestr(path.name, path.read_bytes())
with ZipFile(destination) as archive:
    assert archive.testzip() is None
    for name in archive.namelist():
        assert hashlib.sha256(archive.read(name)).digest() == hashlib.sha256((source / name).read_bytes()).digest()
print(f"Packaged 10 upload documents and consumer guides: {destination}")
