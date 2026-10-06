import { useTranslation } from 'react-i18next';
import type { PortalRole } from '@/shared/types/portal';

export function PortalHomePage({ portal }: { portal: PortalRole }) {
  const { t } = useTranslation('navigation');
  return (
    <section className="placeholder-page">
      <span className="eyebrow">{t(`portals.${portal}`)}</span>
      <h1>{t('portalPlaceholder.title')}</h1>
      <p>{t('portalPlaceholder.description')}</p>
    </section>
  );
}
