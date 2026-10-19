"use client";
import Link from "next/link";
import {ArrowRight, ShieldCheck} from "lucide-react";
import {useInsuranceCopy} from "@/lib/insurance";
export function InsuranceEntry() {
  const t = useInsuranceCopy();
  return <section className="card insurance-entry"><ShieldCheck size={26}/><div><h2>{t("entry")}</h2><p>{t("entryText")}</p></div><Link className="button secondary" href="/insurance">{t("enter")}<ArrowRight size={16}/></Link></section>;
}
