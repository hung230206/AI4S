# Combined RAG generation and bounded Gemini fallback — 19 October 2026

This update supersedes the older extractive-default UI and provider TIMEOUT limitation below. The knowledge page now has one primary question flow: retrieve published evidence, obtain binary consent if needed, then synthesize from the retrieved passages. Agreement continues the pending question with the newly returned permission revision; declining dispatches nothing. Enabling AI later does not replay a declined question. Server-only lookup and explicit permission withdrawal remain available. Missing evidence still abstains before generation. Original citation/page/revision checks and post-generation permission/source revalidation are retained.

Diagnosis used the same server key and a tiny fictional prompt: gemini-3.8-flash returned HTTP 503, while gemini-3.5-flash-lite returned a valid structured answer in 1.375s. This is evidence of the observed model/service failure, not a claim that 3.8 is permanently unavailable. The full source-grounded local request using the former 3.8 setting completed via the alternate in 9.422s. With 3.5 configured directly, actual HTTP acceptance generated a grounded answer in 2.266s. These are individual measurements, not a latency guarantee.

The default is now 3.5 Flash-Lite with low thinking. Existing 3.8 configurations can try one explicit server-configured alternate on timeout, network/5xx or unavailable model. asyncio.wait_for bounds each complete attempt, including response-body reads, and both attempts share the existing overall deadline. The primary gets at most 8s if an alternate is configured; the total remains 25s by default. No alternate attempt occurs for authentication/quota errors, bad input or invalid model output, or if the alternate is blank/identical. An admitted app question can therefore make up to two upstream calls. API responses report the actual model and optional fallback_from metadata; model output cannot set this server transport metadata. All candidates stay at the fixed Google host with the same bounded excerpts and existing consent.

The RAG prompt asks for a concise explanation grounded in the passages, inline source markers and explicit missing-information/sample qualifications. It does not request exposure of chain-of-thought. Lexical retrieval quality and semantic correctness remain separate limitations; no model training or new vector search is claimed.

Primary references consulted for this change:

- Model capabilities/latency intent: https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite
- REST JSON response format: https://ai.google.dev/gemini-api/docs/generate-content/structured-output
- Supported 3.8 thinking levels: https://ai.google.dev/gemini-api/docs/generate-content/whats-new-gemini-3.8

Actual runs, deployment state and receipts are recorded in IMPLEMENTATION_REPORT.md and submission/evidence/rag-llm-*. Browser regression tests mock generation; the separate real browser/API checks are explicitly identified.

---

# Topic D — managed insurance retrieval-augmented generation

Reviewed 19 October 2026. This document describes implemented engineering behaviour, not insurance advice or a compliance certification.

## Contest fit and research

Topic D calls for policy Q&A, coverage-gap analysis and claims guidance. The official leaflet assigns 40% to task completion, 30% to security/compliance and 30% to innovation/interaction. A managed evidence library adds source-grounded Q&A to the existing reviewed-policy comparison and claim-preparation workflows. Teams must still choose one registration topic; combining features does not create a joint registration topic.

Primary contest sources:
- https://www.ieee-cis-singapore.org/2026-fintechathon
- https://www.pol.cmu.ac.th/public/blog/attachment/download/7a51866a-4cee-42b5-9187-fa4e1f4df411

Lewis et al. describe retrieval-augmented generation as combining retrieved external evidence with language generation. This MVP implements retrieval followed by optional generation; it does not reproduce the paper's dense retriever, train a model or claim equivalent experimental results. BM25 provides a transparent local ranking baseline, with document-frequency and length normalization. Page-preserving overlapping chunks and a small explicit VI/EN/ZH insurance glossary improve multilingual term matching; they are not semantic neural embeddings. This choice avoids sending an entire corpus to an embedding API or loading a large model into the free demo host.

- RAG paper: https://arxiv.org/abs/2005.11401
- BM25 primary technical reference: https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html
- Provider structured output: https://ai.google.dev/gemini-api/docs/generate-content/structured-output
- Gemini 3.8 migration: https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8
- Thinking/latency parameters: https://ai.google.dev/gemini-api/docs/generate-content/thinking.md
- Authorization guidance: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- Untrusted RAG inputs: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
- Unpaid Gemini data terms: https://ai.google.dev/gemini-api/terms

## Method and architecture

