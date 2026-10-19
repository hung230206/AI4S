"use client";
import {tr} from "@/lib/i18n";
import {PageIntro} from "./page-intro";
import {FloatingAssistant} from "./floating-assistant";
import {preference, writePreference} from "@/lib/preferences";

import {createContext, useContext, useEffect, useState, useCallback, Suspense} from "react";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {
  ShieldCheck,
  LayoutDashboard,
  Clock3,
  Settings2,
  Globe2,
  ChevronRight,
  UserRound,
  FileText,
  LogOut,
  Wallet,
} from "lucide-react";
import {api, Account, AccountSession} from "@/lib/api";
import {AuthScreen} from "@/components/auth-screen";
import {UserGuide} from "@/components/user-guide";
import {LanguageSelector, ThemeToggle} from "@/components/locale-theme-toggle";
import {useI18n} from "@/components/i18n-provider";

type AuthValue = {
  token: string;
  user: Account | null;
  dataVersion: number;
  invalidate: () => void;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
};
const Auth = createContext<AuthValue>({
  token: "",
  user: null,
  dataVersion: 0,
  invalidate: () => {},
  refresh: async () => {},
  logout: async () => {},
});
export const useToken = () => useContext(Auth).token;
export const useAuth = () => useContext(Auth);

const nav = [
  {href: "/", key: "nav_dashboard", icon: LayoutDashboard},
  {href: "/invoices", key: "nav_invoices", icon: FileText},
  {href: "/finance", key: "nav_finance", icon: Wallet},
  {href: "/history", key: "nav_history", icon: Clock3},
  {href: "/insurance", key: "nav_insurance", icon: ShieldCheck},
  {href: "/account", key: "nav_account", icon: UserRound},
];

