import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import faCommon from '@/locales/fa/common.json';
import faAuth from '@/locales/fa/auth.json';
import faNavigation from '@/locales/fa/navigation.json';
import enCommon from '@/locales/en/common.json';
import enAuth from '@/locales/en/auth.json';
import enNavigation from '@/locales/en/navigation.json';

void i18n.use(initReactI18next).init({
  resources: {
    fa: { common: faCommon, auth: faAuth, navigation: faNavigation },
    en: { common: enCommon, auth: enAuth, navigation: enNavigation },
  },
  lng: 'fa',
  fallbackLng: 'en',
  defaultNS: 'common',
  interpolation: { escapeValue: false },
});

export default i18n;
