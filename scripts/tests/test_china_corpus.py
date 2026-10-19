"""Offline ingestion-boundary checks; no external requests or database writes."""
import asyncio
import importlib.util
import json
from pathlib import Path
import sys

import httpx
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "china_rag_corpus.py"
spec = importlib.util.spec_from_file_location("china_corpus", SCRIPT)
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)


@pytest.mark.parametrize("url", ["http://www.iachina.cn/x", "https://www.iachina.cn.evil.test/x", "https://www.iachina.cn@evil.test/x", "https://name:password@www.iachina.cn/x", "https://www.nhsa.gov.cn:8443/x", "https://www.example.com/x"])
def test_only_exact_official_chinese_https_hosts(url):
    with pytest.raises(ValueError): corpus.allowed_url(url)


def test_nhsa_article_excludes_menu_scripts_and_public_footer():
    body = "基本医疗保险与商业保险不能混同。" * 10
    raw = f'<nav>menu</nav><div id="zoom">{body}<script>not article</script><p>中国医保，一生守护！public footer</p></div>'.encode()
    extracted = corpus.html_text(raw, "nhsa-html")
    assert body in extracted and "menu" not in extracted and "not article" not in extracted and "public footer" not in extracted


def test_iac_uses_metadata_table_and_retains_stopped_status():
    body = "<tr><td>公司名称</td><td>中英人寿保险有限公司</td></tr>" + "".join(f"<tr><td>公开字段{i}</td><td>产品说明和版本信息</td></tr>" for i in range(6))
    raw = ('<table><tr><td>wrong navigation</td></tr></table><table class="biaoge">' + body + '<tr><td>停用日期</td><td>2024-03-12</td></tr><tr><td>客户服务电话</td><td>public service</td></tr></table>').encode()
    result = corpus.html_text(raw, "metadata")
    assert "2024-03-12" in result and "wrong navigation" not in result and "客户服务电话" not in result


def test_missing_expected_article_fails_instead_of_indexing_navigation():
    with pytest.raises(ValueError): corpus.html_text(b"<nav>only menu</nav>", "nhsa-html")


def test_indexing_labels_are_explicit_and_do_not_change_money_or_dates():
    source = "不保证续保。金额人民币2000元，日期2024-03-12。\n[来源：GB/T 36687-2018]"
    result = corpus.annotate(source)
    assert "not official translation" in result and "2000元" in result and "2024-03-12" in result
    assert "不保证续保" in result and "GB/T 36687—2018" in result


def test_product_filing_is_not_labelled_as_patient_crossprovince_registration():
    assert "khám khác tỉnh" not in corpus.annotate("保险产品审批或备案。")
    assert "đăng ký khám khác tỉnh" in corpus.annotate("跨省异地就医备案申请。")


def test_download_rejects_external_redirect_without_fetching_it(monkeypatch):
    actual_client = httpx.AsyncClient; calls = []
    def handler(request):
        calls.append(str(request.url)); return httpx.Response(302, headers={"Location": "https://example.com/private"})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: actual_client(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(ValueError): asyncio.run(corpus.download("https://www.iachina.cn/source"))
    assert calls == ["https://www.iachina.cn/source"]


def test_download_bounds_bytes_and_does_not_retry_access_denied(monkeypatch):
    actual_client = httpx.AsyncClient; calls = []; status = [200]
    monkeypatch.setattr(corpus, "MAX_BYTES", 16)
    def handler(request):
        calls.append(request); return httpx.Response(status[0], content=b"X" * 32)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: actual_client(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(ValueError): asyncio.run(corpus.download("https://www.nhsa.gov.cn/source"))
    status[0] = 403
    with pytest.raises(httpx.HTTPStatusError): asyncio.run(corpus.download("https://www.nhsa.gov.cn/source"))
    assert len(calls) == 2


def test_source_manifest_is_china_only_and_does_not_include_2017_test_catalogue():
    sources = json.loads(corpus.SOURCES.read_text(encoding="utf-8"))
    assert len(sources) == 9 and len({s["slug"] for s in sources}) == 9
    assert all(corpus.allowed_url(s["url"]) for s in sources)
    assert all("col5644" not in s["url"] and "col5643" not in s["url"] for s in sources)
    stopped = next(s for s in sources if s["slug"] == "iac-aviva-stopped-info")
    assert "STOPPED" in stopped["scope"] and "not successfully downloaded" in stopped["scope"]


def test_bad_draft_retrieval_never_reaches_publication(tmp_path, monkeypatch):
    monkeypatch.setattr(corpus, "OUTPUT", tmp_path)
    (tmp_path / "prepared").mkdir(); raw = b"fictional test document for parser acceptance"
    (tmp_path / "prepared/source.txt").write_bytes(raw)
    record = {"slug": "source", "url": "https://www.nhsa.gov.cn/source", "prepared_file": "source.txt", "prepared_sha256": corpus.sha(raw), "metadata": {"jurisdiction": "CN", "source_kind": "PUBLIC_REFERENCE", "language": "zh", "source_url": "https://www.nhsa.gov.cn/source"}, "question": "source question", "expected": ["required evidence"]}
    (tmp_path / "manifest.json").write_text(json.dumps({"sources": [record]}))
    credential = tmp_path / "credentials.json"; credential.write_text(json.dumps({"email": "fake@example.com", "password": "fictional-test-password"}))
    paths = []; actual_client = httpx.Client
    def handler(request):
        paths.append(request.url.path)
        if request.url.path.endswith("/auth/login"): payload = {"user": {"is_rag_admin": True}, "csrf_token": "fictional-csrf"}
        elif request.url.path.endswith("/auth/logout"): payload = {}
        elif request.url.path.endswith("/documents/upload"): payload = {"id": "test-source", "revision": 1}
        elif request.url.path.endswith("/admin/rag/preview"): payload = {"matches": []}
        elif request.url.path.endswith("/admin/rag/documents"): payload = {"items": [], "publication_notice": "fictional-notice"}
        else: pytest.fail("Unreviewed draft reached an unexpected endpoint")
        return httpx.Response(200, json=payload)
    monkeypatch.setattr(httpx, "Client", lambda **kw: actual_client(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(ValueError, match="remains unpublished"):
        corpus.import_sources("http://localhost:8106", credential, True, False, tmp_path / "receipt.json")
    assert not any(path.endswith("/publish") for path in paths)
