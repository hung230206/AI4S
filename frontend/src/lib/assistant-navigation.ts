export type NavigationProposal = {href: string; title: string; reason: string};

const pages = new Set(["/history", "/invoices/new", "/invoices", "/finance", "/rates", "/assistant", "/insurance", "/account"]);
const statuses = new Set(["SUCCEEDED", "FAILED", "PROCESSING", "CANCELLED", "EXPIRED", "AWAITING_CONFIRMATION"]);

// Never feed a model-provided URL directly into the app router.
export function safeNavigation(value: unknown): NavigationProposal | null {
  if (!value || typeof value !== "object") return null;
  const item = value as Partial<NavigationProposal>;
  if (typeof item.href !== "string" || typeof item.title !== "string" || !item.title.trim() || item.title.length > 100 || typeof item.reason !== "string" || item.reason.length > 500) return null;
  const [pathname, query, extra] = item.href.split("?");
  if (!pages.has(pathname) || extra !== undefined) return null;
  if (query !== undefined && (pathname !== "/history" || !query.startsWith("status=") || !statuses.has(query.slice(7)))) return null;
  return {href: item.href, title: item.title, reason: item.reason};
}
