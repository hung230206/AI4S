"use client";
import {useEffect, useState} from "react";
import Link from "next/link";
import {api} from "@/lib/api";
import {type PortfolioPolicy} from "@/lib/insurance";
import {useTaskCopy} from "@/lib/task-ui";
import {useAuth} from "./shell";

export function PaymentNextSteps({invoiceId, orderId}: {invoiceId: string; orderId: string}) {
  const {token} = useAuth(); const t = useTaskCopy(); const [policy, setPolicy] = useState<PortfolioPolicy>();
  useEffect(() => {let active = true; api<{items: PortfolioPolicy[]}>("/insurance/policies", token).then(value => {if (active) setPolicy(value.items.find(p => p.active && p.premium_invoice_id === invoiceId));}).catch(() => {}); return () => {active = false;};}, [token, invoiceId]);
  return <section className="card detail-card payment-complete-next"><h2>{t("paymentDone")}</h2><p>{t("doneText")}</p><div className="actions"><Link className="button primary" href={`/receipts/${orderId}`}>{t("receipt")}</Link><Link className="button secondary" href="/">{t("home")}</Link></div><div className="completion-secondary"><Link className="text-link" href="/finance">{t("budgetLink")} <span aria-hidden="true">→</span></Link>{policy && <Link className="text-link" href={`/insurance#policy-${policy.id}`}>{t("relatedPolicy")} <span aria-hidden="true">→</span></Link>}</div></section>;
}
