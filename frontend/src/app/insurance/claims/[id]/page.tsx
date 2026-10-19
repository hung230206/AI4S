"use client";
import {use, useCallback, useEffect, useState} from "react";
import Link from "next/link";
import {api, API, authHeaders, downloadOwned, time} from "@/lib/api";
import {useInsuranceCopy, type ClaimCase} from "@/lib/insurance";
import {useToken} from "@/components/shell";
import {Heading, ErrorBox} from "@/components/ui";
import {ArrowLeft, Download, FileCheck2, ShieldCheck} from "lucide-react";
import {ClaimEditor} from "@/components/claim-editor";

export default function ClaimDetailPage({params}: {params: Promise<{id: string}>}) {
  const {id} = use(params); const token = useToken(); const t = useInsuranceCopy();
  const [data, setData] = useState<ClaimCase>(); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const [target, setTarget] = useState(""); const [confirmed, setConfirmed] = useState(false); const [note, setNote] = useState("");
  const [pendingChecks, setPendingChecks] = useState<Record<string, boolean>>({});
  const load = useCallback(async () => setData(await api<ClaimCase>(`/insurance/claims/${id}`, token)), [id, token]);
  useEffect(() => {let active = true; api<ClaimCase>(`/insurance/claims/${id}`, token).then(value => {if (active) setData(value);}).catch(e => {if (active) setError(e.message);}); return () => {active = false;};}, [id, token]);
  async function act(action: () => Promise<void>) {if (busy) return; setBusy(true); setError(""); try {await action();} catch(e) {setError((e as Error).message);} finally {setBusy(false);}}
  async function attach(file: File | undefined, code: string) {
    if (!file || !data) return;
    const body = new FormData(); body.append("file", file); body.append("item_code", code); body.append("revision", String(data.revision));
    const response = await fetch(`${API}/api/v1/insurance/claims/${id}/attachments`, {method: "POST", credentials: "include", headers: authHeaders(token), body});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || "Upload failed");
    setData(result); setTarget("");
  }
  function selectTarget(value: string) {setTarget(value); setConfirmed(false); setNote("");}
  return <div className="insurance-workspace">
    <Link className="text-link" href="/insurance"><ArrowLeft size={16}/>{t("insurance")}</Link>
    <Heading eyebrow={t("claims")} title={data?.title || t("open")}>{t("claimHelp")}</Heading>
    <div className="info-note insurance-boundary"><ShieldCheck size={22}/><p>{t("boundary")}</p></div>
    <ErrorBox message={error}/>{error && <button className="text-link" disabled={busy} onClick={() => act(load)}>{t("refresh")}</button>}
    {!data ? !error && <p role="status">{t("busy")}</p> : <>
      {["DRAFT", "READY"].includes(data.status) && <ClaimEditor key={data.revision} data={data} token={token} busy={busy} act={act} receive={value => {setData(value); setTarget("");}}/>}
      <section className="card"><div className="section-heading"><h2>{data.amount} {data.currency}</h2><span className="badge neutral">{t(data.status)}</span></div><p>{t(data.benefit_kind)} · {data.incident_date}</p>{data.deadline && <p>{t("deadline")}: {data.deadline}</p>}{data.description && <p className="insurance-preserve">{data.description}</p>}{data.warnings.map(w => <p className="error" key={w}>{t(w)}</p>)}<a className="text-link" href={data.guide_url} target="_blank" rel="noreferrer">{t("guide")} ↗</a></section>
      <section className="card"><h2>{t("checklist")}</h2><div className="insurance-checklist">{data.checklist.map(item => <article key={item.code} className={item.complete ? "complete" : ""}><div className="section-heading"><h3>{t(item.code)}</h3>{item.complete && <FileCheck2 size={21} aria-label={t("attached")}/>}</div>
        <label className="insurance-check"><input type="checkbox" disabled={busy || !["DRAFT", "READY"].includes(data.status)} checked={pendingChecks[item.code] ?? item.prepared_externally} onChange={e => {const prepared = e.target.checked; setPendingChecks({[item.code]: prepared}); act(async () => {setData(await api<ClaimCase>(`/insurance/claims/${id}/checklist`, token, {revision: data.revision, code: item.code, prepared_externally: prepared})); setTarget("");}).finally(() => setPendingChecks({}));}}/><span>{t("outsidePrepared")}</span></label>
        {!item.offline_only && ["DRAFT", "READY"].includes(data.status) && <label>{t("attach")} · PDF / PNG / JPG / TXT ≤ 5 MB<input type="file" disabled={busy} accept=".pdf,.png,.jpg,.jpeg,.txt" onChange={e => {const file = e.target.files?.[0]; e.target.value = ""; act(() => attach(file, item.code));}}/></label>}
        {data.attachments.filter(f => f.item_code === item.code).map(f => <div className="insurance-attachment" key={f.id}><strong>{f.filename}</strong><small>SHA-256: {f.sha256}</small><button className="text-link" disabled={busy} onClick={() => act(() => downloadOwned(`/insurance/claims/${id}/attachments/${f.id}`, token, f.filename))}><Download size={14}/>{t("download")}</button></div>)}
      </article>)}</div></section>
      <section className="card"><h2>{t("export")}</h2><p>{t("exportHelp")}</p><button className="button secondary" disabled={busy} onClick={() => act(() => downloadOwned(`/insurance/claims/${id}/export`, token, `claim-preparation-${id}.zip`))}><Download size={17}/>{t("export")}</button>
        <div className="insurance-actions insurance-transitions">
          {data.status === "DRAFT" && <button className="button primary" disabled={!data.ready || busy} onClick={() => selectTarget("READY")}>{t("markReady")}</button>}
          {data.status === "READY" && <><button className="button primary" disabled={busy} onClick={() => selectTarget("SUBMITTED_EXTERNALLY")}>{t("external")}</button><button className="button secondary" disabled={busy} onClick={() => selectTarget("DRAFT")}>{t("reopen")}</button></>}
          {data.status === "SUBMITTED_EXTERNALLY" && <button className="button secondary" disabled={busy} onClick={() => selectTarget("CLOSED")}>{t("closeCase")}</button>}
        </div>
        {target && <form className="insurance-inline-confirm" aria-label={t("confirm")} onSubmit={e => {e.preventDefault(); act(async () => {setData(await api<ClaimCase>(`/insurance/claims/${id}/transition`, token, {revision: data.revision, status: target, confirmed, note})); setTarget("");});}}>
          {target === "SUBMITTED_EXTERNALLY" && <label>{t("reference")}<input maxLength={500} required value={note} onChange={e => setNote(e.target.value)}/></label>}
          <label className="insurance-check"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)}/><span>{t("transitionConfirm")}</span></label><button className="button primary" disabled={!confirmed || busy}>{t("confirm")}</button>
        </form>}
      </section>
      <details className="card"><summary>{t("snapshot")} · v{data.policy_snapshot.revision}</summary><h3>{data.policy_snapshot.name}</h3><p>{data.policy_snapshot.starts_on} → {data.policy_snapshot.ends_on} · {t(data.policy_snapshot.territory)}</p><span className="badge neutral">{t(data.policy_snapshot.document_kind)}</span>{data.policy_snapshot.benefits.map(b => <blockquote key={b.kind}><strong>{t(b.kind)} · {t(b.status)}</strong><p>{b.evidence_quote}</p><small>{t("page")} {b.source_page || "—"}</small></blockquote>)}</details>
      <details className="card"><summary>{t("history")} · {data.history.length}</summary><ol className="insurance-history">{data.history.map((h, i) => <li key={i}><time>{time(h.at)}</time><strong>{h.status ? t(h.status) : h.action}</strong>{h.note && <p>{h.note}</p>}</li>)}</ol></details>
    </>}
  </div>;
}
