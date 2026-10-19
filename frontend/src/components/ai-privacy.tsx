"use client";
import {useEffect, useRef, useState} from "react";
import Link from "next/link";
import {ShieldCheck} from "lucide-react";
import {api} from "@/lib/api";
import {AI_PRIVACY_NOTICE_VERSION, privacyText, type AiPermission} from "@/lib/privacy";
import {useI18n} from "./i18n-provider";
import {useAuth} from "./shell";
import {ErrorBox} from "./ui";

export function AiPrivacyControls({value, onChange, onEnabled}: {value: AiPermission | undefined; onChange: (value: AiPermission) => void; onEnabled?: () => void}) {
  const {token} = useAuth(); const {locale} = useI18n(); const t = privacyText(locale);
  const ref = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false); const [scopes, setScopes] = useState<string[]>([]);
  const [ack, setAck] = useState(false); const [adult, setAdult] = useState(false); const [nonSensitive, setNonSensitive] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  useEffect(() => {
    if (open && ref.current) {
      ref.current.showModal();
      ref.current.querySelector<HTMLElement>("h2")?.focus({preventScroll: true});
      ref.current.scrollTop = 0;
    } else ref.current?.close();
  }, [open]);
  function edit() {setScopes(value?.enabled ? value.scopes : []); setAck(false); setAdult(false); setNonSensitive(false); setError(""); setOpen(true);}
  async function save(enabled: boolean) {
    if (!value || busy) return;
    setBusy(true); setError("");
    try {
      const next = await api<AiPermission>("/privacy/ai-permission", token, {revision: value.revision, notice_version: enabled ? AI_PRIVACY_NOTICE_VERSION : value.notice_version, enabled, scopes: enabled ? scopes : [], acknowledged: ack, adult_confirmed: adult, non_sensitive_confirmed: nonSensitive});
      onChange(next); setOpen(false); if (enabled) onEnabled?.();
    } catch (e) {
      setError((e as Error).message);
      // Refresh stale revisions without automatically retrying or granting anything.
      api<AiPermission>("/privacy/ai-permission", token).then(onChange).catch(() => {});
    } finally {setBusy(false);}
  }
  return <div className="ai-privacy-controls">
    <p className="small muted"><ShieldCheck size={14} className="inline-icon"/> {value?.enabled ? t.on : t.off}</p>
    <div className="copilot-actions"><button type="button" className="button secondary" disabled={!value || busy} onClick={edit}>{t.manage}</button>{value?.enabled && <button type="button" className="text-link" disabled={busy} onClick={() => save(false)}>{t.revoke}</button>}<Link className="text-link" href="/privacy">{t.policy} ↗</Link></div>
    {!open && <ErrorBox message={error}/>}
    <dialog ref={ref} className="privacy-dialog" aria-labelledby="ai-privacy-title" onCancel={e => {if (busy) e.preventDefault(); else setOpen(false);}}>
      <form className="form-stack" onSubmit={e => {e.preventDefault(); save(true);}}>
        <h2 id="ai-privacy-title" tabIndex={-1}>{t.title}</h2><p>{t.purpose}</p><p className="privacy-important">{value?.data_mode === "PAID_PRIVATE" ? t.paid : t.demo}</p>
        <p className="small">{t.scope}</p>
        <fieldset disabled={busy} className="privacy-scopes"><legend>{t.title}</legend>{(["history", "documents", "finance", "insurance"] as const).map(scope => <label key={scope} className="privacy-check"><input type="checkbox" disabled={!value?.allowed_scopes.includes(scope)} checked={scopes.includes(scope)} onChange={e => setScopes(items => e.target.checked ? [...items, scope] : items.filter(item => item !== scope))}/><span>{t[scope]}</span></label>)}</fieldset>
        {value?.data_mode === "DEMO_ONLY" && <p className="small muted">{t.docDemo}</p>}<p className="small">{t.excluded}</p>
        <label className="privacy-check"><input type="checkbox" checked={adult} onChange={e => setAdult(e.target.checked)} disabled={busy}/><span>{t.adult}</span></label>
        <label className="privacy-check"><input type="checkbox" checked={nonSensitive} onChange={e => setNonSensitive(e.target.checked)} disabled={busy}/><span>{t.nonSensitive}</span></label>
        <label className="privacy-check"><input type="checkbox" checked={ack} onChange={e => setAck(e.target.checked)} disabled={busy}/><span>{t.ack}</span></label>
        <p className="small muted">{t.revokeNote}</p><a className="text-link" href="https://ai.google.dev/gemini-api/terms" target="_blank" rel="noreferrer">{t.terms} ↗</a><ErrorBox message={error}/>
        {value?.notice_version !== AI_PRIVACY_NOTICE_VERSION && <p role="alert">{t.noticeChanged}</p>}
        <div className="copilot-actions"><button className="button primary" disabled={busy || !ack || !adult || !nonSensitive || value?.notice_version !== AI_PRIVACY_NOTICE_VERSION}>{busy ? t.saving : t.enable}</button><button className="button secondary" type="button" disabled={busy} onClick={() => setOpen(false)}>{t.cancel}</button></div>
      </form>
    </dialog>
  </div>;
}

export function UploadPrivacyNotice() {
  const {locale} = useI18n(); const t = privacyText(locale);
  return <p className="small muted upload-privacy"><ShieldCheck size={14} className="inline-icon"/> {t.upload} <Link className="text-link" href="/privacy">{t.policy} ↗</Link></p>;
}
