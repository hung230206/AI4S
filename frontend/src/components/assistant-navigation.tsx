"use client";
import {useEffect, useId, useRef} from "react";
import {useI18n} from "./i18n-provider";
import {type NavigationProposal} from "@/lib/assistant-navigation";

const copy = {
  vi: {title: "Chuyển trang?", cancel: "Ở lại", confirm: "Mở trang"},
  en: {title: "Open this page?", cancel: "Stay here", confirm: "Open page"},
  zh: {title: "打开此页面？", cancel: "留在此处", confirm: "打开页面"},
};

export function AssistantNavigation({proposal, onCancel, onConfirm}: {proposal: NavigationProposal | null; onCancel: () => void; onConfirm: () => void}) {
  const {locale} = useI18n(); const t = copy[locale]; const id = useId();
  const ref = useRef<HTMLDialogElement>(null); const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (proposal) {ref.current?.showModal(); cancel.current?.focus({preventScroll: true});}
    else ref.current?.close();
  }, [proposal]);
  return <dialog ref={ref} className="privacy-dialog assistant-navigation-dialog" aria-labelledby={id} aria-describedby={`${id}-reason`} onCancel={event => {event.preventDefault(); onCancel();}}>
    <div className="form-stack">
      <h2 id={id}>{t.title}</h2>
      <strong>{proposal?.title}</strong><p id={`${id}-reason`}>{proposal?.reason}</p>
      <div className="copilot-actions"><button ref={cancel} type="button" className="button secondary" onClick={onCancel}>{t.cancel}</button><button type="button" className="button primary" onClick={onConfirm}>{t.confirm}</button></div>
    </div>
  </dialog>;
}
