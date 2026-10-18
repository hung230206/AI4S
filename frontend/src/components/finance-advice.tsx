"use client";
import {useEffect, useState} from "react";
import Link from "next/link";
import {ArrowRight, Sparkles} from "lucide-react";
import {api} from "@/lib/api";
import {Forecast} from "@/lib/finance";
import {useAuth} from "@/components/shell";

export function FinanceAdvice() {
  const {token, dataVersion} = useAuth(); const [forecast, setForecast] = useState<Forecast>(); const [error, setError] = useState("");
  useEffect(() => {let active = true; api<Forecast>("/finance/forecast?days=30", token).then(value => {if (active) {setForecast(value); setError("");}}).catch(e => {if (active) setError(e.message);}); return () => {active = false;};}, [token, dataVersion]);
  return <section className="card next-step-assistant"><div className="section-heading"><h2><Sparkles size={19}/> Việc nên kiểm tra tiếp theo</h2><Link className="text-link" href="/finance">Mở ngân sách <ArrowRight size={15}/></Link></div><p className="small muted">Dựa trên số dư và lịch thu / chi bạn khai báo. Bạn quyết định mọi thay đổi; app không tự chuyển tiền.</p>{forecast ? <div className="advice-list">{forecast.recommendations.length ? forecast.recommendations.slice(0, 3).map((item, index) => <Link className={`advice-item ${item.severity}`} href={item.href} key={index}><div><strong>{item.title}</strong><p>{item.detail}</p></div><ArrowRight size={17}/></Link>) : <p>Chưa thấy thiếu hụt trong lịch 30 ngày đã nhập. Kiểm tra xem bạn đã thêm đủ các khoản phải trả chưa.</p>}</div> : <p className="small muted">{error || "Đang kiểm tra kế hoạch của bạn…"}</p>}</section>;
}
