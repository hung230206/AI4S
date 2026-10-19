"use client";
import {useEffect, useRef, useState} from "react";
import Link from "next/link";
import {ArrowRight, MessageCircle, Send, ShieldCheck, Trash2} from "lucide-react";
import {tr} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";
import {api, documentKinds} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {Heading, ErrorBox} from "@/components/ui";
import {ContextHelp} from "@/components/user-guide";
import {AiPrivacyControls} from "@/components/ai-privacy";
import {studyAssistantText} from "@/lib/study-assistant";
import {ragText, type RagDocument} from "@/lib/rag";
import {privacyText, type AiPermission} from "@/lib/privacy";

type Reply = {
  answer: string; intent: string; notice: string; method: string;
  route?: "RAG" | "GEMINI" | "WORKFLOW"; status?: string; provider?: "GEMINI" | "RULES" | "EXTRACTIVE"; model?: string; fallback_reason?: string;
  actions: {title: string; href: string}[]; executed_actions: string[];
  citations: {title: string; href?: string; url?: string; excerpt?: string; filename?: string; page?: number; source_id?: string; document_kind?: string}[];
};
type Availability = {gemini_configured: boolean; model: string | null};
type Turn = {question: string; reply: Reply; privacyRevision?: number};
const reasons: Record<string, string> = {
  NOT_CONFIGURED: "Gemini chưa được cấu hình. Đang dùng tra cứu trực tiếp.",
  TIMEOUT: "Gemini phản hồi chậm. Đang dùng tra cứu trực tiếp.",
  PROVIDER_RATE_LIMIT: "Gemini đã chạm giới hạn lượt gọi. Đang dùng tra cứu trực tiếp.",
  AUTH_ERROR: "Khóa Gemini chưa được nhà cung cấp chấp nhận. Đang dùng tra cứu trực tiếp.",
  READ_ONLY_GUARD: "Thao tác tài chính cần bạn tự kiểm tra và xác nhận trong ứng dụng.",
  ACCOUNT_LOCAL_ONLY: "Dữ liệu tài khoản được xử lý tại máy chủ theo quyền hiện tại.",
  LOCAL_ONLY: "Câu trả lời được xử lý tại máy chủ; chưa gửi tới Gemini.",
  SOURCES_CHANGED: "Tài liệu đã thay đổi hoặc được gỡ. Hãy hỏi lại để dùng nguồn mới.",
};
const prompts = ["30 ngày tới tôi có đủ tiền không?", "Hóa đơn nào sắp đến hạn?", "Tỷ giá CNY/VND ảnh hưởng thế nào?", "Hồ sơ bồi thường gồm những gì?"];

