import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PortalIcon } from './PortalIcon';
import type { NavigationIcon } from '@/app/navigation/navigation.config';

export function ServicePage({
  titleKey,
  descriptionKey,
  icon = 'briefcase',
  serviceUrl,
}: {
  titleKey: string;
  descriptionKey: string;
  icon?: NavigationIcon;
  serviceUrl?: string;
}) {
  const { t } = useTranslation('portal');
  const location = useLocation();
  const isStudent = location.pathname.startsWith('/student');

  if (!isStudent) {
    return (
      <div className="management-service-canvas">
        <section className="management-service-card">
          <span className="service-icon service-icon--blue"><PortalIcon name={icon} size={24} /></span>
          <h1>{t(titleKey)}</h1>
          <p>{t(descriptionKey)}</p>
          {serviceUrl && <a className="management-service-open" href={serviceUrl}>ورود به سرویس ←</a>}
        </section>
      </div>
    );
  }

  return (
    <div className="student-service-page-view">
      <div className="student-service-page-heading">
        <div className="service-title-row"><span className="service-icon service-icon--blue"><PortalIcon name={icon} size={22} /></span><div><small>{t('servicePage.kicker')}</small><h1>{t(titleKey)}</h1></div></div>
        <Link className="student-service-back" to="/student">{t('servicePage.back')} ←</Link>
      </div>
      <p>{t(descriptionKey)}</p>
      <section className="student-service-placeholder">
        <PortalIcon name={icon} size={42} />
        <h2>{t('servicePage.readyTitle')}</h2>
        <p>{t('servicePage.readyDescription')}</p>
        {serviceUrl && <a className="student-service-open" href={serviceUrl}>ورود به سرویس ←</a>}
      </section>
    </div>
  );
}
