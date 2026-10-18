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
  const {theme, setTheme} = useTheme();
  return (
    <label className="theme-control">
      {theme === "dark" ? <Moon size={16} aria-hidden="true"/> : <Sun size={16} aria-hidden="true"/>}
      <span className="sr-only">{tr("Giao diện")}</span>
      <select aria-label={tr("Giao diện")} value={theme} onChange={event => setTheme(event.target.value as "light" | "dark" | "system")}>
        <option value="system">{tr("Theo thiết bị")}</option>
        <option value="light">{tr("Sáng")}</option>
        <option value="dark">{tr("Tối")}</option>
      </select>
    </label>
  );
}
