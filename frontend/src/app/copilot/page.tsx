"use client";
import {InsuranceEntry} from "@/components/insurance-entry";
import {useEffect, useState} from "react";
import Link from "next/link";
import {ArrowRight, MessageCircle, Send, ShieldCheck, Sparkles, Trash2} from "lucide-react";
import {tr} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";
import {api, documentKinds} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {Heading, ErrorBox} from "@/components/ui";
import {ContextHelp} from "@/components/user-guide";

type Reply = {
  answer: string; intent: string; notice: string; method: string;
  provider?: "GEMINI" | "RULES"; model?: string; fallback_reason?: string;
  actions: {title: string; href: string}[]; executed_actions: string[];
  citations: {title: string; href?: string; url?: string; excerpt?: string; filename?: string; page?: number; source_id?: string; document_kind?: string}[];
};
type Availability = {gemini_configured: boolean; model: string | null};
type Turn = {question: string; reply: Reply};
const reasons: Record<string, string> = {
  NOT_CONFIGURED: "Gemini chưa được cấu hình. Đang dùng tra cứu trực tiếp.",
  TIMEOUT: "Gemini phản hồi chậm. Đang dùng tra cứu trực tiếp.",
  PROVIDER_RATE_LIMIT: "Gemini đã chạm giới hạn lượt gọi. Đang dùng tra cứu trực tiếp.",
  AUTH_ERROR: "Khóa Gemini chưa được nhà cung cấp chấp nhận. Đang dùng tra cứu trực tiếp.",
  READ_ONLY_GUARD: "Thao tác tài chính cần bạn tự kiểm tra và xác nhận trong ứng dụng.",
};
const prompts = ["30 ngày tới tôi có đủ tiền không?", "Hóa đơn nào sắp đến hạn?", "Tỷ giá CNY/VND ảnh hưởng thế nào?", "Hồ sơ bồi thường gồm những gì?"];

