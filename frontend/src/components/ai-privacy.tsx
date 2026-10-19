"use client";
import {useEffect, useRef, useState} from "react";
import Link from "next/link";
import {ShieldCheck} from "lucide-react";
import {api} from "@/lib/api";
import {AI_PRIVACY_NOTICE_VERSION, privacyText, type AiPermission} from "@/lib/privacy";
import {useI18n} from "./i18n-provider";
import {useAuth} from "./shell";
import {ErrorBox} from "./ui";

export function AiPrivacyControls({value, onChange, onEnabled, requested = false, onDismiss}: {value: AiPermission | undefined; onChange: (value: AiPermission) => void; onEnabled?: () => void; requested?: boolean; onDismiss?: () => void}) {
  const {token} = useAuth(); const {locale} = useI18n(); const t = privacyText(locale);
  const ref = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const visible = open || requested;
  function close() {setOpen(false); setError(""); onDismiss?.();}
  useEffect(() => {
    if (visible && ref.current) {
      ref.current.showModal();
      ref.current.querySelector<HTMLElement>("h2")?.focus({preventScroll: true});
      ref.current.scrollTop = 0;
    } else ref.current?.close();
  }, [visible]);
  function edit() {setError(""); setOpen(true);}
  async function save(enabled: boolean) {
    if (!value || busy) return;
    setBusy(true); setError("");
    try {
      const next = await api<AiPermission>("/privacy/ai-permission", token, {revision: value.revision, notice_version: enabled ? AI_PRIVACY_NOTICE_VERSION : value.notice_version, enabled, ...(enabled ? {preset: "SAMPLE_ASSISTANT"} : {})});
      onChange(next); close(); if (enabled) onEnabled?.();
    } catch (e) {
      setError((e as Error).message);
      // Refresh stale revisions without automatically retrying or granting anything.
      api<AiPermission>("/privacy/ai-permission", token).then(onChange).catch(() => {});
    } finally {setBusy(false);}
  }
  return <div className="ai-privacy-controls">
    <p className="small muted"><ShieldCheck size={14} className="inline-icon"/> {value?.enabled ? t.on : t.off}</p>
    <div className="copilot-actions"><button type="button" className="button secondary" disabled={!value || busy} onClick={edit}>{t.manage}</button>{value?.enabled && <button type="button" className="text-link" disabled={busy} onClick={() => save(false)}>{t.revoke}</button>}<Link className="text-link" href="/privacy">{t.policy} ↗</Link></div>
    {!visible && <ErrorBox message={error}/>}
    <dialog ref={ref} className="privacy-dialog" aria-labelledby="ai-privacy-title" onCancel={e => {if (busy) e.preventDefault(); else close();}}>
      <form className="form-stack" onSubmit={e => {e.preventDefault(); save(true);}}>
        <h2 id="ai-privacy-title" tabIndex={-1}>{t.title}</h2><p>{t.purpose}</p><p className="privacy-important">{value?.data_mode === "PAID_PRIVATE" ? t.paid : t.demo}</p>
        <p className="small">{t.adult} {t.nonSensitive}</p>
        <a className="text-link" href="/privacy#gemini" target="_blank" rel="noreferrer">{t.details} ↗</a><ErrorBox message={error}/>
        {value?.notice_version !== AI_PRIVACY_NOTICE_VERSION && <p role="alert">{t.noticeChanged}</p>}
        <div className="copilot-actions"><button className="button secondary" type="button" disabled={busy} onClick={() => value?.enabled ? save(false) : close()}>{t.cancel}</button><button className="button primary" disabled={!value || busy || value.notice_version !== AI_PRIVACY_NOTICE_VERSION}>{busy ? t.saving : t.enable}</button></div>
      </form>
    </dialog>
  </div>;
}

export function UploadPrivacyNotice() {
  const {locale} = useI18n(); const t = privacyText(locale);
  return <p className="small muted upload-privacy"><ShieldCheck size={14} className="inline-icon"/> {t.upload} <Link className="text-link" href="/privacy">{t.policy} ↗</Link></p>;
}
