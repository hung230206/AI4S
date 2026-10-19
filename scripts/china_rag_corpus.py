"""Prepare reviewed Chinese public sources and import through authenticated RAG APIs.

Raw copyrighted originals stay in ignored output/. No CAPTCHA/login is automated.
Publication requires an authorized operator's explicit --publish choice.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app import gemini
from app.rag import Metadata

SOURCES = ROOT / "scripts/china_rag_sources.json"
OUTPUT = ROOT / "output/China_RAG_Corpus"
HOSTS = {"www.iachina.cn", "www.nfra.gov.cn", "www.nhsa.gov.cn"}
MAX_BYTES = 5 * 1024 * 1024
# Indexing labels only: never represented as official Vietnamese translations.
HINTS = [
    (r"健康保险", "bảo hiểm sức khỏe health insurance"),
    (r"主要包括|本办法所称健康保险", "phân loại các loại types"),
    (r"续保", "tái tục bảo đảm gia hạn renewal"),
    (r"不保证续保", "không bảo đảm tái tục non guaranteed renewal"),
    (r"短期", "ngắn hạn short term"),
    (r"等待期", "thời gian chờ waiting period"),
    (r"理赔|索赔", "bồi thường hồ sơ chi trả claims service"),
    (r"原则|以客户为中心|依法合规|诚实守信|高效服务", "nguyên tắc dịch vụ khách hàng tuân thủ principles"),
    (r"基本医疗保险|基本医保", "bảo hiểm y tế công cơ bản social basic medical insurance"),
    (r"商业保险|商保|学生平安险", "bảo hiểm thương mại học sinh thay thế commercial student insurance"),
    (r"异地|跨省", "khám khác tỉnh cross province"),
    (r"就医地.*(?:支付范围|目录)|参保地.*(?:政策|起付)|就医地目录", "thanh toán danh mục chính sách nơi khám nơi tham gia settlement catalogue policy"),
    (r"(?:异地就医|跨省|就医).{0,12}备案|备案(?:申请|进度|记录|类型|材料)|开始备案", "đăng ký khám khác tỉnh filing registration"),
    (r"步骤|第一步|第二步|第三步|第四步", "các bước steps"),
    (r"公司名称|产品名称|编码", "công ty phát hành mã điều khoản product company wording code"),
    (r"在售|停用|停止销售", "trạng thái bán ngừng ngày ngừng bán sales stopped date snapshot"),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def allowed_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Only allowlisted Chinese official HTTPS sources are accepted")
    return url


async def download(url):
    allowed_url(url)
    async def fetch():
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            target = url
            for _ in range(5):
                async with client.stream("GET", target) as response:
                    if response.is_redirect:
                        target = allowed_url(str(response.url.join(response.headers["location"]))); continue
                    response.raise_for_status()
                    raw = bytearray()
                    async for chunk in response.aiter_bytes():
                        raw.extend(chunk)
                        if len(raw) > MAX_BYTES: raise ValueError("Source exceeds 5 MB")
                    return bytes(raw)
            raise ValueError("Too many source redirects")
    return await asyncio.wait_for(fetch(), timeout=35)


def html_text(raw, kind):
    if kind == "nfra-json":
        data = json.loads(raw)["data"]
        soup = BeautifulSoup(data["docClob"], "html.parser")
        area = soup
    else:
        soup = BeautifulSoup(raw, "html.parser")
        area = soup.select_one("#zoom") if kind == "nhsa-html" else soup.select_one("table.biaoge")
        if area is None: raise ValueError("Expected article/metadata region missing; source needs review")
    for node in area.find_all(["script", "style", "nav", "footer", "iframe", "noscript"]): node.decompose()
    if kind == "metadata":
        lines = [row.get_text(" ", strip=True) for row in area.find_all("tr")]
        lines = [line for line in lines if "客户服务电话" not in line]
    else:
        lines = area.get_text("\n", strip=True).splitlines()
    cleaned = []
    for line in lines:
        line = re.sub(r"[ \t\u3000]+", " ", line).strip()
        if "中国医保，一生守护" in line or "打击欺诈骗保举报电话" in line: break
        if not line or line in {"打印", "关闭", "〖打印〗", "〖关闭〗"}: continue
        if cleaned and line == cleaned[-1]: continue
        cleaned.append(line)
    if len("".join(cleaned)) < 80: raise ValueError("Extracted article is unexpectedly short")
    return "\n".join(cleaned)


def annotate(text):
    # GB/T 36687-2018 is a public standard reference, not a personal number.
    # Preserve its digits with a typographic dash; the untouched PDF is retained.
    text = text.replace("36687-2018", "36687—2018")
    text = re.sub(r"[\ue000-\uf8ff]", "", text)
    result = []
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph: continue
        labels = [label for pattern, label in HINTS if re.search(pattern, paragraph)]
        if labels: result.append("[Demo indexing hints only, not official translation: " + "; ".join(labels[:4]) + "]")
        result.append(paragraph)
    return "\n".join(result)


def prepare(cache):
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    for folder in (OUTPUT / "raw", OUTPUT / "prepared"): folder.mkdir(parents=True, exist_ok=True)
    records = []
    for source in sources:
        for key in ("url", "download"):
            if source.get(key): allowed_url(source[key])
        original = cache / source["cache"]
        raw = original.read_bytes() if original.exists() else asyncio.run(download(source.get("download", source["url"])))
        if not raw or len(raw) > MAX_BYTES: raise ValueError("Source file is empty/too large")
        (OUTPUT / "raw" / source["cache"]).write_bytes(raw)
        if source["format"].startswith("pdf"):
            if not raw.startswith(b"%PDF-"): raise ValueError("Expected PDF signature")
            reader = PdfReader(__import__("io").BytesIO(raw))
            if reader.is_encrypted: raise ValueError("Encrypted source requires manual review")
            pages = [{"page": i + 1, "text": page.extract_text() or ""} for i, page in enumerate(reader.pages)]
            if any(len(page["text"].strip()) < 20 for page in pages): raise ValueError("Unreadable PDF page; do not silently omit it")
        else:
            pages = [{"page": 1, "text": html_text(raw, source["format"])}]
        source_chars = sum(len(p["text"]) for p in pages)
        if source_chars > 200000: raise ValueError("Corpus source exceeds this importer limit")
        if source["format"] == "pdf":
            if len(pages) > 50: raise ValueError("PDF exceeds app's 50-page limit")
            upload = raw; filename = source["slug"] + ".pdf"; processing = "Original PDF, unchanged; physical page citations include the cover"
        else:
            header = ("CHINESE PUBLIC REFERENCE / BẢN TRÍCH XUẤT THAM KHẢO\n" + source["title"] + "\nSource: " + source["url"] +
                "\nSource date/snapshot: " + source["date"] + "\nScope: " + source["scope"] +
                "\nDemo VI/EN indexing hints are editorial labels, NOT an official translation. Base factual answers on the Chinese source text.\n\n")
            content = header + "\n\n".join("[Original source physical page " + str(p["page"]) + "]\n" + annotate(p["text"]) for p in pages)
            upload = content.encode("utf-8"); filename = source["slug"] + ".txt"
            processing = "Processed source transcript; original physical-page markers and labelled VI/EN indexing hints; no official translation. Public contact footer removed; GB/T standard-reference hyphen typography normalized."
        license_note = ("Copyright retained by the publisher; public disclosure for restricted educational reference, not an open licence or insurer verification. " + processing +
            " Source date: " + source["date"] + ". Original SHA256: " + sha(raw))
        meta = Metadata(title=source["title"], publisher=source["publisher"], source_url=source["url"], source_kind="PUBLIC_REFERENCE", license_note=license_note, category=source["category"], language="zh", jurisdiction="CN")
        tested_pages = pages if source["format"] == "pdf" else [{"page": 1, "text": upload.decode("utf-8")}]
        gemini.ensure_non_sensitive({"metadata": meta.model_dump(mode="json"), "pages": tested_pages})
        (OUTPUT / "prepared" / filename).write_bytes(upload)
        records.append({**source, "metadata": meta.model_dump(mode="json"), "prepared_file": filename, "raw_sha256": sha(raw), "prepared_sha256": sha(upload),
            "source_pages": len(pages), "source_characters": source_chars, "upload_bytes": len(upload), "processing": processing})
    manifest = {"prepared_at": datetime.now(timezone.utc).isoformat(), "scope": "China only; approved official hosts only", "originals_excluded_from_git_and_team_zip": True,
                "review": "Extraction/source review by coding agent; not legal, insurer authenticity or current-sale certification", "sources": records}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PREPARED: {len(records)} Chinese source documents; originals and ready-to-upload files in output/China_RAG_Corpus")


def import_sources(url, credentials_path, publish, retire_fixtures, evidence):
    if not publish: raise ValueError("Pass --publish only for an authorized, reviewed publication run")
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    credentials = json.loads(credentials_path.read_text(encoding="utf-8"))
    result = {"at": datetime.now(timezone.utc).isoformat(), "origin": url, "items": [], "fixture_sources_unpublished": [], "actual_model_calls": 0}
    def checked(response, status=200):
        if response.status_code != status: raise RuntimeError(f"Corpus API returned {response.status_code}, expected {status}")
        return response.json()
    with httpx.Client(base_url=url.rstrip("/") + "/api/v1", headers={"Origin": url.rstrip("/")}, timeout=60) as client:
        account = checked(client.post("/auth/login", json={"email": credentials["email"], "password": credentials["password"]}))
        if not account["user"]["is_rag_admin"]: raise RuntimeError("Administrator capability required")
        client.headers["X-CSRF-Token"] = account["csrf_token"]
        try:
            listing = checked(client.get("/admin/rag/documents")); notice = listing["publication_notice"]
            for record in manifest["sources"]:
                raw = (OUTPUT / "prepared" / record["prepared_file"]).read_bytes()
                if sha(raw) != record["prepared_sha256"]: raise ValueError("Prepared file changed after review")
                allowed_url(record["url"]); allowed_url(record["metadata"]["source_url"])
                if record["metadata"]["jurisdiction"] != "CN" or record["metadata"]["source_kind"] != "PUBLIC_REFERENCE" or record["metadata"]["language"] != "zh":
                    raise ValueError("Only Chinese-language public China reference records are accepted")
                duplicates = [doc for doc in listing["items"] if doc["source_url"] == record["url"]]
                if duplicates:
                    doc = next((doc for doc in duplicates if doc["sha256"] == sha(raw)), None)
                    if doc is None: raise ValueError("Existing source differs; review its revision in admin before updating")
                    operation = "EXISTING_UNCHANGED"
                    if not doc["published"] or doc["deleted"]: raise ValueError("Existing source is withdrawn; automatic republication refused")
                else:
                    doc = checked(client.post("/admin/rag/documents/upload", headers={"X-Processing-Consent": "rag-corpus:files-2026-10-19-v1"},
                        data={"metadata": json.dumps(record["metadata"], ensure_ascii=False)}, files={"file": (record["prepared_file"], raw, "application/pdf" if record["prepared_file"].endswith(".pdf") else "text/plain")}))
                    preview = checked(client.post("/admin/rag/preview", json={"document_id": doc["id"], "question": record["question"], "language": "vi"}))
                    draft_excerpts = "\n".join(item["excerpt"] for item in preview["matches"])
                    if not all(term in draft_excerpts for term in record["expected"]):
                        raise ValueError("Draft retrieval failed review; source remains unpublished: " + record["slug"])
                    doc = checked(client.post(f"/admin/rag/documents/{doc['id']}/publish", json={"revision": doc["revision"], "notice_version": notice, "publication_confirmed": True}))
                    operation = "CREATED_AND_PUBLISHED"
                answer = checked(client.post("/rag/ask", json={"document_id": doc["id"], "question": record["question"], "language": "vi"}))
                if not answer["citations"]: raise ValueError("Reviewed source did not answer its retrieval smoke question: " + record["slug"])
                excerpts = "\n".join(item["excerpt"] for item in answer["citations"])
                if not all(term in excerpts for term in record["expected"]): raise ValueError("Retrieved evidence needs review: " + record["slug"])
                public = checked(client.get(f"/rag/documents/{doc['id']}?revision={doc['revision']}"))
                for citation in answer["citations"]:
                    if citation["excerpt"] != public["pages"][citation["page"] - 1]["text"][citation["start"]:citation["end"]]: raise ValueError("Citation offset mismatch")
                original = client.get(f"/rag/documents/{doc['id']}/download?revision={doc['revision']}")
                if original.status_code != 200 or sha(original.content) != record["prepared_sha256"]: raise ValueError("Published download hash mismatch")
                result["items"].append({"slug": record["slug"], "document_id": doc["id"], "revision": doc["revision"], "operation": operation, "source_url": record["url"],
                    "source_pages": record["source_pages"], "published_pages": public["page_count"], "sha256": doc["sha256"], "retrieval": "PASS", "citation_offsets": "PASS", "download_hash": "PASS"})
            if retire_fixtures:
                for doc in listing["items"]:
                    if doc["source_kind"] == "TEST_FIXTURE" and doc["published"] and not doc["deleted"]:
                        checked(client.post(f"/admin/rag/documents/{doc['id']}/unpublish", json={"revision": doc["revision"]}))
                        result["fixture_sources_unpublished"].append(doc["id"])
            result["status"] = "PASS"
        except Exception as error:
            result.update(status="FAIL", failure=str(error)[:200]); raise
        finally:
            client.post("/auth/logout", json={})
            evidence.parent.mkdir(parents=True, exist_ok=True)
            evidence.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(result['items'])} official China sources published and source/citation/hash checked")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare"); prep.add_argument("--cache", type=Path, default=OUTPUT / "raw")
    imp = commands.add_parser("import"); imp.add_argument("--url", required=True); imp.add_argument("--credentials", type=Path, required=True)
    imp.add_argument("--publish", action="store_true"); imp.add_argument("--retire-fixtures", action="store_true"); imp.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare": prepare(args.cache)
    else: import_sources(args.url, args.credentials, args.publish, args.retire_fixtures, args.evidence)


if __name__ == "__main__": main()