export default function CopilotPage() {
  const {locale} = useI18n();
  const {token} = useAuth();
  const [availability, setAvailability] = useState<Availability>();
  const [useGemini, setUseGemini] = useState(false);
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api<Availability>("/finance/assistant/status", token).then(value => {
      if (active) {setAvailability(value); setUseGemini(value.gemini_configured);}
    }).catch(() => {if (active) {setAvailability({gemini_configured: false, model: null}); setUseGemini(false);}});
    return () => {active = false;};
  }, [token]);

  async function ask(question: string) {
    if (busy || !availability || question.trim().length < 2) return;
    setBusy(true); setError(""); setMessage(question);
    const recent = history.slice(-3).flatMap(turn => [
      {role: "user", content: turn.question}, {role: "assistant", content: turn.reply.answer.slice(0, 4000)},
    ]);
    try {
      const reply = await api<Reply>("/finance/assistant", token, {message: question, use_gemini: useGemini, language: locale, history: useGemini ? recent : []});
      setHistory(items => [...items, {question, reply}]); setMessage("");
    } catch (e) {setError((e as Error).message);} finally {setBusy(false);}
  }

  return <>
    <InsuranceEntry/>
    <Heading eyebrow={tr("CHỨNG TỪ · NGÂN SÁCH · TỶ GIÁ")} title={tr("Trợ lý du học")}>
      {tr("Hỏi về kế hoạch tiền, hóa đơn đến hạn hoặc tài liệu bảo hiểm. Mỗi kết quả có dữ liệu để bạn kiểm tra.")}
    </Heading>
    <ContextHelp title={tr("Trợ lý có thể tự làm gì?")}>
      <p>{tr("Gemini diễn giải dữ liệu tài khoản và đoạn tài liệu liên quan, có thể hiểu câu hỏi nối tiếp. Tra cứu trực tiếp dùng quy tắc của ứng dụng và không gọi AI bên ngoài.")}</p>
      <p>{tr("Trợ lý không tự ghi thu/chi, sửa hóa đơn, đổi tiền, thanh toán hoặc xác nhận giao dịch. Các nút bên dưới chỉ mở màn hình để bạn kiểm tra và tự thao tác.")}</p>
    </ContextHelp>
    <ErrorBox message={error}/>
    <section className="card copilot-card">
      <div className="copilot-toolbar">
        <div className="prompt-chips" role="group" aria-label={tr("Chế độ trả lời")}>
          <button type="button" aria-pressed={useGemini} disabled={busy || !availability?.gemini_configured} onClick={() => setUseGemini(true)}><Sparkles size={15}/> Gemini AI</button>
          <button type="button" aria-pressed={!useGemini} disabled={busy || !availability} onClick={() => setUseGemini(false)}>{tr("Tra cứu trực tiếp")}</button>
        </div>
        <button type="button" className="text-link" disabled={busy || !history.length} onClick={() => {setHistory([]); setError("");}}><Trash2 size={15}/> {tr("Xóa cuộc trò chuyện")}</button>
      </div>
      <p className="small muted copilot-privacy">
        {!availability ? tr("Đang kiểm tra kết nối trợ lý…") : useGemini
          ? <>{availability.model} · {tr("Khi gửi, câu hỏi, 3 lượt hội thoại gần nhất và dữ liệu/tài liệu liên quan được gửi tới Google Gemini. Không gửi tệp gốc. Dùng dữ liệu mẫu hoặc đã ẩn danh; nội dung nhạy cảm nên chọn Tra cứu trực tiếp. Hãy kiểm tra nguồn trước khi sử dụng câu trả lời.")}</>
          : tr("Tra cứu trực tiếp dùng dữ liệu đã lưu và quy tắc. Nội dung câu hỏi không được gửi tới Gemini.")}
        {availability && !availability.gemini_configured && <> {tr("Gemini chưa được cấu hình. Đang dùng tra cứu trực tiếp.")}</>}
      </p>
      {!history.length && <div className="copilot-intro"><MessageCircle size={30}/><h2>{tr("Bắt đầu với một việc cụ thể")}</h2><p>{tr("Chọn câu hỏi hoặc nhập nội dung của bạn. Nếu thiếu số dư hay tài liệu, trợ lý sẽ nói rõ cần bổ sung gì.")}</p></div>}
      <div className="prompt-chips">{prompts.map(question => <button type="button" key={question} disabled={busy || !availability} onClick={() => ask(question)}>{tr(question)}</button>)}</div>
      <div className="copilot-history" role="log" aria-label={tr("Cuộc trò chuyện")} aria-live="polite">
        {history.map((item, index) => <article key={index} className="copilot-turn">
          <div className="copilot-question">{item.question}</div>
          <div className="copilot-answer">
            <span className="badge reference">{item.reply.provider === "GEMINI" ? "Gemini AI" : tr("Tra cứu trực tiếp")}</span>
            {item.reply.provider === "GEMINI" && <span className="small muted"> · {tr(item.reply.citations.length ? "Có nguồn để đối chiếu" : "Giải thích tổng quát")}</span>}
            {item.reply.fallback_reason && <p className="copilot-fallback">{tr(reasons[item.reply.fallback_reason] || "Gemini tạm thời chưa trả lời được. Đang dùng tra cứu trực tiếp.")}</p>}
            <p className="copilot-answer-text">{item.reply.answer}</p>
            {item.reply.citations.map((source, i) => <div className="copilot-source" key={i}>
              {source.source_id && <span className="badge neutral">{source.source_id}</span>} {source.href ? <Link href={source.href}>{source.title} ↗</Link> : source.url ? <a href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a> : <strong>{source.title} · {tr("Trang")} {source.page}</strong>}
              {source.document_kind && <div><span className={`badge ${source.document_kind === "TEST_FIXTURE" ? "demo" : "reference"}`}>{documentKinds[source.document_kind] || source.document_kind}</span></div>}
              {source.excerpt && <blockquote>{source.excerpt}</blockquote>}{source.filename && <small>{source.filename}</small>}
            </div>)}
            <div className="copilot-actions">{item.reply.actions.map(action => <Link className="button secondary" href={action.href} key={action.href}>{action.title}<ArrowRight size={15}/></Link>)}</div>
            <p className="small muted"><ShieldCheck size={13} className="inline-icon"/> {tr(" Không có hành động tài chính nào được thực hiện.")}</p>
          </div>
        </article>)}
      </div>
      {busy && <p role="status">{tr(useGemini ? "Gemini đang đối chiếu dữ liệu và soạn câu trả lời…" : "Đang kiểm tra dữ liệu và nguồn…")}</p>}
      <form className="copilot-composer" onSubmit={event => {event.preventDefault(); ask(message);}}>
        <label className="sr-only" htmlFor="copilot-message">{tr("Câu hỏi cho trợ lý")}</label>
        <textarea id="copilot-message" required minLength={2} maxLength={500} rows={2} disabled={busy} value={message} onChange={e => setMessage(e.target.value)} placeholder={tr("Ví dụ: tháng tới tôi có đủ tiền trả tiền nhà không?")}/>
        <button className="button primary" disabled={busy || !availability || message.trim().length < 2}><Send size={17}/> {tr("Gửi câu hỏi")}</button>
      </form>
      <p className="small muted">{tr("Hội thoại chỉ giữ trong tab hiện tại; tải lại trang hoặc xóa cuộc trò chuyện sẽ làm mới ngữ cảnh.")}</p>
    </section>
  </>;
}
