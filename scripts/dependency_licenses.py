"""Export installed package license metadata without copying third-party source."""
import importlib.metadata as metadata
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
python = []
for dist in metadata.distributions():
    if dist.metadata["Name"] == "insurance-payment-demo":
        continue
    classifiers = [c.replace("License :: ", "") for c in dist.metadata.get_all("Classifier", []) if c.startswith("License ::")]
    value = dist.metadata.get("License-Expression") or dist.metadata.get("License") or "; ".join(classifiers) or "See installed distribution license files"
    python.append({"name": dist.metadata["Name"], "version": dist.version, "license": value[:300]})
lock = json.loads((root / "frontend/package-lock.json").read_text())
npm = [{"package": name, "version": item.get("version"), "license": item.get("license", "See distribution license"), "dev": item.get("dev", False)} for name, item in lock["packages"].items() if name]
output = root / "submission/evidence/dependency-licenses.json"
output.write_text(json.dumps({"python": python, "npm": npm}, indent=2), encoding="utf-8")
print(f"Exported license metadata: {len(python)} Python distributions, {len(npm)} npm package entries.")
