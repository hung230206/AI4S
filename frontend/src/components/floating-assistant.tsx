"use client";
import {useCallback, useEffect, useId, useLayoutEffect, useRef, useState} from "react";
import {useRouter, useSearchParams} from "next/navigation";
import {ArrowUp, ChevronDown, Sparkles} from "lucide-react";
import {useAuth} from "./shell";
import {useI18n} from "./i18n-provider";
import {AiPrivacyControls} from "./ai-privacy";
import {api, documentKinds} from "@/lib/api";
import {AI_PRIVACY_NOTICE_VERSION, type AiPermission} from "@/lib/privacy";
import {safeNavigation, type NavigationProposal} from "@/lib/assistant-navigation";
import {AssistantNavigation} from "./assistant-navigation";

const copy = {
  vi: {title: "Trợ lý du học", launch: "Mở trợ lý du học", close: "Thu nhỏ trợ lý", hint: "Hỏi về du học, ngân sách, bảo hiểm…", welcome: "Bạn cần mình giúp gì về du học, ngân sách hoặc bảo hiểm?", question: "Câu hỏi cho trợ lý", send: "Gửi câu hỏi", working: "Đang trả lời…", sources: "Nguồn tham khảo", page: "Trang", keys: "Enter gửi · Shift+Enter xuống dòng", local: "Trợ lý chưa tạo được câu trả lời. Đây là kết quả tra cứu tại máy chủ.", changed: "Nguồn đã thay đổi. Hãy hỏi lại để lấy thông tin mới.", account: "Thông tin tài khoản được xử lý tại máy chủ theo quyền hiện tại."},
  en: {title: "Study-abroad assistant", launch: "Open study-abroad assistant", close: "Minimize assistant", hint: "Ask about study, budgets or insurance…", welcome: "How can I help with studying abroad, budgets or insurance?", question: "Question for the assistant", send: "Send question", working: "Preparing your answer…", sources: "Sources", page: "Page", keys: "Enter sends · Shift+Enter adds a line", local: "The assistant cannot generate an answer right now. This is a server-side lookup result.", changed: "A source changed. Ask again for current information.", account: "Account data is processed on the server under your current permissions."},
  zh: {title: "留学助手", launch: "打开留学助手", close: "收起助手", hint: "咨询留学、预算或保险…", welcome: "需要我帮助了解留学、预算或保险吗？", question: "向助手提问", send: "发送问题", working: "正在回答…", sources: "参考来源", page: "页", keys: "Enter 发送 · Shift+Enter 换行", local: "助手暂时无法生成回答，以下为服务器查询结果。", changed: "来源已更新，请重新提问。", account: "按当前权限在服务器处理账户数据。"},
};
type Citation = {source_id?: string; title: string; href?: string; url?: string; page?: number; excerpt?: string; document_kind?: string};
type Reply = {answer: string; provider: string; fallback_reason?: string; citations: Citation[]; actions: {title: string; href: string}[]; navigation?: NavigationProposal};
type Turn = {id: number; question: string; reply?: Reply; privacyRevision?: number};
type Availability = {gemini_configured: boolean};