export function Shell({children}: {children: React.ReactNode}) {
  const path = usePathname();
  const {t} = useI18n();
  const [token, setToken] = useState("");
  const [user, setUser] = useState<Account | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [connectionError, setConnectionError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [dataVersion, setDataVersion] = useState(0);
  const invalidate = useCallback(() => setDataVersion(value => value + 1), []);

  function accept(value: AccountSession) {
    writePreference("baoan.mode", "");
    setUser(value.user);
    setToken(`csrf:${value.csrf_token}`);
    setConnectionError("");
  }
  async function demo() {
    const result = await api<{access_token: string}>("/demo/session", "", {role: "STUDENT"});
    const profile = await api<AccountSession>("/auth/session", result.access_token);
    writePreference("baoan.mode", "demo");
    setToken(result.access_token);
    setUser(profile.user);
  }
  async function refresh() {
    accept(await api<AccountSession>("/auth/session", ""));
  }
  async function logout() {
    await api("/auth/logout", token, {});
    writePreference("baoan.mode", "");
    setToken("");
    setUser(null);
  }
  useEffect(() => {
    const expired = () => {
      writePreference("baoan.mode", "");
      setToken("");
      setUser(null);
    };
    window.addEventListener("baoan:unauthorized", expired);
    return () => window.removeEventListener("baoan:unauthorized", expired);
  }, []);
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const result = await api<AccountSession>("/auth/session", "");
        if (active) {
          writePreference("baoan.mode", "");
          setToken(`csrf:${result.csrf_token}`);
          setUser(result.user);
          setConnectionError("");
        }
      } catch (e) {
        if (!active) return;
        if ((e as Error).message.includes("UNAUTHORIZED")) {
          if (preference("baoan.mode", "") === "demo") {
            try {
              const result = await api<{access_token: string}>("/demo/session", "", {role: "STUDENT"});
              const profile = await api<AccountSession>("/auth/session", result.access_token);
              if (active) {
                setToken(result.access_token);
                setUser(profile.user);
              }
            } catch (e) {
              if (active) setConnectionError((e as Error).message);
            }
          }
        } else {
          setConnectionError((e as Error).message);
        }
      } finally {
        if (active) setLoaded(true);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [attempt]);

  if (path === "/privacy") return <Auth.Provider value={{token, user, dataVersion, invalidate, refresh, logout}}>{children}{loaded && token && user && <Suspense fallback={null}><FloatingAssistant key={`${user.id}:${token}`}/></Suspense>}</Auth.Provider>;
  if (!loaded) return <div className="loading" role="status">{t("checking_session")}</div>;
  if (!token)
    return (
      <>
        {connectionError && (
          <div className="error" role="alert">
            {connectionError}
            <button onClick={() => setAttempt(v => v + 1)}>{t("reconnect")}</button>
          </div>
        )}
        <div className="auth-preferences"><ThemeToggle/><LanguageSelector/></div>
        {path.startsWith("/admin/rag") && <p className="info-note">{t("nav_rag_admin")} · {tr("Đăng nhập bằng tài khoản quản trị được cấp. Tạo tài khoản thường không cấp quyền quản trị.")}</p>}
        <AuthScreen onAccount={accept} onDemo={demo}/>
      </>
    );

  const demoMode = Boolean(user?.is_demo);
  const pageLabel =
    (nav.find(item => item.href === path) ? t(nav.find(item => item.href === path)!.key) : "") ||
    (path === "/rates" ? t("nav_rates") : path === "/assistant" ? t("nav_assistant") : path.startsWith("/admin/rag") ? t("nav_rag_admin") : path.startsWith("/knowledge") ? t("nav_knowledge") : path.startsWith("/checkout") ? t("checkout_label") :
      path.startsWith("/payments") ? t("payments_label") :
        path.startsWith("/receipts") ? t("receipts_label") :
          path.startsWith("/insurance") ? t("nav_insurance") :
          path === "/test-lab" ? t("testlab_label") :
            path === "/operator" ? t("operator_label") :
              path.endsWith("/edit") ? t("edit_invoice_label") :
                path === "/invoices/new" ? t("new_invoice_label") : t("invoice_detail_label"));
  return (
    <Auth.Provider value={{token, user, dataVersion, invalidate, refresh, logout}}>
      <div className="app-shell">
        <aside className="sidebar">
          <Link href="/" className="brand">
            <span className="brand-icon"><ShieldCheck size={27}/></span>
            <span>Demo<span className="brand-sub">STUDENT FINANCE</span></span>
          </Link>
          <div className="workspace-label">{t("workspace_label")}</div>
          <nav aria-label={tr("Điều hướng chính")}>
            {nav.map(n => {
              const label = t(n.key);
              return (
                <Link
                  className={`nav-item ${path === n.href ? "active" : ""}`}
                  href={n.href}
                  key={n.href}
                  title={label}
                >
                  <n.icon size={19}/>
                  {label}
                  {path === n.href && <ChevronRight size={15} className="nav-chevron"/>}
                </Link>
              );
            })}
            {user?.is_rag_admin && <Link className={`nav-item ${path === "/admin/rag" ? "active" : ""}`} href="/admin/rag"><Settings2 size={19}/>{t("nav_rag_admin")}</Link>}
          </nav>
          <div className="sidebar-bottom">
            <div className="corridor">
              <Globe2 size={23}/>
              <div>
                {t("corridor_title")}
                <small>{t("corridor_sub")}</small>
              </div>
            </div>
            <div className="sandbox-label">
              <span className="dot"/>
              {demoMode ? t("sandbox_label_demo") : t("sandbox_label_personal")}
            </div>
            <button className="text-link logout-button" onClick={() => logout().catch(e => setConnectionError(e.message))}>
              <LogOut size={14}/>
              {t("logout")}
            </button>
            <Link className="text-link" href="/test-lab">{t("test_lab")}</Link>
            <details className="operator-tools">
              <summary>{t("operator_tools")}</summary>
              <Link href="/operator" className="text-link">
                <Settings2 size={14}/> {t("operator_panel")}
              </Link>
            </details>
          </div>
        </aside>
        <div className="main-shell">
          <header className="topbar">
            <span className="breadcrumb">
              {t("breadcrumb_space")} <ChevronRight size={14}/> <b>{pageLabel}</b>
            </span>
            <div className="topbar-right">
              <ThemeToggle/>
              <LanguageSelector/>
              <UserGuide key={user?.id} userId={user?.id || "demo"}/>
              <Link href="/account" className="avatar" aria-label={tr("Mở tài khoản")}>
                {user?.display_name.slice(0, 2).toUpperCase()}
              </Link>
              <span className="user-name">
                {user?.display_name}
                <small>{demoMode ? t("sandbox_label_demo") : user?.email}</small>
              </span>
            </div>
          </header>
          <div className="simulation-bar">
            <ShieldCheck size={16}/>
            <span>{demoMode ? t("simulation_demo") : t("simulation_personal")}</span>
          </div>
          <main id="main-content">{connectionError && <div className="error" role="alert">{connectionError}</div>}{children}</main>
          <footer>
            {t("footer_copyright")} <Link href="/privacy">{tr("Quyền riêng tư")}</Link>
            <span>{demoMode ? t("footer_demo") : t("footer_personal")}</span>
          </footer>
        </div>
      </div>
      <Suspense fallback={null}><PageIntro key={user?.id} userId={user?.id || "demo"}/></Suspense>
      <Suspense fallback={null}><FloatingAssistant key={`${user?.id}:${token}`}/></Suspense>
    </Auth.Provider>
  );
}
