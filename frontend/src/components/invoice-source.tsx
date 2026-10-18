"use client";
import {tr} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";

import {useEffect, useState} from "react";
import {api, API, authHeaders} from "@/lib/api";
import {InvoiceDraft} from "@/components/invoice-import";
import {useAuth} from "@/components/shell";
import {ErrorBox} from "@/components/ui";
export function InvoiceSource({invoiceId}: {invoiceId: string}) {
  useI18n();
  const {token} = useAuth(); const [source, setSource] = useState<InvoiceDraft | null>(null); const [error, setError] = useState("");
  useEffect(() => {let active = true; api<{source: InvoiceDraft | null}>(`/invoice-imports/by-invoice/${invoiceId}`, token).then(value => {if (active) setSource(value.source);}).catch(e => {if (active) setError(e.message);}); return () => {active = false;};}, [invoiceId, token]);
  async function download() {if (!source) return; try {const response = await fetch(`${API}/api/v1/invoice-imports/${source.id}/download`, {credentials: "include", headers: authHeaders(token)}); if (!response.ok) throw new Error(tr("Không tải được chứng từ gốc")); const url = URL.createObjectURL(await response.blob()); const a = document.createElement("a"); a.href = url; a.download = source.filename; a.click(); URL.revokeObjectURL(url);} catch (e) {setError((e as Error).message);}}
  return <>{error && <ErrorBox message={error}/>} {source && <details className="context-help source-evidence"><summary>{tr("Chứng từ gốc và nội dung đã đọc")}</summary><div><p><strong>{source.filename}</strong> · {source.method === "LOCAL_TESSERACT" ? tr("Đã nhận dạng bằng OCR cục bộ") : tr("Đã đọc văn bản trực tiếp")}</p><p>{tr("Dữ liệu hóa đơn đã được người dùng đối chiếu trước khi lưu.")}</p><button className="text-link" onClick={download}>{tr("Tải chứng từ gốc")}</button>{source.pages.map(page => <section key={page.page}><strong>{tr("Trang")} {page.page}</strong><pre className="policy-source">{page.text}</pre></section>)}</div></details>}</>;
}
