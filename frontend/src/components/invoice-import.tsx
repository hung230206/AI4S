"use client";
import {requestFileConsent, fileConsentHeader} from "@/lib/file-consent";
import {tr, localized} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";

import {useState} from "react";
import Link from "next/link";
import {FileScan, Upload, CheckCircle2} from "lucide-react";
import {API, authHeaders} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {ErrorBox} from "@/components/ui";

export type InvoiceDraft = {id: string; filename: string; method: string; invoice_id: string | null; pages: {page: number; text: string; confidence?: number}[]; suggestions: {fields: Record<string, {value: string; page: number; source_line: string}>; currency: string | null; warnings: string[]}};
const fieldNames: Record<string, string> = localized({invoice_number: "Mã hóa đơn", institution_name: "Đơn vị phát hành", beneficiary_name: "Bên nhận", amount_cny: "Số tiền CNY", due_date: "Hạn thanh toán"});

export function InvoiceImportBox({onApply}: {onApply: (draft: InvoiceDraft) => void}) {
  useI18n();
  const {token} = useAuth(); const [language, setLanguage] = useState("auto"); const [file, setFile] = useState<File>(); const [draft, setDraft] = useState<InvoiceDraft>(); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  async function extract() {
    if (!file) return; setBusy(true); setError("");
    try {
      if (!await requestFileConsent("invoice-ocr")) return;
      const body = new FormData(); body.append("file", file); body.append("language", language);
      const response = await fetch(`${API}/api/v1/invoice-imports`, {method: "POST", credentials: "include", headers: {...authHeaders(token), ...fileConsentHeader("invoice-ocr")}, body});
      const result = await response.json();
      if (!response.ok) {
        const errors: Record<string, string> = {OCR_NOT_READY: tr("Nhận dạng chữ chưa sẵn sàng trên máy chủ. Bạn vẫn có thể nhập tay."), OCR_BUSY: tr("Máy chủ đang đọc chứng từ khác. Hãy thử lại sau ít phút."), OCR_TIMEOUT: tr("Tệp mất quá lâu để đọc. Hãy dùng ít trang hơn hoặc ảnh rõ hơn."), OCR_FAILED: tr("Không đọc được ảnh. Hãy chụp rõ hơn hoặc nhập thông tin bằng tay."), DOCUMENT_INVALID: tr("Tệp bị lỗi hoặc không đúng định dạng. Hãy thử bản gốc hoặc ảnh khác."), DOCUMENT_NO_TEXT: tr("Chưa đọc được chữ trong tệp. Hãy dùng ảnh rõ hơn hoặc nhập tay."), DOCUMENT_TOO_LARGE: tr("Tệp vượt giới hạn 5 MB, 5 trang hoặc 16 megapixel."), DOCUMENT_TYPE_UNSUPPORTED: tr("Hãy dùng PNG, JPG, WebP, PDF, TXT hoặc MD.")};
        throw new Error(errors[result.error?.code] || result.error?.message || tr("Không đọc được tệp. Hãy thử ảnh rõ hơn hoặc nhập tay."));
      }
      setDraft(result); if (!result.invoice_id) onApply(result);
    } catch (e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  return <section className="card import-card" aria-labelledby="import-title"><div className="section-heading"><div><span className="eyebrow">{tr("TỰ ĐỘNG ĐỌC · BẠN KIỂM TRA")}</span><h2 id="import-title"><FileScan size={21}/> {tr(" Nhập từ ảnh hoặc PDF")}</h2></div><span className="badge reference">{tr("OCR CỤC BỘ")}</span></div><p>{tr("Chụp thông báo thu phí hoặc tải tệp lên. App gợi ý thông tin vào biểu mẫu bên dưới; bạn sửa và xác nhận trước khi lưu.")}</p><div className="import-actions"><label>{tr("Tệp hóa đơn")}<input type="file" accept=".png,.jpg,.jpeg,.webp,.pdf,.txt,.md" onChange={e => {setFile(e.target.files?.[0]); setError("");}}/></label><label>{tr("Ngôn ngữ hóa đơn")}<select aria-label={tr("Ngôn ngữ hóa đơn")} value={language} onChange={e => setLanguage(e.target.value)}><option value="auto">{tr("Trung / Việt / Anh")}</option><option value="zh">{tr("Tiếng Trung và Anh")}</option><option value="vi">{tr("Tiếng Việt và Anh")}</option><option value="en">{tr("Tiếng Anh")}</option></select></label><button className="button secondary" type="button" disabled={!file || busy} onClick={extract}><Upload size={16}/>{busy ? tr("Đang đọc chứng từ…") : tr("Đọc và điền thông tin")}</button></div><p className="small muted">{tr("PNG, JPG, WebP, PDF tối đa 5 trang, TXT hoặc MD; tối đa 5 MB. Chọn ngôn ngữ chính của tệp để nhận dạng tốt hơn. Tệp được xử lý tại máy chủ của app, không gửi tới dịch vụ OCR bên ngoài.")}</p><ErrorBox message={error}/>{busy && <p role="status">{tr("Đang nhận dạng chữ. Với tài liệu quét, quá trình có thể mất vài chục giây.")}</p>}{draft && <div className="import-result">{draft.invoice_id ? <p>{tr("Tệp này đã được lưu thành hóa đơn. ")}<Link className="text-link" href={`/invoices/${draft.invoice_id}`}>{tr("Mở hóa đơn hiện có")}</Link></p> : <><div className="success-note"><CheckCircle2 size={17}/> {tr(" Đã gợi ý ")}{Object.keys(draft.suggestions.fields).length}{tr("/5 trường từ ")}{draft.filename}{tr(". Kiểm tra các trường còn thiếu trong biểu mẫu.")}</div><div className="extracted-fields">{Object.entries(draft.suggestions.fields).map(([key, value]) => <div key={key}><strong>{fieldNames[key] || key}</strong><span>{value.value}</span><small>{tr("Trang")} {value.page}: {value.source_line}</small></div>)}</div>{draft.suggestions.warnings.map(warning => <p className="small muted" key={warning}>{warning}</p>)}</>}<details className="context-help"><summary>{tr("Xem toàn văn đã đọc")}</summary><div>{draft.pages.map(page => <section key={page.page}><strong>{tr("Trang")} {page.page}</strong><pre className="policy-source">{page.text}</pre></section>)}</div></details></div>}</section>;
}