export default function CopilotPage() {
  const {locale} = useI18n();
  const privacy = privacyText(locale); const t = studyAssistantText(locale); const rt = ragText(locale);
  const {token, user} = useAuth();
  const [docs, setDocs] = useState<RagDocument[]>([]);
  const pending = useRef<{question: string; preview: boolean} | null>(null);
  const [cancelled, setCancelled] = useState(false);
  const [availability, setAvailability] = useState<Availability>();
  const [permissionRequested, setPermissionRequested] = useState(false);
  const [permission, setPermission] = useState<AiPermission>();
  const useGemini = Boolean(availability?.gemini_configured && permission?.enabled);
  const [preview, setPreview] = useState<unknown>();
  const inFlight = useRef(false);
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api<{items: RagDocument[]}>("/rag/documents", token).then(value => {if (active) setDocs(value.items);}).catch(() => {});
    api<Availability>("/finance/assistant/status", token).then(value => {
      if (active) {setAvailability(value);}
    }).catch(() => {if (active) {setAvailability({gemini_configured: false, model: null});}});
    return () => {active = false;};
  }, [token]);
  useEffect(() => {
    if (!permission?.enabled || !permission.expires_at) return;
    const timer = setTimeout(() => {setPermission(value => value ? {...value, enabled: false, scopes: []} : value); setPreview(undefined);}, Math.max(0, new Date(permission.expires_at).getTime() - Date.now()));
    return () => clearTimeout(timer);
  }, [permission]);
  useEffect(() => {
    let active = true;
    const refresh = () => api<AiPermission>("/privacy/ai-permission", token).then(value => {if (active) {setPermission(value);}}).catch(() => {if (active) {setPermission(undefined);}});
    refresh(); window.addEventListener("focus", refresh);
    return () => {active = false; window.removeEventListener("focus", refresh);};
  }, [token]);

  function chatBody(question: string, consent = permission) {
    const recent = history.filter(turn => turn.reply.provider === "GEMINI" && turn.privacyRevision === consent?.revision).slice(-3).flatMap(turn => [
      {role: "user", content: turn.question}, {role: "assistant", content: turn.reply.answer.slice(0, 4000)},
    ]);
    return {message: question, use_gemini: Boolean(availability?.gemini_configured && consent?.enabled), language: locale,
      privacy_revision: consent?.enabled ? consent.revision : undefined,
      history: consent?.enabled && consent.scopes.includes("history") ? recent : []};
  }

  async function ask(question: string, consent = permission, previewOnly = false) {
    if (inFlight.current || !availability || !consent || question.trim().length < 2) return;
    setMessage(question); setCancelled(false);
    if (availability.gemini_configured && (!consent.enabled || !consent.scopes.includes("documents"))) {
      pending.current = {question, preview: previewOnly}; setPermissionRequested(true); return;
    }
    inFlight.current = true; setBusy(true); setError(""); setPreview(undefined);
    try {
      if (previewOnly) setPreview(await api("/study-assistant/preview", token, chatBody(question, consent)));
      else {
        const reply = await api<Reply>("/study-assistant/chat", token, chatBody(question, consent));
        setHistory(items => [...items, {question, reply, privacyRevision: consent.enabled ? consent.revision : undefined}]); setMessage("");
      }
    } catch (e) {setError((e as Error).message);} finally {inFlight.current = false; setBusy(false);}
  }

  return <>
    <Heading eyebrow={tr("CHỨNG TỪ · NGÂN SÁCH · TỶ GIÁ")} title={tr("Trợ lý du học")}>
      {t.intro}
    </Heading>
    <ContextHelp title={tr("Trợ lý có thể tự làm gì?")}>
      <p>{privacy.purpose}</p>
      <p>{tr("Trợ lý không tự ghi thu/chi, sửa hóa đơn, đổi tiền, thanh toán hoặc xác nhận giao dịch. Các nút bên dưới chỉ mở màn hình để bạn kiểm tra và tự thao tác.")}</p>
    </ContextHelp>
    <ErrorBox message={error}/>
    <section className="card copilot-card">
      <div className="copilot-toolbar">
        <span className="small muted">{t.automatic}</span>
        <button type="button" className="text-link" disabled={busy || !history.length} onClick={() => {setHistory([]); setError("");}}><Trash2 size={15}/> {tr("Xóa cuộc trò chuyện")}</button>
      </div>
      <AiPrivacyControls requested={permissionRequested} continuation={permissionRequested ? t.pending : undefined} onDismiss={() => {setPermissionRequested(false); if (pending.current) {pending.current = null; setCancelled(true);}}} value={permission} onChange={next => {setPermission(next); setHistory([]); setPreview(undefined);}} onEnabled={next => {const task = pending.current; pending.current = null; if (task) void ask(task.question, next, task.preview);}}/>
      {cancelled && <p className="info-note" role="status">{t.noSend}</p>}
      <p className="small muted copilot-privacy">
        {!availability ? tr("Đang kiểm tra kết nối trợ lý…") : useGemini
          ? <>{availability.model} · Google Gemini · {permission?.scopes.length ? permission.scopes.map(scope => privacy[scope as "history" | "documents" | "finance" | "insurance"]).join(" · ") : privacy.questionOnly}</>
          : tr("Tra cứu trực tiếp dùng dữ liệu đã lưu và quy tắc. Nội dung câu hỏi không được gửi tới Gemini.")}
        {availability && !availability.gemini_configured && <> {tr("Gemini chưa được cấu hình. Đang dùng tra cứu trực tiếp.")}</>}
      </p>
      {!history.length && <div className="copilot-intro"><MessageCircle size={30}/><h2>{tr("Bắt đầu với một việc cụ thể")}</h2><p>{tr("Chọn câu hỏi hoặc nhập nội dung của bạn. Nếu thiếu số dư hay tài liệu, trợ lý sẽ nói rõ cần bổ sung gì.")}</p></div>}
      <div className="prompt-chips">{[t.prompt, ...prompts].map(question => <button type="button" key={question} disabled={busy || !availability || !permission} onClick={() => ask(question)}>{tr(question)}</button>)}</div>
      <div className="copilot-history" role="log" aria-label={tr("Cuộc trò chuyện")} aria-live="polite">
        {history.map((item, index) => <article key={index} className="copilot-turn">
          <div className="copilot-question">{item.question}</div>
          <div className="copilot-answer">
            <span className="badge reference">{item.reply.provider === "GEMINI" ? (item.reply.route === "RAG" ? t.rag : t.direct) : t.local}</span>
            {item.reply.provider === "GEMINI" && <span className="small muted"> · {tr(item.reply.citations.length ? "Có nguồn để đối chiếu" : "Giải thích tổng quát")}</span>}
            {item.reply.fallback_reason && <p className="copilot-fallback">{tr(reasons[item.reply.fallback_reason] || "Gemini tạm thời chưa trả lời được. Đang dùng tra cứu trực tiếp.")}</p>}
            <p className="copilot-answer-text">{item.reply.answer}</p>
            {item.reply.citations.map((source, i) => <div className="copilot-source" key={i}>
              {source.source_id && <span className="badge neutral">{source.source_id}</span>} {source.href ? <Link href={source.href}>{source.title} ↗</Link> : source.url ? <a href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a> : <strong>{source.title} · {tr("Trang")} {source.page}</strong>}
              {source.document_kind && <div><span className={`badge ${source.document_kind === "TEST_FIXTURE" ? "demo" : "reference"}`}>{documentKinds[source.document_kind] || source.document_kind}</span></div>}
              {source.href && source.page && <small>{tr("Trang")} {source.page}</small>}
              {source.excerpt && <blockquote>{source.excerpt}</blockquote>}{source.filename && <small>{source.filename}</small>}
            </div>)}
            <div className="copilot-actions">{item.reply.actions.map(action => <Link className="button secondary" href={action.href} key={action.href}>{action.title}<ArrowRight size={15}/></Link>)}</div>
            <p className="small muted"><ShieldCheck size={13} className="inline-icon"/> {tr(" Không có hành động tài chính nào được thực hiện.")}</p>
          </div>
        </article>)}
      </div>
      {busy && <p role="status">{t.working}</p>}
      <form className="copilot-composer" onSubmit={event => {event.preventDefault(); ask(message);}}>
        <label className="sr-only" htmlFor="copilot-message">{tr("Câu hỏi cho trợ lý")}</label>
        <textarea id="copilot-message" required minLength={2} maxLength={500} rows={2} disabled={busy} value={message} onChange={e => {setMessage(e.target.value); setPreview(undefined);}} onKeyDown={e => {
          if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing && e.nativeEvent.keyCode !== 229) {
            e.preventDefault(); if (!e.repeat) e.currentTarget.form?.requestSubmit();
          }
        }} aria-describedby="chat-keyboard-help" placeholder={tr("Ví dụ: tháng tới tôi có đủ tiền trả tiền nhà không?")}/>
        <button className="button primary" disabled={busy || !availability || !permission || message.trim().length < 2}><Send size={17}/> {tr("Gửi câu hỏi")}</button>
      </form>
      <p className="small muted" id="chat-keyboard-help">{privacy.keyboard}</p>
      {useGemini && <button type="button" className="text-link" disabled={busy || message.trim().length < 2} onClick={() => ask(message, permission, true)}>{privacy.preview}</button>}
      {preview !== undefined && <details className="privacy-preview" open><summary>{privacy.previewTitle}</summary><p className="small muted">{privacy.previewNote}</p><pre>{JSON.stringify(preview, null, 2)}</pre></details>}
      <p className="small muted">{tr("Hội thoại chỉ giữ trong tab hiện tại; tải lại trang hoặc xóa cuộc trò chuyện sẽ làm mới ngữ cảnh.")}</p>
    </section>
    <details className="card detail-card rag-library"><summary>{t.sources} ({docs.length})</summary>
      {user?.is_rag_admin && <p><Link className="button secondary" href="/admin/rag">{t.admin} →</Link></p>}
      {docs.map(doc => <article key={doc.id}><h3><Link href={`/knowledge/${doc.id}?revision=${doc.revision}`}>{doc.title} ↗</Link></h3><p className="small muted">{doc.publisher} · {doc.page_count} {rt.page}</p></article>)}
    </details>
  </>;
}
