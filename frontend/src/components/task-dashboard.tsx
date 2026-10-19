"use client";
import {useEffect, useState} from "react";
import Link from "next/link";
import {ArrowRight, FileText, ShieldCheck, Wallet, Clock3} from "lucide-react";
import {api, type Invoice, type Order} from "@/lib/api";
import {useTaskCopy} from "@/lib/task-ui";
import {useAuth} from "./shell";
import {Heading, ErrorBox} from "./ui";

export function TaskDashboard() {
  const t = useTaskCopy(); const {token, dataVersion} = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]); const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  useEffect(() => {let active = true; Promise.all([api<{items: Invoice[]}>("/invoices", token), api<{items: Order[]}>("/orders", token)]).then(([i, o]) => {if (active) {setInvoices(i.items); setOrders(o.items); setError("");}}).catch(e => {if (active) setError(e.message);}).finally(() => {if (active) setLoading(false);}); return () => {active = false;};}, [token, dataVersion]);
  const pending = orders.find(o => ["PROCESSING", "AWAITING_CONFIRMATION"].includes(o.status));
  const openFees = invoices.filter(i => i.status === "OPEN" && !orders.some(o => o.invoice_id === i.id && ["SUCCEEDED", "PROCESSING", "AWAITING_CONFIRMATION"].includes(o.status)));
  const goals = [{key: "fee", icon: FileText, href: invoices.length ? "/invoices" : "/invoices/new", action: "feeAction"}, {key: "insurance", icon: ShieldCheck, href: "/insurance", action: "insuranceAction"}, {key: "budget", icon: Wallet, href: "/finance", action: "budgetAction"}];
  return <>
    <Heading eyebrow="DEMO · STUDENT FINANCE" title={t("homeTitle")}>{t("homeSub")}</Heading><ErrorBox message={error}/>
    <section className="goal-grid" aria-label={t("homeTitle")}>{goals.map(goal => <article className="card goal-card" key={goal.key}><span className="task-icon"><goal.icon size={27}/></span><h2>{t(goal.key)}</h2><p>{t(`${goal.key}Text`)}</p><Link className="button primary" href={goal.href}>{t(goal.action)}<ArrowRight size={17}/></Link></article>)}</section>
    <section className="card task-resume"><h2><Clock3 size={20}/>{t("continue")}</h2>{!loading && !pending && !openFees.length && <p className="muted">{t("noTasks")}</p>}
      {pending && <div className="task-resume-row"><p>{t(pending.status === "PROCESSING" ? "waiting" : "confirm")}</p><Link className="button secondary" href={`/payments/${pending.id}`}>{t("open")}<ArrowRight size={16}/></Link></div>}
      {openFees.slice(0, 3).map(invoice => <div className="task-resume-row" key={invoice.id}><div><strong>{invoice.invoice_number}</strong><p>{invoice.amount_cny} CNY · {invoice.due_date}</p></div><Link className="button secondary" href={`/invoices/${invoice.id}`}>{t("open")}<ArrowRight size={16}/></Link></div>)}
      <Link className="text-link" href="/history">{t("history")} →</Link>
    </section>
    <Link className="text-link sample-shortcut" href="/test-lab">{t("samples")} →</Link>
  </>;
}
