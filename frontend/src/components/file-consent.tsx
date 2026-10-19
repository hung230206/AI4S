"use client";
import {useEffect, useRef, useState} from "react";
import {useI18n} from "./i18n-provider";
import {fileNotice, privacyText} from "@/lib/privacy";
import type {ConsentRequest} from "@/lib/file-consent";

export function FileConsentDialog() {
  const {locale} = useI18n(); const t = privacyText(locale);
  const [request, setRequest] = useState<ConsentRequest>();
  const pending = useRef<ConsentRequest | undefined>(undefined);
  const dialog = useRef<HTMLDialogElement>(null);
  function finish(accepted: boolean) {pending.current?.resolve(accepted); pending.current = undefined; setRequest(undefined);}
  useEffect(() => {
    const receive = (event: Event) => {
      const next = (event as CustomEvent<ConsentRequest>).detail;
      if (pending.current) {next.resolve(false); return;}
      pending.current = next; setRequest(next);
    };
    window.addEventListener("demo:file-consent", receive);
    return () => {window.removeEventListener("demo:file-consent", receive); pending.current?.resolve(false); pending.current = undefined;};
  }, []);
  useEffect(() => {
    if (request) {dialog.current?.showModal(); dialog.current?.querySelector<HTMLElement>("h2")?.focus();}
    else dialog.current?.close();
  }, [request]);
  const notice = request ? fileNotice(locale, request.purpose) : undefined;
  return <dialog ref={dialog} className="privacy-dialog" aria-labelledby="file-consent-title" aria-describedby="file-consent-summary" onCancel={() => finish(false)}>
    {notice && <div className="form-stack"><h2 id="file-consent-title" tabIndex={-1}>{notice.title}</h2><p id="file-consent-summary">{notice.summary}</p><p className="small muted">{notice.limit}</p>
      <a className="text-link" href={`/privacy#${request?.purpose}`} target="_blank" rel="noreferrer">{t.details} ↗</a>
      <div className="copilot-actions"><button type="button" className="button secondary" onClick={() => finish(false)}>{t.cancel}</button><button type="button" className="button primary" onClick={() => finish(true)}>{t.enable}</button></div>
    </div>}
  </dialog>;
}
