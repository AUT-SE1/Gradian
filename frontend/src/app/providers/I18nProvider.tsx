import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';
import i18n from '@/shared/i18n/i18n';
import type { Language } from '@/shared/types/i18n';

type I18nContextValue = { language: Language; toggleLanguage: () => void };
const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: PropsWithChildren) {
  const [language, setLanguage] = useState<Language>((localStorage.getItem('language') as Language) || 'fa');

  useEffect(() => {
    void i18n.changeLanguage(language);
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'fa' ? 'rtl' : 'ltr';
    localStorage.setItem('language', language);
  }, [language]);

  const value = useMemo(() => ({
    language,
    toggleLanguage: () => setLanguage((current) => current === 'fa' ? 'en' : 'fa'),
  }), [language]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const value = useContext(I18nContext);
  if (!value) throw new Error('useI18n must be used inside I18nProvider');
  return value;
}
