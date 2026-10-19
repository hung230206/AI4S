"use client";
import {useInsuranceCopy, type Benefit} from "@/lib/insurance";

export type DocumentProposal = {fields: Record<string, string>; evidence: Record<string, {value: string; page: number; quote: string}>; benefits?: Benefit[]; missing_fields?: string[]; warnings?: string[]; findings?: string[]; document_type?: string};
export function DocumentSuggestions({proposal}: {proposal: DocumentProposal}) {
  const t = useInsuranceCopy();
  const label = (key: string) => t(({premium_due: "due", starts_on: "starts", ends_on: "ends", incident_date: "eventDate", amount: "expense", benefit_kind: "benefit"} as Record<string, string>)[key] || key);
  return <aside className="document-proposal" aria-label={t("autoDetails")}>
    <p role="status"><strong>{t("autoFound")} {Object.keys(proposal.evidence).length} {t("autoFields")}</strong> {t("autoReview")}</p>
    {!!proposal.missing_fields?.length && <p className="small">{t("autoMissing")}: {proposal.missing_fields.map(label).join(", ")}.</p>}
    {!!proposal.warnings?.length && <p className="small">{t("autoAmbiguous")}</p>}
    {proposal.findings?.map(code => <p className="error" key={code}>{t(code)}</p>)}
    <details><summary>{t("autoEvidence")}</summary>{Object.entries(proposal.evidence).map(([key, e]) => <blockquote key={key}><strong>{label(key)}: {e.value} · {t("page")} {e.page}</strong><p className="insurance-preserve">{e.quote}</p></blockquote>)}</details>
  </aside>;
}