1. Trace the existing owner-private document search, optional Gemini consent, authentication and Topic D workflows.
2. Add a separate shared library with a server-assigned administrator capability, publication state, source provenance, licensing declaration, revision journal and durable chunks. Ordinary private policy/claim files are not copied into this corpus.
3. Ingest authored text or locally extracted PDF/image/TXT/MD pages. Chunks contain at most 900 characters with approximately 100-character overlap; store page and character offsets within the locally extracted page text (OCR can be imperfect), term frequencies, token count and source SHA-256. Admin preview searches drafts locally.
4. Rank published/current/nondeleted chunks with BM25 (k1=1.5, b=.75), diacritic normalization, Chinese bigrams and explicit insurance-concept expansion. Match relevant benefit concepts, diversify requested concepts and suppress overlapping duplicate chunks. Filter publication, document/category and territory before ranking, not after top-k. Select at most three excerpts. Retrieval loads no original file binaries into ranking memory.
5. Without Gemini, return exact excerpts with an extractive label. With valid document consent, build a bounded original-excerpt prompt; Gemini has no tools and receives a source-only insurance rule. Reject unknown/empty source IDs, retain original citations and fall back honestly on errors. The API does not verify semantic entailment of every generated sentence; source IDs alone are not a proof of correctness.
6. After the model call, reload session/consent and source state. Reject revoked/expired sessions or permissions; suppress stale content if a source was changed/withdrawn during either successful generation or a timeout fallback.
7. Also fill unused slots in the existing copilot document context from published library sources, keeping the combined private/sample excerpt limit at three. This does not add personal finance/policy or claim permissions.
8. Run adversarial API tests, a documented regression retrieval set, actual HTTP acceptance and browser workflows. Provider tests use fictional material only and explicitly distinguish mocks, successful real calls and fallbacks.

## Administrator account and lifecycle

`is_rag_admin` is a database capability in addition to the existing STUDENT role. Administration requires this capability plus a real account session. Demo bearer/operator sessions are denied. Public registration/profile DTOs reject privilege fields. Argon2 passwords, HttpOnly session cookies, CSRF, origin checks and existing login throttles are reused.

Server CLI or explicit server-only RAG_ADMIN_EMAIL/RAG_ADMIN_PASSWORD configuration creates the first test account. Credentials are random and stored only in ignored .local files / hosting secrets; nothing is seeded with a public default password. Provisioning is idempotent, never auto-promotes an existing student and never resets an existing admin password. Account management/issuing more administrator privileges is deliberately server-operated.

Create -> draft -> local review/preview -> explicit binary publication confirmation -> published. Metadata/content replacement returns to draft and updates chunks atomically. Revision checks reject stale writes. Unpublish/delete immediately remove a source from new retrieval. Delete is recoverable trash; restore is a draft. A source reader/download accepts only the currently published revision. Journals store metadata/hashes, not a backup of every old file. Previously downloaded copies/chat or provider-held content cannot be recalled.

Uploads ask before sending bytes. Publication has a separate two-button popup disclosing account-wide sharing and optional downstream Gemini excerpts. Publication requires source/usage metadata, a matching notice, an affirmative action and the existing sensitive-text tripwire. The tripwire cannot prove anonymity or copyright rights; the administrator must review. No source URL is fetched by the server; credential-bearing URLs are rejected.

## Data and evaluation

`fixtures/rag_demo_corpus.json` contains three team-authored CC0 fictional examples: English policy terms, Vietnamese claim-preparation guidance and Chinese terminology. They are marked TEST_FIXTURE, not authentic insurer policies or training data. Seed uses stable IDs, never overwrites edited/deleted sources and does not resurrect trashed material. An admin must add legitimately usable real references for real-world coverage questions.

The regression set `fixtures/rag_evaluation.json` has 18 answerable and 6 unsupported/unrelated questions in VI/EN/ZH. On the supplied fixture corpus: Recall@3 = 1.0, MRR@3 = 0.7962963, abstention accuracy = 1.0. These are 24 handcrafted regression cases, not independent/human-rated answer accuracy or a generalisation benchmark. Evidence: submission/evidence/rag-retrieval-evaluation.json. `scripts/evaluate_rag.py` reruns the actual retriever against the configured database; changes to the corpus can change these scores.

## Limits

No dense/vector embeddings, neural reranker, model fine-tuning, comprehensive language understanding, automatic insurer authenticity verification or automatic legal eligibility/claims decision is claimed. Lexical/glossary matching can miss paraphrases and retrieve adjacent clauses; inspect the full source. BM25 scores are relative retrieval scores, not confidence probabilities. The corpus has bounded demo quotas (100 documents including trash; 20,000 chunks) and synchronous local OCR. It is intended for a small demonstration corpus, not an unbounded enterprise search installation.

Drafts and trash remain administrator-readable; automatic retention/purge, MFA, verified email ownership, dual-person publication approval, version-content rollback, full account deletion and independent penetration/privacy audit remain unfinished operational work. Free-host/database lifecycle and model availability remain deployment constraints. See IMPLEMENTATION_REPORT.md for exact completed runs, real provider outcome and known failures.
