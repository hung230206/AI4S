"use client";
import {useEffect, useState} from "react";
import Link from "next/link";
import {api, labels, vnd, type Invoice, type Order} from "@/lib/api";
import type {Plan} from "@/lib/finance";
import {useTaskCopy} from "@/lib/task-ui";
import {tr} from "@/lib/i18n";
import {useAuth} from "./shell";
import {ErrorBox} from "./ui";

export function InvoiceJourney({invoice}: {invoice: Invoice}) {
  const {token, dataVersion} = useAuth(); const t = useTaskCopy();
  const [order, setOrder] = useState<Order>(); const [plan, setPlan] = useState<Plan>(); const [loaded, setLoaded] = useState(false); const [error, setError] = useState("");
  useEffect(() => {let active = true;
    async function load() {
      try {
        const [orders, plans] = await Promise.all([api<{items: Order[]}>("/orders", token), api<{items: Plan[]}>("/finance/plans", token)]);
        const matching = orders.items.filter(o => o.invoice_id === invoice.id).sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at));
        const selected = matching.find(o => o.status === "SUCCEEDED") || matching.find(o => ["PROCESSING", "AWAITING_CONFIRMATION"].includes(o.status)) || matching[0];
        const detail = selected ? await api<Order>(`/orders/${selected.id}`, token) : undefined;
        if (active) {setOrder(detail); setPlan(plans.items.find(p => p.invoice_id === invoice.id && p.active)); setError("");}
      } catch (e) {if (active) setError((e as Error).message);} finally {if (active) setLoaded(true);}
    }
    void load(); return () => {active = false;};
  }, [invoice.id, token, dataVersion]);
  return <section className="card invoice-journey" aria-label={t("feeProgress")}><h2>{t("feeProgress")}</h2><ErrorBox message={error}/><ol>
    <li><span>1</span><div><strong>{t("saved")}</strong><p>{invoice.amount_cny} CNY · {invoice.due_date}</p></div></li>
    <li><span>2</span><div><strong>{t("plan")}</strong><p>{error ? t("unavailable") : loaded ? t(plan ? "planYes" : "planNo") : tr("Đang tải…")}</p>{plan && (plan.amount !== invoice.amount_cny || plan.due_date !== invoice.due_date) && <p className="error">{t("planChanged")}</p>}</div></li>
    <li><span>3</span><div><strong>{t("payment")}</strong><p>{error ? t("unavailable") : order ? labels[order.status] : loaded ? t("notTried") : tr("Đang tải…")}</p>{!error && order?.quote && <p>{vnd(order.quote.total_vnd)} · {order.quote.rate_source === "DEMO_FIXED" ? "DEMO_RATE" : "FRANKFURTER"}</p>}</div></li>
  </ol>{invoice.status === "VOID" && <p className="info-note">{tr("Hóa đơn đã được lưu trữ, không tạo thêm báo giá.")}</p>}<p className="small muted">{t("quoteNote")}</p>{loaded && !error && <div className="actions">{order && ["SUCCEEDED", "PROCESSING", "AWAITING_CONFIRMATION"].includes(order.status) ? <Link className="button primary" href={`/payments/${order.id}`}>{t("viewPayment")}</Link> : invoice.status === "OPEN" && <Link className="button primary" href={`/checkout/${invoice.id}`}>{tr(invoice.source_type === "SYNTHETIC" ? "Xem báo giá mô phỏng" : "Xem giá trị VND")}</Link>}<Link className="text-link" href="/finance">{t("budgetLink")} →</Link></div>}</section>;
}
