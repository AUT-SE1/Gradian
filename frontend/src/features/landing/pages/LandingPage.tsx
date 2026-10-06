import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function LandingPage() {
  const { t } = useTranslation('common');
  return (
    <section className="placeholder-page">
      <span className="eyebrow">{t('appName')}</span>
      <h1>{t('landing.title')}</h1>
      <p>{t('landing.subtitle')}</p>
      <Link className="primary-button" to="/login">{t('landing.login')}</Link>
    </section>
  );
}
