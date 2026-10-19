"use client";
import Link from "next/link";
import {useI18n} from "./i18n-provider";
import {ragText} from "@/lib/rag";
export function InsuranceRagEntry() {
  const {locale} = useI18n(); const t = ragText(locale);
  return <aside className="card detail-card"><h2>{t.title}</h2><p>{t.intro}</p><Link className="button secondary" href="/knowledge">{t.ask} →</Link></aside>;
}
