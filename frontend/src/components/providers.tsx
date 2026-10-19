"use client";
import {FileConsentDialog} from "./file-consent";
import {ThemeProvider} from "@/components/theme-provider";
import {I18nProvider} from "@/components/i18n-provider";

export function Providers({children}: {children: React.ReactNode}) {
  return (
    <ThemeProvider>
      <I18nProvider>{children}<FileConsentDialog/></I18nProvider>
    </ThemeProvider>
  );
}