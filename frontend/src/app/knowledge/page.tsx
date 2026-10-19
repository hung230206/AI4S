"use client";
import {useEffect, useRef, useState} from "react";
import Link from "next/link";
import {useAuth} from "@/components/shell";
import {useI18n} from "@/components/i18n-provider";
import {AiPrivacyControls} from "@/components/ai-privacy";
import {Heading, ErrorBox} from "@/components/ui";
import {api, documentKinds} from "@/lib/api";
import {ragText, type RagDocument, type RagAnswer} from "@/lib/rag";
import type {AiPermission} from "@/lib/privacy";

export default function KnowledgePage() {
  const {token, user} = useAuth(); const {locale} = useI18n(); const t = ragText(locale);
  const [docs, setDocs] = useState<RagDocument[]>([]); const [configured, setConfigured] = useState(false);
  const [permission, setPermission] = useState<AiPermission>(); const [requested, setRequested] = useState(false);
  const [cloud, setCloud] = useState(false); const [question, setQuestion] = useState(""); const [selected, setSelected] = useState("");
  const [reply, setReply] = useState<RagAnswer>(); const [preview, setPreview] = useState<unknown>();
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const inFlight = useRef(false);
  useEffect(() => {
    let active = true;
    api<{items: RagDocument[]; gemini_configured: boolean}>("/rag/documents", token).then(result => {if (active) {setDocs(result.items); setConfigured(result.gemini_configured);}}).catch(e => {if (active) setError(e.message);});
    const refresh = () => api<AiPermission>("/privacy/ai-permission", token).then(value => {if (active) {setPermission(value); if (!value.enabled || !value.scopes.includes("documents")) setCloud(false);}}).catch(() => {if (active) {setPermission(undefined); setCloud(false);}});
    refresh(); window.addEventListener("focus", refresh);
    return () => {active = false; window.removeEventListener("focus", refresh);};
  }, [token]);
  useEffect(() => {
    if (!permission?.enabled || !permission.expires_at) return;
    const timer = setTimeout(() => {setCloud(false); setPermission(p => p ? {...p, enabled: false, scopes: []} : p); setPreview(undefined);}, Math.max(0, new Date(permission.expires_at).getTime() - Date.now()));
    return () => clearTimeout(timer);
  }, [permission]);
  async function submit(isPreview = false) {
    if (inFlight.current || question.trim().length < 2 || (cloud && !permission?.enabled)) return;
    inFlight.current = true; setBusy(true); setError(""); setPreview(undefined);
    try {
      const body = {question, language: locale, document_id: selected || null, use_gemini: cloud, privacy_revision: cloud ? permission?.revision : undefined};
      if (isPreview) setPreview(await api("/rag/preview", token, body));
      else setReply(await api<RagAnswer>("/rag/ask", token, body));
    } catch(e) {setError((e as Error).message);} finally {inFlight.current = false; setBusy(false);}
  }
  return <>
    <Heading eyebrow="TOPIC D · RAG" title={t.title}>{t.intro}</Heading>
    {user?.is_rag_admin && <Link className="button secondary" href="/admin/rag">{t.admin} →</Link>}
    <p className="info-note">{t.noInference}</p><ErrorBox message={error}/>
    <section className="card detail-card form-stack">
      <div className="prompt-chips" role="group" aria-label={t.title}><button type="button" aria-pressed={!cloud} disabled={busy} onClick={() => setCloud(false)}>{t.local}</button><button type="button" aria-pressed={cloud} disabled={busy || !configured || !permission} onClick={() => permission?.enabled && permission.scopes.includes("documents") ? setCloud(true) : setRequested(true)}>{t.gemini}</button></div>
      <AiPrivacyControls value={permission} requested={requested} onDismiss={() => setRequested(false)} onChange={value => {setPermission(value); setPreview(undefined); if (!value.enabled) setCloud(false);}} onEnabled={() => setCloud(true)}/>
      <div className="prompt-chips">{t.questions.map(text => <button type="button" disabled={busy} key={text} onClick={() => setQuestion(text)}>{text}</button>)}</div>
      <form className="form-stack" onSubmit={e => {e.preventDefault(); submit();}}>
        <label>{t.scope}<select aria-label={t.scope} value={selected} onChange={e => {setSelected(e.target.value); setReply(undefined);}}><option value="">{t.all}</option>{docs.map(doc => <option key={doc.id} value={doc.id}>{doc.title}</option>)}</select></label>
        <label>{t.question}<textarea aria-label={t.question} rows={3} required minLength={2} maxLength={500} value={question} disabled={busy} onChange={e => {setQuestion(e.target.value); setPreview(undefined);}} onKeyDown={e => {if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing && e.nativeEvent.keyCode !== 229) {e.preventDefault(); if (!e.repeat) e.currentTarget.form?.requestSubmit();}}}/></label>
        <div className="copilot-actions"><button className="button primary" disabled={busy || !docs.length || question.trim().length < 2}>{busy ? t.working : t.ask}</button>{cloud && <button type="button" className="text-link" disabled={busy || question.trim().length < 2} onClick={() => submit(true)}>{t.dataPreview}</button>}</div>
      </form>
      {!docs.length && <p>{t.empty}</p>}
    </section>
    {busy && <p role="status">{t.working}</p>}
    {preview !== undefined && <details open className="privacy-preview"><summary>{t.dataPreview}</summary><pre>{JSON.stringify(preview, null, 2)}</pre></details>}
    {reply && <section className="rag-answer" aria-live="polite"><article className="card detail-card"><span className="badge reference">{reply.provider === "GEMINI" ? "Gemini · RAG" : t.local}</span>{reply.fallback_reason && <p className="info-note">{reply.status === "SOURCES_CHANGED" ? t.changed : t.fallback} ({reply.fallback_reason})</p>}{reply.status === "PARTIAL_EVIDENCE" && <p className="info-note">{t.partial}</p>}<p className="copilot-answer-text">{reply.answer}</p></article>
      {reply.citations.length > 0 && <h2>{t.evidence}</h2>}{reply.citations.map(match => <article className="card citation-card" key={match.chunk_id || match.source_id}><span className="badge reference">{match.source_id} · {t.page} {match.page} · {t.version} {match.revision}</span><span className={`badge ${match.document_kind === "TEST_FIXTURE" ? "demo" : "reference"}`}>{documentKinds[match.document_kind]}</span><h3>{match.title}</h3><blockquote>{match.excerpt}</blockquote><p className="small muted">{match.publisher} · {match.filename}</p><Link className="text-link" href={match.href} target="_blank">{t.fullSource} ↗</Link></article>)}
    </section>}
    <section className="rag-library"><h2>{t.scope}</h2>{docs.map(doc => <article className="card detail-card" key={doc.id}><h3><Link href={`/knowledge/${doc.id}?revision=${doc.revision}`}>{doc.title} ↗</Link></h3><span className={`badge ${doc.source_kind === "TEST_FIXTURE" ? "demo" : "reference"}`}>{documentKinds[doc.source_kind]}</span><p className="small muted">{doc.publisher} · {doc.language.toUpperCase()} · {doc.page_count} {t.page} · {t.version} {doc.revision}</p></article>)}</section>
  </>;
}
