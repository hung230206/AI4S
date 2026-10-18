"use client";
import {createContext, useContext, useEffect, useState, useCallback} from "react";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {ShieldCheck, LayoutDashboard, Clock3, BookOpen, Settings2, Globe2, ChevronRight, UserRound, FileText, LogOut, Wallet, TrendingUp, MessageCircle} from "lucide-react";
import {api, Account, AccountSession} from "@/lib/api";
import {AuthScreen} from "@/components/auth-screen";
import {UserGuide} from "@/components/user-guide";

type AuthValue = {token: string; user: Account | null; dataVersion: number; invalidate: () => void; refresh: () => Promise<void>; logout: () => Promise<void>};
const Auth = createContext<AuthValue>({token: "", user: null, dataVersion: 0, invalidate: () => {}, refresh: async () => {}, logout: async () => {}});
export const useToken = () => useContext(Auth).token;
export const useAuth = () => useContext(Auth);
const nav = [
  {href: "/", label: "Tổng quan", icon: LayoutDashboard},
  {href: "/copilot", label: "Trợ lý du học", icon: MessageCircle},
  {href: "/invoices", label: "Hóa đơn", icon: FileText},
  {href: "/finance", label: "Ngân sách & thu chi", icon: Wallet},
  {href: "/rates", label: "Tỷ giá & ngân sách", icon: TrendingUp},
  {href: "/history", label: "Lịch sử giao dịch", icon: Clock3},
  {href: "/assistant", label: "Tài liệu bảo hiểm", icon: BookOpen},
  {href: "/account", label: "Tài khoản", icon: UserRound},
];

export function Shell({children}: {children: React.ReactNode}) {
  const path = usePathname();
  const [token, setToken] = useState("");
  const [user, setUser] = useState<Account | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [connectionError, setConnectionError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [dataVersion, setDataVersion] = useState(0);
  const invalidate = useCallback(() => setDataVersion(value => value + 1), []);

  function accept(value: AccountSession) {
    localStorage.removeItem("baoan.mode");
    setUser(value.user); setToken(`csrf:${value.csrf_token}`); setConnectionError("");
  }
  async function demo() {
    const result = await api<{access_token: string}>("/demo/session", "", {role: "STUDENT"});
    const profile = await api<AccountSession>("/auth/session", result.access_token);
    localStorage.setItem("baoan.mode", "demo"); setToken(result.access_token); setUser(profile.user);
  }
  async function refresh() {accept(await api<AccountSession>("/auth/session", ""));}
  async function logout() {
    if (token.startsWith("csrf:")) await api("/auth/logout", token, {});
    localStorage.removeItem("baoan.mode"); setToken(""); setUser(null);
  }
  useEffect(() => {
    const expired = () => {localStorage.removeItem("baoan.mode"); setToken(""); setUser(null);};
    window.addEventListener("baoan:unauthorized", expired);
    return () => window.removeEventListener("baoan:unauthorized", expired);
  }, []);
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const result = await api<AccountSession>("/auth/session", "");
        if (active) {localStorage.removeItem("baoan.mode"); setToken(`csrf:${result.csrf_token}`); setUser(result.user); setConnectionError("");}
      } catch (e) {
        if (!active) return;
        if ((e as Error).message.includes("UNAUTHORIZED")) {
          if (localStorage.getItem("baoan.mode") === "demo") {
            try {
              const result = await api<{access_token: string}>("/demo/session", "", {role: "STUDENT"});
              const profile = await api<AccountSession>("/auth/session", result.access_token);
              if (active) {setToken(result.access_token); setUser(profile.user);}
            } catch (e) {if (active) setConnectionError((e as Error).message);}
          }
        } else setConnectionError((e as Error).message);
      } finally {if (active) setLoaded(true);}
    }
    load(); return () => {active = false;};
  }, [attempt]);

  if (!loaded) return <div className="loading" role="status">Đang kiểm tra phiên đăng nhập…</div>;
  if (!token) return <>{connectionError && <div className="error" role="alert">{connectionError}<button onClick={() => setAttempt(v => v + 1)}>Kết nối lại</button></div>}<AuthScreen onAccount={accept} onDemo={demo}/></>;

  const demoMode = Boolean(user?.is_demo);
  const pageLabel = nav.find(n => n.href === path)?.label || (path.startsWith("/checkout") ? "Kiểm tra giá trị VND" : path.startsWith("/payments") ? "Theo dõi giao dịch" : path.startsWith("/receipts") ? "Biên nhận thử nghiệm" : path === "/test-lab" ? "Test A–Z" : path === "/operator" ? "Công cụ vận hành" : path.endsWith("/edit") ? "Chỉnh sửa hóa đơn" : path === "/invoices/new" ? "Thêm hóa đơn" : "Chi tiết hóa đơn");
  return <Auth.Provider value={{token, user, dataVersion, invalidate, refresh, logout}}>
    <div className="app-shell">
      <aside className="sidebar">
        <Link href="/" className="brand"><span className="brand-icon"><ShieldCheck size={27}/></span><span>Demo<span className="brand-sub">STUDENT FINANCE</span></span></Link>
        <div className="workspace-label">KHÔNG GIAN SINH VIÊN</div>
        <nav aria-label="Điều hướng chính">{nav.map(n => <Link className={`nav-item ${path === n.href ? "active" : ""}`} href={n.href} key={n.href} title={n.label}><n.icon size={19}/>{n.label}{path === n.href && <ChevronRight size={15} className="nav-chevron"/>}</Link>)}</nav>
        <div className="sidebar-bottom">
          <div className="corridor"><Globe2 size={23}/><div>Kết nối hành trình du học<small>Việt Nam <span>→</span> Trung Quốc</small></div></div>
          <div className="sandbox-label"><span className="dot"/> {demoMode ? "Đang dùng dữ liệu mẫu" : "Không gian cá nhân"}</div>
          <button className="text-link logout-button" onClick={() => logout().catch(e => setConnectionError(e.message))}><LogOut size={14}/> Đăng xuất</button>
          <Link className="text-link" href="/test-lab">Test A–Z và tải dữ liệu mẫu</Link><details className="operator-tools"><summary>Công cụ cho người vận hành</summary><Link href="/operator" className="text-link"><Settings2 size={14}/> Vận hành sandbox</Link></details>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar"><span className="breadcrumb">Không gian sinh viên <ChevronRight size={14}/><b>{pageLabel}</b></span><div className="topbar-right"><UserGuide key={user?.id} userId={user?.id || "demo"}/><Link href="/account" className="avatar" aria-label="Mở tài khoản">{user?.display_name.slice(0, 2).toUpperCase()}</Link><span className="user-name">{user?.display_name}<small>{demoMode ? "Dữ liệu mẫu dùng chung" : user?.email}</small></span></div></header>
        <div className="simulation-bar"><ShieldCheck size={16}/><span>{demoMode ? "Bạn đang dùng dữ liệu mẫu. Các giao dịch là mô phỏng." : "Bạn có thể tính chi phí và tra cứu tài liệu. Thanh toán đang ở chế độ thử, chưa chuyển tiền thật."}</span></div>
        <main id="main-content">{connectionError && <div className="error" role="alert">{connectionError}</div>}{children}</main>
        <footer>© 2026 Demo · Student finance<span>{demoMode ? "DỮ LIỆU MẪU · SANDBOX" : "HÓA ĐƠN VÀ TÀI LIỆU RIÊNG TƯ"}</span></footer>
      </div>
    </div>
  </Auth.Provider>;
}
