"use client";
import {requestFileConsent, fileConsentHeader} from "@/lib/file-consent";
import {tr, localized} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";

import {useEffect, useRef, useState} from "react";
import Link from "next/link";
import {FileScan, Upload, CheckCircle2} from "lucide-react";
import {api, API, authHeaders} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {ErrorBox} from "@/components/ui";

export type InvoiceDraft = {id: string; filename: string; method: string; status?: string; error_code?: string; invoice_id: string | null; pages: {page: number; text: string; confidence?: number}[]; suggestions: {document_type?: string; fee_type?: string | null; fields: Record<string, {value: string; page: number; source_line: string}>; currency: string | null; warnings: string[]}};
const fieldNames: Record<string, string> = localized({invoice_number: "Mã hóa đơn", institution_name: "Đơn vị phát hành", beneficiary_name: "Bên nhận", amount_cny: "Số tiền CNY", due_date: "Hạn thanh toán"});

export function InvoiceImportBox({onApply, onReset}: {onApply: (draft: InvoiceDraft) => void; onReset?: () => void}) {
  useI18n();
  const {token, user} = useAuth(); const [language, setLanguage] = useState("auto"); const [file, setFile] = useState<File>(); const [draft, setDraft] = useState<InvoiceDraft>(); const [uploading, setBusy] = useState(false); const [error, setError] = useState("");
  const [job, setJob] = useState(""); const [processing, setProcessing] = useState("");
  const busy = uploading || Boolean(job);
  const special = Boolean(draft?.suggestions.document_type && draft.suggestions.document_type !== "INVOICE_OR_NOTICE") || draft?.suggestions.currency === "VND";
  const apply = useRef(onApply); useEffect(() => {apply.current = onApply;}, [onApply]);
  const storageKey = `demo.ocr-job:${user?.id || ""}`;
  useEffect(() => {const frame = requestAnimationFrame(() => {try {const saved = sessionStorage.getItem(storageKey); if (saved) {setJob(saved); setBusy(true);}} catch {}}); return () => cancelAnimationFrame(frame);}, [storageKey]);
  useEffect(() => {
    if (!job) return;
    let active = true; let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const value = await api<InvoiceDraft>(`/invoice-imports/${job}`, token);
        if (!active) return;
        if (["QUEUED", "RUNNING"].includes(value.status || "")) {setProcessing(value.status!); timer = setTimeout(poll, 1500); return;}
        try {sessionStorage.removeItem(storageKey);} catch {}
        setBusy(false); setJob(""); setProcessing("");
        if (value.status === "FAILED") throw new Error(value.error_code === "OCR_TIMEOUT" ? tr("Máy chủ chưa đọc xong trong thời gian cho phép. Chọn ngôn ngữ chính của tài liệu rồi thử lại; tệp gốc vẫn được giữ riêng trong tài khoản.") : tr("Tác vụ đọc tệp bị gián đoạn hoặc không đọc được chữ. Chọn lại tệp và thử lại."));
        setDraft(value); if (!value.invoice_id) apply.current(value);
      } catch (e) {if (active) {setError((e as Error).message); setBusy(false); setJob(""); try {sessionStorage.removeItem(storageKey);} catch {}}}
    }
    void poll(); return () => {active = false; clearTimeout(timer);};
  }, [job, token, storageKey]);
  async function extract() {
    if (!file) return; setBusy(true); setError("");
    try {
      if (!await requestFileConsent("invoice-ocr")) return;
      const body = new FormData(); body.append("file", file); body.append("language", language);
      const response = await fetch(`${API}/api/v1/invoice-imports/jobs`, {method: "POST", credentials: "include", headers: {...authHeaders(token), ...fileConsentHeader("invoice-ocr")}, body});
      const result = await response.json();
      if (!response.ok) {
        const errors: Record<string, string> = {OCR_NOT_READY: tr("Nhận dạng chữ chưa sẵn sàng trên máy chủ. Bạn vẫn có thể nhập tay."), OCR_BUSY: tr("Máy chủ đang đọc chứng từ khác. Hãy thử lại sau ít phút."), OCR_TIMEOUT: tr("Tệp mất quá lâu để đọc. Hãy dùng ít trang hơn hoặc ảnh rõ hơn."), OCR_FAILED: tr("Không đọc được ảnh. Hãy chụp rõ hơn hoặc nhập thông tin bằng tay."), DOCUMENT_INVALID: tr("Tệp bị lỗi hoặc không đúng định dạng. Hãy thử bản gốc hoặc ảnh khác."), DOCUMENT_NO_TEXT: tr("Chưa đọc được chữ trong tệp. Hãy dùng ảnh rõ hơn hoặc nhập tay."), DOCUMENT_TOO_LARGE: tr("Tệp vượt giới hạn 5 MB, 5 trang hoặc 16 megapixel."), DOCUMENT_TYPE_UNSUPPORTED: tr("Hãy dùng PNG, JPG, WebP, PDF, TXT hoặc MD.")};
        throw new Error(errors[result.error?.code] || result.error?.message || tr("Không đọc được tệp. Hãy thử ảnh rõ hơn hoặc nhập tay."));
      }
      if (["QUEUED", "RUNNING"].includes(result.status)) {setProcessing(result.status); setJob(result.id); try {sessionStorage.setItem(storageKey, result.id);} catch {} return;}
      setDraft(result); if (!result.invoice_id) onApply(result);
    } catch (e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  return <section className="card import-card" aria-labelledby="import-title"><div className="section-heading"><div><span className="eyebrow">{tr("TỰ ĐỘNG ĐỌC · BẠN KIỂM TRA")}</span><h2 id="import-title"><FileScan size={21}/> {tr(" Nhập từ ảnh hoặc PDF")}</h2></div><span className="badge reference">{tr("OCR CỤC BỘ")}</span></div><p>{tr("Chụp thông báo thu phí hoặc tải tệp lên. App gợi ý thông tin vào biểu mẫu bên dưới; bạn sửa và xác nhận trước khi lưu.")}</p><div className="import-actions"><label>{tr("Tệp hóa đơn")}<input type="file" disabled={busy} accept=".png,.jpg,.jpeg,.webp,.pdf,.txt,.md" onChange={e => {setFile(e.target.files?.[0]); setDraft(undefined); onReset?.(); setError("");}}/></label><label>{tr("Ngôn ngữ hóa đơn")}<select aria-label={tr("Ngôn ngữ hóa đơn")} value={language} disabled={busy} onChange={e => setLanguage(e.target.value)}><option value="auto">{tr("Trung / Việt / Anh")}</option><option value="zh">{tr("Tiếng Trung và Anh")}</option><option value="vi">{tr("Tiếng Việt và Anh")}</option><option value="en">{tr("Tiếng Anh")}</option></select></label><button className="button secondary" type="button" disabled={!file || busy} onClick={extract}><Upload size={16}/>{busy ? tr("Đang đọc chứng từ…") : tr("Đọc và điền thông tin")}</button></div><p className="small muted">{tr("PNG, JPG, WebP, PDF tối đa 5 trang, TXT hoặc MD; tối đa 5 MB. Chọn ngôn ngữ chính của tệp để nhận dạng tốt hơn. Tệp được xử lý tại máy chủ của app, không gửi tới dịch vụ OCR bên ngoài.")}</p><ErrorBox message={error}/>{busy && <p role="status">{processing === "QUEUED" ? tr("Đã nhận tệp, đang chờ lượt xử lý.") : tr("Đang đọc chữ tại máy chủ. Bạn có thể tải lại trang; tác vụ vẫn tiếp tục. Trên máy chủ demo có thể mất vài phút.")}</p>}{draft && <div className="import-result">{draft.invoice_id ? <p>{tr("Tệp này đã được lưu thành hóa đơn. ")}<Link className="text-link" href={`/invoices/${draft.invoice_id}`}>{tr("Mở hóa đơn hiện có")}</Link></p> : special ? <div className="info-note"><div><h3>{draft.suggestions.document_type === "CLAIM_FORM" ? tr("Đã nhận diện giấy yêu cầu bồi thường") : draft.suggestions.document_type !== "INVOICE_OR_NOTICE" ? tr("Chứng từ hồ sơ hoặc khoản đã chi") : tr("Tài liệu dùng VND, không phải khoản phải trả CNY")}</h3>{draft.suggestions.warnings.map(w => <p key={w}>{tr(w)}</p>)}{draft.suggestions.document_type !== "INVOICE_OR_NOTICE" && <Link className="button primary" href={draft.suggestions.document_type === "CLAIM_FORM" ? `/insurance?tab=claims&import=${draft.id}` : "/insurance?tab=claims"}>{tr("Đưa vào hồ sơ bồi thường")}</Link>}<button type="button" className="button secondary" onClick={() => {setDraft(undefined); onReset?.();}}>{tr("Nhập hóa đơn khác bằng tay")}</button></div></div> : <><div className="success-note"><CheckCircle2 size={17}/> {tr(" Đã gợi ý ")}{Object.keys(draft.suggestions.fields).filter(k => fieldNames[k]).length}{tr("/5 trường từ ")}{draft.filename}{tr(". Kiểm tra các trường còn thiếu trong biểu mẫu.")}</div><div className="extracted-fields">{Object.entries(draft.suggestions.fields).map(([key, value]) => <div key={key}><strong>{fieldNames[key] || key}</strong><span>{value.value}</span><small>{tr("Trang")} {value.page}: {value.source_line}</small></div>)}</div>{draft.suggestions.warnings.map(warning => <p className="small muted" key={warning}>{tr(warning)}</p>)}</>}<details className="context-help"><summary>{tr("Xem toàn văn đã đọc")}</summary><div>{draft.pages.map(page => <section key={page.page}><strong>{tr("Trang")} {page.page}</strong><pre className="policy-source">{page.text}</pre></section>)}</div></details></div>}</section>;
}
