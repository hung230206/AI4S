"use client";
import {createContext, useContext, useEffect, useSyncExternalStore} from "react";
import {activateLocale, getLocale, setLocale, t, type Locale} from "@/lib/i18n";
import {subscribePreferences} from "@/lib/preferences";
export type {Locale};
const I18nCtx = createContext({locale: "vi" as Locale, setLocale, t});
export function I18nProvider({children}: {children: React.ReactNode}) {
  const locale = useSyncExternalStore(subscribePreferences, getLocale, () => "vi" as Locale);
  useEffect(activateLocale, []);
  useEffect(() => {document.documentElement.lang = locale === "zh" ? "zh-CN" : locale;}, [locale]);
  return <I18nCtx.Provider value={{locale, setLocale, t}}>{children}</I18nCtx.Provider>;
}
export function useI18n() {return useContext(I18nCtx);}
