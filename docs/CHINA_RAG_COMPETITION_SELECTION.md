# Current China references selected for the competition

Reviewed on 19 October 2026. The user's requested competition snapshot contains **8 active sources: 3 IAC, 2 NFRA and 3 NHSA**. No long-term legal-status monitoring system was added.

## Selection decisions

| Source | Decision and evidence |
|---|---|
| PICC Health 2024 wording and its metadata (2 records) | Retained. [Matching IAC disclosure](https://www.iachina.cn/IC/tkk/02/e40f8000-6ece-4e33-aa8f-4acaa88d6233.html) displays 在售. Applies to the matching product/version; not an issued personal policy. |
| T/IAC 53-2024 claims service standard | Retained. [IAC's issued text](https://www.iachina.cn/module/download/downfile.jsp?classid=0&filename=253ba2d6743c4fe8a5aa5ca651b88bbf.pdf) states effective 19 February 2025; no replacement found in the review. It is an industry standard, not a law. |
| Health Insurance Administrative Measures 2019 | Retained. [Beijing's official policy page](https://jrj.beijing.gov.cn/2024zcwj/gjzcfg2024/202409/t20240906_3792019.html) labels it 现行有效. Its 2006 predecessor was repealed, not this version. |
| Individual short-term health insurance notice 2021 | Retained. [MOFCOM's legal registry](https://policy.mofcom.gov.cn/claw/clawContent.shtml?id=87884) labels it 现行有效; [NFRA publishes the original](https://www.nfra.gov.cn/cn/view/pages/ItemDetail.html?docId=958198). |
| Cross-province direct settlement notice 2022 | Retained. [Xinjiang's September 2026 policy explanation](https://ylbzj.xinjiang.gov.cn/ylbzj/zcj/202609/579c4492a36e48578ae2c745fb38a555.shtml) still cites it alongside the supplementary 2024 notice. The national framework and current local implementation must be read together. |
| NHSA student insurance distinction and filing guide 2025 (2 records) | Retained as official explanatory guidance, not legislation or a universal current benefit schedule. [Student article](https://www.nhsa.gov.cn/art/2025/1/26/art_52_15573.html), [filing guide](https://www.nhsa.gov.cn/art/2025/6/7/art_14_16754.html). |
| 中英人寿爱心保 metadata | **Excluded.** [IAC disclosure](https://www.iachina.cn/IC/tkk/02/01ad48f5-003b-49f0-b062-562cc4c400b6.html) explicitly says 停用 since 12 March 2024. Unpublished from local and Render libraries, omitted from active upload files and package. |

The retained set contains no source identified as repealed or a stopped product in this review. A dated review is not a legal certification: sale status, regulatory effectiveness and guidance currency are different evidence types. Product terms depend on the issued contract. NHSA articles do not establish an international student's eligibility or guarantee a reimbursement amount.

## Applied changes and checks

- Removed the stopped source from scripts/china_rag_sources.json; decisions and primary URLs are recorded in scripts/china_rag_competition_review.json.
- The authenticated importer unpublishes only the exact excluded public-reference URL. It preserves the administrative draft/audit history and refuses stale prepared manifests containing that URL. Current references and private records are not rewritten.
- Real local and Render checks confirm exactly 8 selected public sources. The withdrawn source returns 404 for public detail, download and scoped retrieval; unscoped retrieval no longer cites it.
- All 8 retained documents pass real retrieval, citation offset and download hash checks. 17 offline importer tests pass. This change makes zero Gemini calls; it does not claim the separate provider quota issue is resolved.
- Raw/prepared files, CSV and local corpus ZIP contain only the 8 selected active sources. The excluded file is preserved separately under ignored output/China_RAG_Archive for audit, outside the upload package.

Evidence: submission/evidence/china-rag-current-render-import.json, china-rag-current-local-import.json, china-rag-current-render-check.json, china-rag-current-local-check.json, china-rag-current-selection-tests.xml. Earlier nine-source evidence records the historical snapshot and must not be used as the current count.

Reproduction from the repository root: PowerShell uses backend/.venv/Scripts/python.exe; Unix uses backend/.venv/bin/python. Run that interpreter with `scripts/china_rag_corpus.py prepare --cache output/China_RAG_Corpus/raw`, then `scripts/china_rag_corpus.py import --url <origin> --credentials .local/rag-admin-test.json --publish --retire-fixtures --evidence <receipt.json>`. The original files remain excluded from GitHub. Database publication changes are already applied and do not require a Render application redeploy.
