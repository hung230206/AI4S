"use client";
import {createContext, useContext, useEffect, useSyncExternalStore} from "react";
import {preference, writePreference, subscribePreferences} from "@/lib/preferences";
export type Theme = "light" | "dark" | "system";
const ThemeCtx = createContext<{theme: Theme; setTheme: (value: Theme) => void; resolved: "light" | "dark"}>({theme: "system", setTheme: () => {}, resolved: "light"});
function getTheme(): Theme {const value = preference("baoan.theme", "system"); return value === "light" || value === "dark" ? value : "system";}
function subscribeSystem(listener: () => void) {const media = matchMedia("(prefers-color-scheme: dark)"); media.addEventListener("change", listener); return () => media.removeEventListener("change", listener);}
function getSystemDark() {return matchMedia("(prefers-color-scheme: dark)").matches;}
function setTheme(value: Theme) {writePreference("baoan.theme", value);}
export function ThemeProvider({children}: {children: React.ReactNode}) {
  const theme = useSyncExternalStore(subscribePreferences, getTheme, () => "system" as Theme);
  const systemDark = useSyncExternalStore(subscribeSystem, getSystemDark, () => false);
  const resolved = theme === "system" ? systemDark ? "dark" : "light" : theme;
  useEffect(() => {document.documentElement.classList.toggle("dark", resolved === "dark"); document.documentElement.style.colorScheme = resolved;}, [resolved]);
  return <ThemeCtx.Provider value={{theme, setTheme, resolved}}>{children}</ThemeCtx.Provider>;
}
export function useTheme() {return useContext(ThemeCtx);}
