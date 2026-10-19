"use client";
import {useEffect, useId, useRef, useState, useSyncExternalStore, type KeyboardEvent} from "react";
import {usePathname} from "next/navigation";
import {CircleHelp} from "lucide-react";
import {pageIntro, pageIntroId, pageIntroKey, hiddenIntrosKey} from "@/lib/page-intro";
import {preference, subscribePreferences, writePreference} from "@/lib/preferences";
import {useI18n} from "./i18n-provider";

const copy = {
  vi: {done: "Đã hiểu", hide: "Không hiện lại hướng dẫn này", setting: "Tự hiện hướng dẫn khi chuyển trang", help: "Ô trong popup chỉ ẩn hướng dẫn của trang đó. Cài đặt được lưu trên trình duyệt này.", title: "Hướng dẫn khi dùng ứng dụng", reset: "Hiện lại các hướng dẫn đã ẩn", restored: "Đã bật lại các hướng dẫn đã ẩn."},
  en: {done: "Got it", hide: "Don't show this introduction again", setting: "Show a short introduction on each page", help: "The popup checkbox hides only that page's introduction. Preferences are saved in this browser.", title: "Help while using the app", reset: "Restore hidden introductions", restored: "Hidden introductions have been restored."},
  zh: {done: "明白了", hide: "不再显示此页面简介", setting: "切换页面时自动显示简介", help: "弹窗中的选项仅隐藏当前页面的简介。设置保存在此浏览器中。", title: "使用应用时的帮助", reset: "恢复已隐藏的页面简介", restored: "已恢复隐藏的页面简介。"},
};
function useSaved(key: string, fallback: string) {return useSyncExternalStore(subscribePreferences, () => preference(key, fallback), () => fallback);}
function hiddenIds(value: string): string[] {
  try {const parsed: unknown = JSON.parse(value); return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === "string") : [];} catch {return [];}
}

export function PageIntro({userId}: {userId: string}) {
  const path = usePathname(); const {locale} = useI18n(); const t = copy[locale];
  const enabled = useSaved(pageIntroKey(userId), "on") !== "off";
  const hidden = useSaved(hiddenIntrosKey(userId), "[]"); const introId = pageIntroId(path);
  const isHidden = !!introId && hiddenIds(hidden).includes(introId); const text = pageIntro(path, locale);
  const dialog = useRef<HTMLDialogElement>(null); const hide = useRef<HTMLInputElement>(null); const done = useRef<HTMLButtonElement>(null); const id = useId();
  useEffect(() => {
    const element = dialog.current;
    if (!element || !pageIntroId(path)) return;
    let pending = enabled && !isHidden && new URLSearchParams(window.location.search).get("assistant") !== "open";
    const attempt = () => {
      if (!pending || document.querySelector("dialog[open]")) return;
      if (hide.current) hide.current.checked = false;
      element.showModal(); done.current?.focus(); pending = false;
    };
    const observer = new MutationObserver(attempt);
    observer.observe(document.body, {subtree: true, attributes: true, attributeFilter: ["open"]});
    const frame = requestAnimationFrame(attempt);
    return () => {pending = false; cancelAnimationFrame(frame); observer.disconnect(); element.close();};
  }, [path, userId, enabled, isHidden]);
  function keepFocus(event: KeyboardEvent<HTMLDialogElement>) {
    if (event.key !== "Tab") return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>("button, input"));
    const first = controls[0]; const last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last?.focus();}
    else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first?.focus();}
  }
  function close() {
    if (hide.current?.checked && introId) {
      const key = hiddenIntrosKey(userId);
      writePreference(key, JSON.stringify([...new Set([...hiddenIds(preference(key, "[]")), introId])]));
    }
    dialog.current?.close();
    const heading = document.querySelector<HTMLElement>("main h1");
    if (heading && !document.querySelector("dialog[open]")) {heading.setAttribute("tabindex", "-1"); heading.focus({preventScroll: true});}
  }
  return <dialog ref={dialog} className="page-intro-dialog" aria-labelledby={text ? id : undefined} aria-describedby={`${id}-text`} onKeyDown={keepFocus} onCancel={event => {event.preventDefault(); close();}}>
    <CircleHelp size={24} aria-hidden="true"/><h2 id={id}>{text?.[0]}</h2><p id={`${id}-text`}>{text?.[1]}</p>
    <label className="intro-setting"><input ref={hide} type="checkbox"/><span>{t.hide}</span></label>
    <button ref={done} type="button" className="button primary" autoFocus onClick={close}>{t.done}</button>
  </dialog>;
}

export function PageIntroSettings({userId}: {userId: string}) {
  const {locale} = useI18n(); const t = copy[locale]; const enabled = useSaved(pageIntroKey(userId), "on") !== "off"; const [restored, setRestored] = useState(false);
  return <section className="card detail-card"><h2>{t.title}</h2><label className="intro-setting"><input type="checkbox" checked={enabled} onChange={event => writePreference(pageIntroKey(userId), event.target.checked ? "on" : "off")}/><span>{t.setting}</span></label><p className="small muted">{t.help}</p><button className="button secondary" onClick={() => {writePreference(hiddenIntrosKey(userId), "[]"); setRestored(true);}}>{t.reset}</button>{restored && <p className="small success-note" role="status">{t.restored}</p>}</section>;
}