export function FloatingAssistant() {
  const {token} = useAuth(); const {locale} = useI18n(); const t = copy[locale];
  const router = useRouter(); const [navigation, setNavigation] = useState<NavigationProposal | null>(null);
  const launchRequested = useSearchParams().get("assistant") === "open";
  const panelId = useId(); const inputId = useId();
  const [open, setOpen] = useState(false); const [opening, setOpening] = useState(false);
  const [requested, setRequested] = useState(false); const [permission, setPermission] = useState<AiPermission>();
  const [availability, setAvailability] = useState<Availability>();
  const [message, setMessage] = useState(""); const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const alive = useRef(true); const inFlight = useRef(false); const openingRef = useRef(false);
  const permissionRef = useRef<AiPermission | undefined>(undefined); const epoch = useRef(0);
  const sequence = useRef(0); const pending = useRef<string | null>(null);
  const dock = useRef<HTMLDivElement>(null); const scroller = useRef<HTMLDivElement>(null);
  const content = useRef<HTMLDivElement>(null); const input = useRef<HTMLTextAreaElement>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const invalidate = useCallback(() => {epoch.current++;}, []);

  const applyPermission = useCallback((next: AiPermission) => {
    if (!alive.current || (permissionRef.current && next.revision < permissionRef.current.revision)) return;
    const previous = permissionRef.current;
    if (previous && (previous.revision !== next.revision || (previous.enabled && !next.enabled))) {
      epoch.current++; setTurns([]); setNavigation(null);
      if (!next.enabled) setOpen(false);
    }
    permissionRef.current = next; setPermission(next);
  }, []);

  useEffect(() => {
    alive.current = true;
    const refresh = () => api<AiPermission>("/privacy/ai-permission", token).then(applyPermission).catch(() => {
      if (alive.current) {epoch.current++; setPermission(undefined); permissionRef.current = undefined; setOpen(false); setTurns([]); setNavigation(null);}
    });
    void refresh();
    api<Availability>("/finance/assistant/status", token).then(value => {if (alive.current) setAvailability(value);}).catch(() => {if (alive.current) setAvailability({gemini_configured: false});});
    window.addEventListener("focus", refresh); window.addEventListener("demo:ai-permission-changed", refresh);
    return () => {alive.current = false; invalidate(); window.removeEventListener("focus", refresh); window.removeEventListener("demo:ai-permission-changed", refresh);};
  }, [token, applyPermission, invalidate]);

  useEffect(() => {
    if (!permission?.enabled || !permission.expires_at) return;
    const timer = setTimeout(() => applyPermission({...permission, enabled: false, scopes: []}), Math.max(0, new Date(permission.expires_at).getTime() - Date.now()));
    return () => clearTimeout(timer);
  }, [permission, applyPermission]);

  const scrollToLatest = useCallback(() => {if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight;}, []);
  useLayoutEffect(scrollToLatest, [open, turns, busy, error, scrollToLatest]);
  useEffect(() => {
    if (!open || !content.current) return;
    const observer = new ResizeObserver(scrollToLatest); observer.observe(content.current);
    const frame = requestAnimationFrame(() => input.current?.focus({preventScroll: true}));
    return () => {observer.disconnect(); cancelAnimationFrame(frame);};
  }, [open, scrollToLatest]);
  useEffect(() => {
    const viewport = window.visualViewport;
    const resize = () => {
      dock.current?.style.setProperty("--assistant-viewport", `${viewport?.height || window.innerHeight}px`);
      dock.current?.style.setProperty("--assistant-keyboard", `${viewport ? Math.max(0, window.innerHeight - viewport.height - viewport.offsetTop) : 0}px`);
      scrollToLatest();
    };
    resize(); viewport?.addEventListener("resize", resize); viewport?.addEventListener("scroll", resize);
    return () => {viewport?.removeEventListener("resize", resize); viewport?.removeEventListener("scroll", resize);};
  }, [scrollToLatest]);

  const requestOpen = useCallback(async () => {
    if (openingRef.current) return;
    openingRef.current = true; setOpening(true); setError("");
    try {
      const next = await api<AiPermission>("/privacy/ai-permission", token);
      if (!alive.current) return;
      applyPermission(next);
      if (!next.enabled || !next.scopes.includes("documents") || next.notice_version !== AI_PRIVACY_NOTICE_VERSION) setRequested(true);
      else setOpen(true);
    } catch (e) {if (alive.current) {setOpen(true); setError((e as Error).message);}}
    finally {openingRef.current = false; if (alive.current) setOpening(false);}
  }, [token, applyPermission]);
  useEffect(() => {
    const launch = () => {void requestOpen();};
    window.addEventListener("demo:open-assistant", launch);
    // Old /copilot links still open the same global chat, via the homepage.
    if (launchRequested) {
      launch();
      const url = new URL(window.location.href); url.searchParams.delete("assistant");
      window.history.replaceState(null, "", url.pathname + url.search + url.hash);
    }
    return () => window.removeEventListener("demo:open-assistant", launch);
  }, [requestOpen, launchRequested]);

  function minimize() {setOpen(false); requestAnimationFrame(() => launcher.current?.focus({preventScroll: true}));}
  function cancelNavigation() {setNavigation(null); requestAnimationFrame(() => input.current?.focus({preventScroll: true}));}
  function confirmNavigation() {
    const target = safeNavigation(navigation); setNavigation(null);
    if (target && permissionRef.current?.enabled) {minimize(); router.push(target.href);}
  }

  async function ask(question: string, consent = permissionRef.current) {
    question = question.trim();
    if (inFlight.current || question.length < 2 || !consent || !availability) return;
    if (!consent.enabled || !consent.scopes.includes("documents") || consent.notice_version !== AI_PRIVACY_NOTICE_VERSION) {
      pending.current = question; setRequested(true); return;
    }
    inFlight.current = true; setBusy(true); setError(""); setMessage("");
    const requestEpoch = epoch.current; const id = ++sequence.current;
    let proposed = false;
    const history = consent.scopes.includes("history") ? turns.filter(turn => turn.reply?.provider === "GEMINI" && turn.privacyRevision === consent.revision).slice(-3).flatMap(turn => [{role: "user", content: turn.question}, {role: "assistant", content: turn.reply!.answer.slice(0, 4000)}]) : [];
    setTurns(items => [...items, {id, question, privacyRevision: consent.revision}]);
    try {
      const reply = await api<Reply>("/study-assistant/chat", token, {message: question, language: locale, use_gemini: availability.gemini_configured, privacy_revision: consent.revision, history});
      if (alive.current && epoch.current === requestEpoch) {
        setTurns(items => items.map(turn => turn.id === id ? {...turn, reply} : turn));
        const target = safeNavigation(reply.navigation);
        if (target) {proposed = true; setNavigation(target);}
      }
    } catch (e) {
      if (alive.current && epoch.current === requestEpoch) {setError((e as Error).message); setMessage(question); setTurns(items => items.filter(turn => turn.id !== id));}
    } finally {inFlight.current = false; if (alive.current) {setBusy(false); if (!proposed) requestAnimationFrame(() => input.current?.focus({preventScroll: true}));}}
  }

  return <>
    <AssistantNavigation proposal={navigation} onCancel={cancelNavigation} onConfirm={confirmNavigation}/>
    <AiPrivacyControls dialogOnly value={permission} requested={requested} onChange={applyPermission} onDismiss={() => {setRequested(false); pending.current = null;}} onEnabled={next => {
      setOpen(true); const question = pending.current; pending.current = null; if (question) void ask(question, next);
    }}/>
    <div className="floating-assistant" ref={dock}>
      {!open ? <button ref={launcher} type="button" className="assistant-launcher" aria-label={t.launch} aria-expanded={false} aria-controls={panelId} disabled={opening} onClick={() => void requestOpen()}><Sparkles size={20}/><span>{t.title}</span><span className="assistant-launcher-hint">{t.hint}</span><ArrowUp size={17}/></button> :
        <section className="floating-chat" id={panelId} role="region" aria-label={t.title} onKeyDown={event => {if (event.key === "Escape" && !event.nativeEvent.isComposing) {event.preventDefault(); minimize();}}}>
          <header className="floating-chat-header"><span><Sparkles size={18}/>{t.title}</span><button type="button" aria-label={t.close} onClick={minimize}><ChevronDown size={21}/></button></header>
          <div className="floating-chat-scroll" ref={scroller} role="log" aria-label={t.title} aria-live="polite" aria-busy={busy}>
            <div className="floating-chat-content" ref={content}>
              {!turns.length && <p className="assistant-welcome">{t.welcome}</p>}
              {turns.map(turn => <article className="assistant-turn" key={turn.id}>
                <p className="assistant-question">{turn.question}</p>
                {turn.reply && <div className="assistant-answer"><p>{turn.reply.answer}</p>
                  {turn.reply.fallback_reason && <p className="assistant-note">{turn.reply.fallback_reason === "SOURCES_CHANGED" ? t.changed : ["ACCOUNT_LOCAL_ONLY", "LOCAL_ONLY", "READ_ONLY_GUARD"].includes(turn.reply.fallback_reason) ? t.account : t.local}</p>}
                  {turn.reply.citations.length > 0 && <details className="assistant-sources"><summary>{t.sources} ({turn.reply.citations.length})</summary>{turn.reply.citations.map((source, index) => <div key={index}>
                    {source.href || source.url ? <a href={source.href || source.url} target="_blank" rel="noreferrer">{source.source_id && `[${source.source_id}] `}{source.title} ↗</a> : <strong>{source.title}</strong>}
                    {source.document_kind && documentKinds[source.document_kind] && <small>{documentKinds[source.document_kind]}</small>}
                    {source.page && <small>{t.page} {source.page}</small>}{source.excerpt && <blockquote>{source.excerpt}</blockquote>}
                  </div>)}</details>}
                  {turn.reply.actions.length > 0 && <div className="assistant-actions">{turn.reply.actions.map(action => {
                    const target = safeNavigation({href: action.href, title: action.title, reason: action.title});
                    return target && <button type="button" key={action.href} onClick={() => setNavigation(safeNavigation(turn.reply?.navigation) || target)}>{action.title} →</button>;
                  })}</div>}
                </div>}
              </article>)}
              {busy && <p className="assistant-typing" role="status"><span/><span/><span/>{t.working}</p>}
              {error && <p className="assistant-error" role="alert">{error}</p>}
            </div>
          </div>
          <form className="floating-chat-composer" onSubmit={event => {event.preventDefault(); void ask(message);}}>
            <label className="sr-only" htmlFor={inputId}>{t.question}</label>
            <textarea ref={input} id={inputId} rows={2} maxLength={500} required minLength={2} value={message} disabled={busy} placeholder={t.hint} onChange={event => setMessage(event.target.value)} onKeyDown={event => {
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing && event.nativeEvent.keyCode !== 229) {event.preventDefault(); if (!event.repeat) event.currentTarget.form?.requestSubmit();}
            }}/>
            <button type="submit" aria-label={t.send} disabled={busy || !availability || message.trim().length < 2}><ArrowUp size={21}/></button>
          </form>
          <p className="assistant-keyboard-hint">{t.keys}</p>
        </section>}
    </div>
  </>;
}
