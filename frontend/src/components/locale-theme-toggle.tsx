"use client";
import {Moon, Sun} from "lucide-react";
import {useTheme} from "@/components/theme-provider";
import {useI18n, type Locale} from "@/components/i18n-provider";
import {tr} from "@/lib/i18n";

const LOCALES: {value: Locale; label: string}[] = [
  {value: "vi", label: "Tiếng Việt"},
  {value: "en", label: "English"},
  {value: "zh", label: "中文"},
];

export function LanguageSelector() {
  const {locale, setLocale} = useI18n();
  return (
    <div className="language-group" role="group" aria-label={tr("Chọn ngôn ngữ")}>
      {LOCALES.map(l => (
        <button
          key={l.value}
          className={`lang-btn${l.value === locale ? " active" : ""}`}
          onClick={() => setLocale(l.value)}
          aria-pressed={l.value === locale}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}

export function ThemeToggle() {
  useI18n();
  const {resolved, setTheme} = useTheme();
  const isDark = resolved === "dark";
  return (
    <button
      type="button"
      className="icon-button theme-toggle"
      aria-label={tr("Giao diện")}
      aria-pressed={isDark}
      title={tr(isDark ? "Chuyển sang chế độ sáng" : "Chuyển sang chế độ tối")}
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      {isDark ? <Sun size={18} aria-hidden="true"/> : <Moon size={18} aria-hidden="true"/>}
    </button>
  );
}
