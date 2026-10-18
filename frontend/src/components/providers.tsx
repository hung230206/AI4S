"use client";
import {ThemeProvider} from "@/components/theme-provider";
import {I18nProvider} from "@/components/i18n-provider";

export function Providers({children}: {children: React.ReactNode}) {
  return (
    <ThemeProvider>
      <I18nProvider>{children}</I18nProvider>
    </ThemeProvider>
  );
}