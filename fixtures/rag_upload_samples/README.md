# Upload samples for the administrator RAG workflow

These are UTF-8 copies of the three CC0, team-authored fictional sources in `../rag_demo_corpus.json`. They contain no real policyholder records and are not authentic insurance contracts. The existing seeded library already contains their content; upload a copy with a distinct title to test the complete administrator workflow. Do not upload this README as policy evidence.

| File | Suggested title | Category | Language | Jurisdiction |
|---|---|---|---|---|
| student-policy-sample-en.txt | Upload test — fictional student policy | POLICY | en | CN |
| claims-guide-sample-vi.md | Upload test — hồ sơ bồi thường mẫu | CLAIMS | vi | CN |
| insurance-glossary-sample-zh.txt | Upload test — 保险术语 | GLOSSARY | zh | WORLD |

For each file, set publisher to **Demo team (self-authored)**, source kind to **TEST_FIXTURE**, and usage rights to **CC0 — team-authored fictional material for software tests; not an insurer policy**. A public-reference URL is not required for these fictional fixtures. Review extracted text and the publication notice before publishing.

1. Sign in at https://ai4s-demo.onrender.com/admin/rag using the privately handed-over test account.
2. Create a document, enter the metadata above, select the matching file and agree to that file's processing notice. Save the draft.
3. Preview retrieval locally, review the source, then publish using the separate publication notice.
4. At https://ai4s-demo.onrender.com/knowledge, select the uploaded source and ask one of the questions below. Check the page/revision citation and original download.
5. Edit metadata or replace the file: it becomes a draft. Republish after review; the old citation link must report that the source changed.
6. Move the test copy to trash. It disappears from student retrieval; restoring it returns a draft.

Questions with expected source facts:

- English policy: **What is the annual outpatient limit?** → fictional CNY 2,000; deductible CNY 100 per visit.
- English policy: **What is the maternity benefit limit?** → insufficient information; this source does not state that benefit.
- Vietnamese guide: **Hồ sơ bồi thường cần giấy tờ gì?** → sample claim form, hospital invoice and relevant medical records; no insurer submission is performed.
- Chinese glossary: **免赔额是什么意思？** → the portion of eligible costs that may need to be borne personally; check actual policy conditions.

Use **original excerpts at the server** for the verified path. The real Gemini generation check timed out in this release; the application labels its extractive fallback rather than representing it as a generated answer. See `../../RAG_GUIDE.md` and `../../IMPLEMENTATION_REPORT.md`.
