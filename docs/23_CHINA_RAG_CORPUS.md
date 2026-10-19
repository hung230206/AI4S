# China-only public RAG corpus — 19 October 2026

The competition snapshot now has 8 active sources. The stopped-product metadata was withdrawn from local/Render public retrieval and the upload package. See [current-source review](CHINA_RAG_COMPETITION_SELECTION.md) for dated decisions and primary evidence; earlier nine-source test receipts are historical.

## Selection and provenance

The user requested Chinese sources, prioritising the Insurance Association of China (IAC), National Financial Regulatory Administration (NFRA) and National Healthcare Security Administration (NHSA). Eight selected current source records were downloaded, prepared and published through authenticated administrator APIs on local and Render databases. All eight are PUBLIC_REFERENCE, language zh, jurisdiction CN. Three are IAC disclosures/standard, two NFRA regulatory texts and three NHSA social-insurance guides/rules. There are two original PDFs with 52 physical pages and six HTML/JSON source objects; 78,457 Unicode characters were extracted before editorial index labels. These counts describe this curated snapshot, not the size of the publishers' complete catalogues.

| Source ID | Content | Date/snapshot qualification | Primary source |
|---|---|---|---|
| iac-picc-terms-2024 | [IAC · 2024] PICC Health 健康金福 — điều khoản y tế | Product wording code 人保健康[2024]医疗保险008号; no publication day asserted | [Original](https://www.iachina.cn/IC/tkk/01/e40f8000-6ece-4e33-aa8f-4acaa88d6233.html) |
| iac-picc-product-info | [IAC · Snapshot] PICC 健康金福 — công ty, mã và trạng thái công bố | Undated disclosure page; retrieved snapshot only | [Original](https://www.iachina.cn/IC/tkk/02/e40f8000-6ece-4e33-aa8f-4acaa88d6233.html) |
| iac-claims-standard-2024 | [IAC · T/IAC 53-2024] Quy chuẩn dịch vụ bồi thường | Published 2024-11-19; effective 2025-02-19 | [Original](https://www.iachina.cn/module/download/downfile.jsp?classid=0&filename=253ba2d6743c4fe8a5aa5ca651b88bbf.pdf) |
| nfra-health-measures-2019 | [NFRA · 2019] Quy định quản lý bảo hiểm sức khỏe | Published 2019-11-12; stated effective 2019-12-01 | [Original](https://www.nfra.gov.cn/cn/view/pages/rulesDetail.html?docId=1027050) |
| nfra-shortterm-notice-2021 | [NFRA · 2021] Bảo hiểm ngắn hạn và không bảo đảm tái tục | 2021-01-11; 银保监办发〔2021〕7号 | [Original](https://www.nfra.gov.cn/cn/view/pages/ItemDetail.html?docId=958198) |
| nhsa-student-insurance-2025 | [NHSA · 2025] Bảo hiểm học sinh thương mại và医保 cơ bản | 2025-01-26 | [Original](https://www.nhsa.gov.cn/art/2025/1/26/art_52_15573.html) |
| nhsa-crossprovince-rules-2022 | [NHSA · 2022] Quy tắc thanh toán BHYT công khác tỉnh | Published 2022-07-26; procedure effective 2023-01-01; 医保发〔2022〕22号 | [Original](https://www.nhsa.gov.cn/art/2022/7/26/art_104_8629.html) |
| nhsa-crossprovince-guide-2025 | [NHSA · 2025] Hướng dẫn đăng ký khám khác tỉnh | 2025-06-07 | [Original](https://www.nhsa.gov.cn/art/2025/6/7/art_14_16754.html) |

The PICC PDF cover was visually checked against its IAC metadata: issuer/product and wording code 人保健康[2024]医疗保险008号 match. Its 36 physical pages include the cover. This is public product wording, not an issued policy for an account holder. The Aviva/中英 disclosure explicitly states stopped on 2024-03-12; its metadata is now excluded from the active competition corpus. Its linked wording PDF did not complete download, so no contents or benefits are attributed to it. In-sale text on the other metadata page is a fetched disclosure snapshot, not independently verified real-time availability.

The IAC dynamic search portal has a CAPTCHA. No CAPTCHA was solved or bypassed. Independently published, publicly indexed static IAC disclosure pages and their linked product PDF were accessible without that portal and used as primary references. The 2017 test/archive catalogue pages investigated earlier were excluded in favour of the actual 2024 product disclosure. The user-linked NHSA 2020 handbook was reviewed as a lead, but newer 2025 explanatory pages and their 2022 normative basis were selected instead. NFRA's publicly used static JSON endpoints supply the same document IDs/content as the linked official pages; their scripts were inspected as text, never executed.

## Processing method

1. A fixed eight-source manifest limits acquisition to exact official Chinese HTTPS hosts. Redirects are checked, downloads have a complete-attempt deadline and a 5 MB size cap. Access-denied responses are not retried through protected paths. Raw bytes and SHA-256 are preserved under ignored output/China_RAG_Corpus/raw.
2. Text extraction uses local pypdf. PICC's original PDF is uploaded unchanged, preserving physical page citations. The IAC standard is a processed transcript with original physical-page markers; its GB/T standard-reference hyphen is typographically normalised to avoid the existing conservative number tripwire, without changing digits. Original PDF bytes remain available locally. Representative cover/body pages of both PDFs were rendered and visually checked with PDFium. This is extraction review, not complete legal/insurer certification of every clause or table.
3. NHSA article content comes from #zoom and IAC metadata from table.biaoge; menus, scripts and the irrelevant public-contact footer are excluded. NFRA regulatory HTML comes from docClob. Adjacent duplicate text nodes are removed; amounts/dates and Chinese substantive text are preserved.
4. Clearly marked VI/EN indexing labels support Vietnamese queries over Chinese paragraphs. They are editorial search aids, not official translations or insurer statements. Generic labels were narrowed after a retrieval check, including separating insurance-product filing from patient cross-province registration. Original source dates and scope warnings are retained. No model is called during download, preparation or indexing.
5. Publication uses the existing real administrator session, CSRF, per-file acknowledgement and publication notice. Prepared hashes are checked. The importer previews a new draft and refuses publication if its expected evidence is absent; existing withdrawn sources are never resurrected automatically. A different existing hash requires separate revision review, not blind replacement. Current published sources were then verified by actual retrieval, exact source character offsets and download hashes; an unchanged rerun is idempotent.
6. Three seeded fictional sources were unpublished, not deleted, in both target databases. They remain administrator drafts and in the source fixture files. Startup seed does not republish them. Only the eight selected China references are now active. Private policies, finance/claim records and other accounts were not copied, cleared or changed.

## Domain boundaries and data rights

Commercial product wording, product metadata, industry service standards, regulatory requirements and basic public social insurance are different evidence types. A metadata record cannot establish a benefit amount. A stopped product is not a current offer. NHSA public insurance instructions cannot establish international-student eligibility or a commercial policy claim. Cross-province direct settlement is domestic Chinese social-insurance administration, not international money transfer. Dates on older rules are explicit; this snapshot is not an exhaustive legal-currentness audit.

Original publisher rights are retained; no open licence, endorsement or insurer verification is asserted. Originals/prepared full texts are kept out of GitHub and the public source handoff ZIP. The separate local corpus package provides traceable source links and hashes for the user's authorised demonstration. Operators must review permitted reuse before broader redistribution. The raw/processed source hashes, extraction statistics and scope notes are recorded in submission/evidence/china-rag-source-registry.json.

The model is not trained or fine-tuned. Published passages are retrieved locally with the existing BM25 index; at most three excerpts are sent to Gemini after current session consent. Original files are not sent to the model. The public-only free-provider boundary, no executable model tools, no payment actions and post-generation consent/source revalidation remain.

## Actual validation and limits

- 15 offline ingestion-boundary checks pass: exact-host/protocol filtering, redirect rejection, byte cap, access denial, correct article/metadata selection, explicit labels, preserved figures/dates, filing terminology and refusal to publish an unsupported draft. Initial fixture/minimum-length failure was corrected and retained in the initial report.
- All 8 selected sources pass actual local and Render retrieval, exact citation-offset and published-download SHA-256 checks. Final idempotent reruns keep existing IDs/revisions. Receipts: china-rag-local-import.json and china-rag-render-import.json. The first successful Render receipt records the three fixture withdrawals.
- Three actual local Gemini 3.5 answers were manually reviewed: non-guaranteed short-term renewal; public/social versus commercial insurance without inferring foreign-student eligibility; and refusal to infer a VND payout from product metadata. Unscoped retrieval finds the short-term rule; an unrelated Bitcoin question abstains. A separate actual local browser question, binary consent, generated answer, source citation and permission withdrawal passed without model-response mocks. Evidence: china-rag-local-answers.json and china-rag-real-browser.json; screenshot screenshots/rag/china-rag-real.png.
- At the current online check, Render's explicit primary model remains gemini-3.8-flash and returned PROVIDER_RATE_LIMIT. No quota retry is performed. The operator was asked to set GEMINI_MODEL=gemini-3.5-flash-lite. Live model verification is recorded separately; successful local checks are not represented as successful online LLM checks.

The previous 24-question fictional regression scores do not measure this new production corpus. Eight curated smoke questions and three reviewed answers are not independent accuracy/generalisation evidence. Lexical retrieval, OCR/text layout, multilingual paraphrases, legal currency, changing source availability and provider quotas remain limitations. Full source review and the user's actual contract are still required.

## Reproduction

PowerShell from repository root:

```powershell
backend/.venv/Scripts/python.exe -m pip install -r scripts/requirements-china-corpus.txt
backend/.venv/Scripts/python.exe scripts/china_rag_corpus.py prepare --cache output/China_RAG_Corpus/raw
backend/.venv/Scripts/python.exe scripts/china_rag_corpus.py import --url https://ai4s-demo.onrender.com --credentials .local/rag-admin-test.json --publish --retire-fixtures --evidence submission/evidence/china-rag-render-import.json
backend/.venv/Scripts/python.exe -m pytest -q scripts/tests/test_china_corpus.py
```

On Unix substitute backend/.venv/bin/python. An absent cached file is downloaded from the manifest's public URL; a slow/dead publisher endpoint fails visibly. Use the complete local corpus snapshot to reproduce offline extraction without depending on a future download. Import requires the privately provisioned administrator account. Current report: IMPLEMENTATION_REPORT.md; user walkthrough: output/China_RAG_Corpus/README.md.
