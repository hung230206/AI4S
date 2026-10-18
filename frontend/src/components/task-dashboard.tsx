"use client";
import {tr} from "@/lib/i18n";
import {useI18n} from "@/components/i18n-provider";

import {useEffect, useState} from "react";
import Link from "next/link";
import {ArrowRight, ArrowUpRight, BookOpen, CheckCircle2, Clock3, FileText, Globe2, Plus} from "lucide-react";
import {api, Invoice, Order, ReferenceRate, time, vnd, rateText} from "@/lib/api";
import {useAuth} from "@/components/shell";
import {Heading, InvoiceCard, ErrorBox, StatusBadge} from "@/components/ui";
import {FinanceAdvice} from "@/components/finance-advice";
import {t} from "@/lib/i18n";

export function TaskDashboard() {
  useI18n();
  const {token, user, dataVersion} = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [fx, setFx] = useState<ReferenceRate>();
  const [fxError, setFxError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const demo = Boolean(user?.is_demo);
  useEffect(() => {
    let active = true;
    Promise.all([api<{items: Invoice[]}>("/invoices", token), api<{items: Order[]}>("/orders", token)]).then(([i, o]) => {if (active) {setInvoices(i.items); setOrders(o.items);}}).catch(e => {if (active) setError(e.message);}).finally(() => {if (active) setLoading(false);});
    if (!demo) api<ReferenceRate>("/fx/latest", token).then(value => {if (active) setFx(value);}).catch(e => {if (active) setFxError(e.message);});
    return () => {active = false;};
  }, [token, demo, dataVersion]);
  const open = invoices.filter(i => i.status === "OPEN");
  const pending = orders.find(o => o.status === "PROCESSING" || o.status === "AWAITING_CONFIRMATION");
  const recentInvoice = open[0] || invoices[0];
  return <>
    <Heading eyebrow={t("dashboard_eyebrow")} title={t("dashboard_title")}>{t("dashboard_sub")}</Heading>
    <ErrorBox message={error}/>
    <section className="lab-banner"><div><strong>{t("lab_banner_strong")}</strong><p>{t("lab_banner_text")}</p></div><Link className="button primary" href="/test-lab">{t("lab_banner_button")} <ArrowRight size={16}/></Link></section>
    <section className="task-start" aria-labelledby="task-start-title">
      <div className="section-heading"><div><span className="eyebrow">{t("task_start_eyebrow")}</span><h2 id="task-start-title">{t("task_start_title")}</h2></div><span className="task-time">{t("task_start_time")}</span></div>
      <div className="task-grid">
        <article className="task-card task-primary"><span className="task-icon"><FileText size={24}/></span><span className="task-number">01 / {t("task_01_label").replace("01 / ","")}</span><h3>{t("task_01_title")}</h3><p>{t("task_01_text")}</p><Link className="button primary" href={invoices.length ? "/invoices" : "/invoices/new"}>{invoices.length ? t("task_01_button") : t("task_01_button_empty")}<ArrowRight size={17}/></Link><small>{t("task_01_small")}</small></article>
        <article className="task-card"><span className="task-icon"><BookOpen size={24}/></span><span className="task-number">02 / {t("task_02_label").replace("02 / ","")}</span><h3>{t("task_02_title")}</h3><p>{t("task_02_text")}</p><Link className="button secondary" href="/assistant">{t("task_02_button")}<ArrowRight size={17}/></Link><small>{t("task_02_small")}</small></article>
      </div>
    </section>
    <section className="card getting-started" aria-labelledby="journey-title"><div><span className="eyebrow">{t("journey_eyebrow")}</span><h2 id="journey-title">{t("journey_title")}</h2><p>{t("journey_sub")}</p></div><ol><li className={invoices.length ? "done" : ""}><span>{invoices.length ? <CheckCircle2 size={18}/> : "1"}</span><div><strong>{t("journey_1_title")}</strong><small>{t("journey_1_small")}</small></div></li><li><span>2</span><div><strong>{t("journey_2_title")}</strong><small>{t("journey_2_small")}</small></div></li><li><span>3</span><div><strong>{t("journey_3_title")}</strong><small>{t("journey_3_small")}</small></div></li></ol></section>
    {pending && <div className="continue-card"><Clock3 size={23}/><div><strong>{pending.status === "PROCESSING" ? t("continue_processing") : t("continue_awaiting")}</strong><p>{pending.status === "PROCESSING" ? t("continue_processing_text") : t("continue_awaiting_text")}</p></div><Link className="button secondary" href={`/payments/${pending.id}`}>{t("continue_button")}<ArrowRight size={16}/></Link></div>}
    <div className="finance-quick-links"><Link href="/finance"><strong>{t("quick_finance")}</strong><span>{t("quick_finance_sub")}</span><ArrowRight size={18}/></Link><Link href="/rates"><strong>{t("quick_rates")}</strong><span>{t("quick_rates_sub")}</span><ArrowRight size={18}/></Link></div><FinanceAdvice/><section className="stats-grid" aria-label={tr("Tổng quan giao dịch")}>{[{label: t("stats_open_invoices"), value: open.length, icon: FileText}, {label: t("stats_processing"), value: orders.filter(o => o.status === "PROCESSING").length, icon: Clock3}, {label: t("stats_succeeded"), value: orders.filter(o => o.status === "SUCCEEDED").length, icon: CheckCircle2}].map(s => <div className="stat-card" key={s.label}><span className="stat-icon"><s.icon size={20}/></span><div><span>{s.label}</span><strong>{loading ? "—" : s.value.toString().padStart(2, "0")}</strong></div></div>)}</section>
    <div className="dashboard-columns"><section><div className="section-heading"><h2>{t("invoices_heading")}</h2><Link href="/invoices/new" className="text-link"><Plus size={15}/> {t("invoices_add")}</Link></div>{loading ? <p role="status">{t("invoices_loading")}</p> : recentInvoice ? <><InvoiceCard invoice={recentInvoice}/><Link className="button secondary full" href="/invoices">{t("invoices_view_all", {count: String(invoices.length)})}</Link></> : <div className="card empty"><FileText size={30}/><h2>{t("invoices_empty_title")}</h2><p>{t("invoices_empty_text")}</p><Link className="text-link" href="/invoices/new">{t("invoices_empty_button")} <ArrowRight size={15}/></Link></div>}</section>
      <section><div className="section-heading"><h2>{demo ? t("rates_heading_demo") : t("rates_heading_personal")}</h2><Globe2 size={20}/></div><div className="card detail-card rate-overview">{demo ? <><span className="badge demo">{t("rates_demo_badge")}</span><h3>{t("rates_demo_title")}</h3><p>{t("rates_demo_text")}</p><Link className="text-link" href="/account">{t("rates_demo_button")} <ArrowRight size={15}/></Link></> : fx ? <><span className="badge reference">{t("rates_reference")}</span><p className="muted">{t("rates_equivalent")}</p><strong className="live-rate">{rateText(fx.rate)} <span>VND</span></strong><dl className="detail-list"><div><dt>{t("rates_date_label")}</dt><dd>{fx.rate_date}</dd></div><div><dt>{t("rates_fetched_label")}</dt><dd>{time(fx.fetched_at)}</dd></div></dl>{fx.is_stale && <p className="small">{t("rates_stale")}</p>}<a className="text-link" href={fx.source_url} target="_blank" rel="noreferrer">{t("rates_source_link")}</a><p className="small muted">{t("rates_small")}</p></> : <><ErrorBox message={fxError}/>{!fxError && <p role="status">{tr("Đang lấy tỷ giá tham chiếu…")}</p>}</>}</div></section>
    </div>
    <section className="recent-section"><div className="section-heading"><h2>{t("recent_transactions")}</h2><Link href="/history" className="text-link">{t("recent_view_history")}<ArrowRight size={15}/></Link></div><div className="card">{orders.length ? orders.slice(0, 3).map(o => <Link className="history-row" href={`/payments/${o.id}`} key={o.id}><div><strong>{t("recent_transaction", {id: o.id.slice(0, 8)})}</strong><small>{time(o.created_at)}</small></div><b>{vnd(o.total_vnd)}</b><StatusBadge status={o.status}/><ArrowUpRight size={17}/></Link>) : <div className="empty"><Clock3 size={27}/><h3>{t("recent_empty_title")}</h3><p>{t("recent_empty_text")}</p></div>}</div></section>
  </>;
}