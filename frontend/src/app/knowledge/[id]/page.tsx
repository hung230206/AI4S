"use client";
import {use, useEffect, useState} from "react";
import Link from "next/link";
import {useSearchParams} from "next/navigation";
import {useAuth} from "@/components/shell";
import {useI18n} from "@/components/i18n-provider";
import {ErrorBox} from "@/components/ui";
import {api, downloadOwned, documentKinds} from "@/lib/api";
import {ragText, type RagDocument} from "@/lib/rag";

export default function SourcePage({params}: {params: Promise<{id: string}>}) {
  const {id} = use(params); const revision = useSearchParams().get("revision"); const {token} = useAuth(); const {locale} = useI18n(); const t = ragText(locale);
  const [doc, setDoc] = useState<RagDocument>(); const [error, setError] = useState("");
  useEffect(() => {let active = true; api<RagDocument>(`/rag/documents/${id}${revision ? `?revision=${encodeURIComponent(revision)}` : ""}`, token).then(value => {if (active) setDoc(value);}).catch(e => {if (active) setError(e.message);}); return () => {active = false;};}, [id, revision, token]);
  return <><Link className="text-link" href="/knowledge">← {t.title}</Link><ErrorBox message={error}/>{error && <p>{t.changed}</p>}{doc && <article className="card detail-card rag-source"><h1>{doc.title}</h1><span className={`badge ${doc.source_kind === "TEST_FIXTURE" ? "demo" : "reference"}`}>{documentKinds[doc.source_kind]}</span><p>{doc.publisher} · {t.version} {doc.revision}</p><p>{doc.license_note}</p>{doc.source_url && <a className="text-link" href={doc.source_url} target="_blank" rel="noreferrer">{t.source} ↗</a>}<p><button className="button secondary" onClick={() => downloadOwned(`/rag/documents/${doc.id}/download?revision=${doc.revision}`, token, doc.filename).catch(e => setError(e.message))}>{t.download}</button></p><p className="small muted rag-hash">SHA-256: {doc.sha256}</p>{doc.pages?.map(page => <section id={`page-${page.page}`} key={page.page}><h2>{t.page} {page.page}</h2><pre className="policy-source">{page.text}</pre></section>)}</article>}</>;
}
