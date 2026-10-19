"use client";
import {useCallback, useEffect, useRef, useState} from "react";
import Link from "next/link";
import {useAuth} from "@/components/shell";
import {useI18n} from "@/components/i18n-provider";
import {Heading, ErrorBox} from "@/components/ui";
import {api, API, authHeaders, documentKinds, time} from "@/lib/api";
import {requestFileConsent, fileConsentHeader} from "@/lib/file-consent";
import {RAG_PUBLICATION_NOTICE, ragText, type RagDocument, type RagMatch} from "@/lib/rag";

const blank = () => ({title: "", publisher: "", source_url: "", source_kind: "TEST_FIXTURE", license_note: "", category: "POLICY", language: "vi", jurisdiction: "CN", content: ""});
export default function RagAdminPage() {
  const {token, user, logout} = useAuth(); const {locale} = useI18n(); const t = ragText(locale);
  const [docs, setDocs] = useState<RagDocument[]>([]); const [trash, setTrash] = useState(false);
  const [notice, setNotice] = useState(""); const [selected, setSelected] = useState<RagDocument>();
  const [form, setForm] = useState(blank); const [formOpen, setFormOpen] = useState(false); const [editing, setEditing] = useState<RagDocument>();
  const [mode, setMode] = useState("text"); const [file, setFile] = useState<File>(); const [fileKey, setFileKey] = useState(0);
  const [replacement, setReplacement] = useState<File>(); const [question, setQuestion] = useState(""); const [matches, setMatches] = useState<RagMatch[]>();
  const [deleteId, setDeleteId] = useState(""); const [error, setError] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false); const inFlight = useRef(false);
  const load = useCallback(async () => {const data = await api<{items: RagDocument[]; publication_notice: string}>(`/admin/rag/documents?deleted=${trash}`, token); setDocs(data.items); setNotice(data.publication_notice);}, [token, trash]);
  useEffect(() => {if (!user?.is_rag_admin) return; let active = true; api<{items: RagDocument[]; publication_notice: string}>(`/admin/rag/documents?deleted=${trash}`, token).then(data => {if (active) {setDocs(data.items); setNotice(data.publication_notice);}}).catch(e => {if (active) setError(e.message);}); return () => {active = false;};}, [token, trash, user?.is_rag_admin]);
  async function act(action: () => Promise<void>) {
    if (inFlight.current) return; inFlight.current = true; setBusy(true); setError(""); setMessage("");
    try {await action();} catch(e) {setError((e as Error).message);} finally {inFlight.current = false; setBusy(false);}
  }
  async function inspect(doc: RagDocument) {setSelected(await api<RagDocument>(`/admin/rag/documents/${doc.id}`, token)); setMatches(undefined); setQuestion(""); setReplacement(undefined); setFileKey(k => k + 1);}
  async function openEdit(doc: RagDocument) {
    const detail = await api<RagDocument>(`/admin/rag/documents/${doc.id}`, token);
    setEditing(detail); setForm({title: detail.title, publisher: detail.publisher, source_url: detail.source_url || "", source_kind: detail.source_kind, license_note: detail.license_note, category: detail.category, language: detail.language, jurisdiction: detail.jurisdiction, content: detail.origin === "AUTHORED_TEXT" ? detail.pages?.map(p => p.text).join("\n\n") || "" : ""}); setFormOpen(true); setMode("text"); setFile(undefined); setFileKey(k => k + 1);
  }
  async function sendFile(path: string, upload: File, metadata?: unknown, revision?: number) {
    if (!await requestFileConsent("rag-corpus")) return false;
    const body = new FormData(); body.append("file", upload); if (metadata) body.append("metadata", JSON.stringify(metadata)); if (revision) body.append("revision", String(revision));
    const response = await fetch(`${API}/api/v1${path}`, {method: "POST", credentials: "include", headers: {...authHeaders(token), ...fileConsentHeader("rag-corpus")}, body});
    const data = await response.json(); if (!response.ok) throw new Error(data.error?.message || "Upload failed");
    return data as RagDocument;
  }
  async function save() {
    const {content, ...fields} = form; const metadata = {...fields, source_url: form.source_url || null};
    let doc: RagDocument | false;
    if (editing) doc = await api<RagDocument>(`/admin/rag/documents/${editing.id}/update`, token, {...metadata, revision: editing.revision, ...(editing.origin === "AUTHORED_TEXT" ? {content} : {})});
    else if (mode === "file") {if (!file) return; doc = await sendFile("/admin/rag/documents/upload", file, metadata);}
    else doc = await api<RagDocument>("/admin/rag/documents", token, {...metadata, content});
    if (!doc) return;
    setFormOpen(false); setEditing(undefined); setFile(undefined); setMessage(t.saved); await load(); await inspect(doc);
  }
  async function change(doc: RagDocument, action: "publish" | "unpublish" | "delete" | "restore") {
    if (action === "publish") {
      if (notice !== RAG_PUBLICATION_NOTICE) throw new Error("Thông báo công bố đã thay đổi; tải lại trang.");
      if (!await requestFileConsent("rag-publish")) return;
    }
    await api(`/admin/rag/documents/${doc.id}/${action}`, token, {revision: doc.revision, ...(action === "publish" ? {publication_confirmed: true, notice_version: RAG_PUBLICATION_NOTICE} : {})});
    setSelected(undefined); setDeleteId(""); setMessage(t.saved); await load();
  }
  if (!user?.is_rag_admin) return <><Heading eyebrow="ADMIN · RAG" title={t.admin}>{t.denied}</Heading><button className="button primary" onClick={() => logout().catch(e => setError(e.message))}>{t.login}</button><ErrorBox message={error}/></>;
  return <>
    <Heading eyebrow="ADMIN · TOPIC D" title={t.admin}>{t.adminIntro}</Heading><p className="info-note">{t.sourceNote}</p><Link className="text-link" href="/copilot">{t.title} →</Link><ErrorBox message={error}/>{message && <p role="status" className="success-note">{message}</p>}
    <div className="copilot-actions"><button className="button primary" disabled={busy} onClick={() => {setEditing(undefined); setForm(blank()); setFormOpen(true); setFile(undefined); setMode("text"); setFileKey(k => k + 1);}}>{t.add}</button><button className="button secondary" disabled={busy} onClick={() => {setTrash(v => !v); setSelected(undefined); setFormOpen(false);}}>{trash ? t.active : t.trash}</button></div>
    {formOpen && <form className="card detail-card form-stack rag-editor" onSubmit={e => {e.preventDefault(); act(save);}}>
      <h2>{editing ? t.edit : t.add}</h2>
      <div className="form-grid">
        <label>{t.name}<input required minLength={3} maxLength={200} value={form.title} onChange={e => setForm({...form, title: e.target.value})}/></label>
        <label>{t.publisher}<input required minLength={2} maxLength={200} value={form.publisher} onChange={e => setForm({...form, publisher: e.target.value})}/></label>
        <label>{t.kind}<select aria-label={t.kind} value={form.source_kind} onChange={e => setForm({...form, source_kind: e.target.value})}><option value="TEST_FIXTURE">{documentKinds.TEST_FIXTURE}</option><option value="PUBLIC_REFERENCE">{documentKinds.PUBLIC_REFERENCE}</option></select></label>
        <label>{t.category}<select aria-label={t.category} value={form.category} onChange={e => setForm({...form, category: e.target.value})}><option value="POLICY">Policy</option><option value="CLAIMS">Claims</option><option value="GLOSSARY">Glossary</option></select></label>
        <label>{t.language}<select aria-label={t.language} value={form.language} onChange={e => setForm({...form, language: e.target.value})}><option value="vi">Tiếng Việt</option><option value="en">English</option><option value="zh">中文</option></select></label>
        <label>{t.country}<select aria-label={t.country} value={form.jurisdiction} onChange={e => setForm({...form, jurisdiction: e.target.value})}><option value="CN">CN</option><option value="VN">VN</option><option value="WORLD">WORLD</option></select></label>
      </div>
      <label>{t.source}<input type="url" required={form.source_kind === "PUBLIC_REFERENCE"} maxLength={2000} value={form.source_url} onChange={e => setForm({...form, source_url: e.target.value})}/></label>
      <label>{t.rights}<textarea aria-label={t.rights} required minLength={10} maxLength={1000} rows={2} value={form.license_note} onChange={e => setForm({...form, license_note: e.target.value})}/></label>
      {!editing && <div className="prompt-chips"><button type="button" aria-pressed={mode === "text"} onClick={() => setMode("text")}>{t.authored}</button><button type="button" aria-pressed={mode === "file"} onClick={() => setMode("file")}>{t.uploaded}</button></div>}
      {((!editing && mode === "text") || editing?.origin === "AUTHORED_TEXT") && <label>{t.content}<textarea aria-label={t.content} required minLength={40} maxLength={200000} rows={9} value={form.content} onChange={e => setForm({...form, content: e.target.value})}/></label>}
      {!editing && mode === "file" && <label>{t.file}<input key={fileKey} type="file" required accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.md" onChange={e => setFile(e.target.files?.[0])}/></label>}
      <div className="copilot-actions"><button className="button primary" disabled={busy}>{busy ? t.working : t.save}</button><button type="button" className="button secondary" disabled={busy} onClick={() => setFormOpen(false)}>{t.cancel}</button></div>
    </form>}
    <section className="rag-admin-list"><h2>{trash ? t.trash : t.active}</h2>{!docs.length && <p>{t.empty}</p>}{docs.map(doc => <article className="card detail-card" key={doc.id}><h3>{doc.title}</h3><span className={`badge ${doc.published ? "reference" : "neutral"}`}>{doc.published ? t.published : t.draft}</span><span className={`badge ${doc.source_kind === "TEST_FIXTURE" ? "demo" : "reference"}`}>{documentKinds[doc.source_kind]}</span><p className="small muted">{t.version} {doc.revision} · {doc.language} · {doc.page_count} {t.page} · {time(doc.updated_at)}</p>
      <div className="copilot-actions"><button className="text-link" disabled={busy} onClick={() => act(() => inspect(doc))}>{t.read}</button>{trash ? <button className="button secondary" disabled={busy} onClick={() => act(() => change(doc, "restore"))}>{t.restore}</button> : <><button className="button secondary" disabled={busy} onClick={() => act(() => openEdit(doc))}>{t.edit}</button><button className="button secondary" disabled={busy || (!doc.published && notice !== RAG_PUBLICATION_NOTICE)} onClick={() => act(() => change(doc, doc.published ? "unpublish" : "publish"))}>{doc.published ? t.unpublish : t.publish}</button><button className="text-link" disabled={busy} onClick={() => setDeleteId(doc.id)}>{t.remove}</button></>}</div>
      {deleteId === doc.id && <div className="archive-confirm"><p>{t.confirmDelete}</p><button className="button danger" disabled={busy} onClick={() => act(() => change(doc, "delete"))}>{t.confirm}</button><button className="button secondary" disabled={busy} onClick={() => setDeleteId("")}>{t.cancel}</button></div>}
    </article>)}</section>
    {selected && <section className="card detail-card form-stack rag-source"><h2>{selected.title}</h2><p>{t.version} {selected.revision} · {selected.chunk_count} chunks · {selected.filename}</p><p className="small muted rag-hash">SHA-256: {selected.sha256}</p><p>{selected.license_note}</p>{selected.pages?.map(page => <details key={page.page} open><summary>{t.page} {page.page}</summary><pre className="policy-source">{page.text}</pre></details>)}
      {!selected.deleted && <><form className="form-stack" onSubmit={e => {e.preventDefault(); act(async () => {const result = await api<{matches: RagMatch[]}>("/admin/rag/preview", token, {question, document_id: selected.id}); setMatches(result.matches);});}}><label>{t.question}<input minLength={2} maxLength={500} required value={question} onChange={e => setQuestion(e.target.value)}/></label><button className="button secondary" disabled={busy}>{t.preview}</button></form>{matches && <div><p>{matches.length} chunks</p>{matches.map((match, i) => <blockquote key={i}>{match.excerpt}</blockquote>)}</div>}
      <form className="form-stack" onSubmit={e => {e.preventDefault(); if (replacement) act(async () => {const next = await sendFile(`/admin/rag/documents/${selected.id}/file`, replacement, undefined, selected.revision); if (next) {await load(); await inspect(next); setMessage(t.saved);}});}}><label>{t.replace}<input key={fileKey} type="file" required accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.md" onChange={e => setReplacement(e.target.files?.[0])}/></label><button className="button secondary" disabled={busy || !replacement}>{t.replace}</button></form></>}
      <details><summary>{t.history}</summary>{selected.history?.map(item => <p key={item.revision}>{t.version} {item.revision} · {item.action} · {time(item.at)}</p>)}</details>
    </section>}
  </>;
}
