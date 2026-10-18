export type Wallet = {id: string; name: string; currency: "CNY" | "VND"; balance: string; opening_balance: string; opening_date: string};
export type Entry = {id: string; wallet_id: string; wallet_name: string; currency: string; title: string; kind: "INCOME" | "EXPENSE"; amount: string; category: string; occurred_on: string; status: "POSTED" | "VOID"};
export type Plan = {id: string; wallet_id: string; wallet_name: string; currency: string; title: string; kind: "INCOME" | "EXPENSE"; amount: string; category: string; due_date: string; recurrence: "NONE" | "MONTHLY"; active: boolean; invoice_id: string | null};
export type Advice = {code: string; title: string; detail: string; href: string; severity: "info" | "warning"};
export type ForecastWallet = {wallet_id: string; name: string; currency: string; current_balance: string; projected_balance: string; minimum_balance: string; first_shortfall_date: string | null; points: {date: string; balance: string}[]};
export type CashEvent = {plan_id: string; wallet_id: string; wallet_name: string; currency: string; title: string; kind: "INCOME" | "EXPENSE"; amount: string; due_date: string; effective_date: string; overdue: boolean};
export type Forecast = {from: string; to: string; days: number; wallets: ForecastWallet[]; events: CashEvent[]; totals: Record<string, string>; projected_value_vnd: string | null; reference_rate: {rate: string; rate_date: string; source_url: string; is_stale: boolean} | null; rate_error: string | null; recommendations: Advice[]; notice: string};
export const categories: Record<string, string> = {TUITION: "Học phí", INSURANCE: "Bảo hiểm", HOUSING: "Tiền nhà", FOOD: "Ăn uống", TRANSPORT: "Đi lại", HEALTH: "Y tế", SCHOLARSHIP: "Học bổng", FAMILY: "Gia đình hỗ trợ", OTHER: "Khác"};
export const localDate = () => new Intl.DateTimeFormat("en-CA", {timeZone: "Asia/Ho_Chi_Minh", year: "numeric", month: "2-digit", day: "2-digit"}).format(new Date());
export const nativeMoney = (value: string, currency: string) => {
  const negative = value.startsWith("-"); const [whole, decimal = ""] = value.replace("-", "").split(".");
  return `${negative ? "−" : ""}${BigInt(whole || "0").toLocaleString("vi-VN")}${currency === "CNY" ? `,${decimal.padEnd(2, "0").slice(0, 2)}` : ""} ${currency === "VND" ? "₫" : currency}`;
};

export function chartPoints(values: string[], includeZero = true): string {
  // Number is used only for drawing positions; displayed amounts come from server Decimal strings.
  const coordinates = values.map(Number); const low = includeZero ? Math.min(0, ...coordinates) : Math.min(...coordinates); const high = Math.max(low + 1, ...coordinates);
  return coordinates.map((value, index) => `${15 + index * 670 / Math.max(1, values.length - 1)},${150 - (value - low) * 125 / (high - low)}`).join(" ");
}
