import { usePanelServices } from '../hooks/usePanelData';
import { serviceKeys } from '../api/serviceRoutes';
import { serviceHref } from '../api/panelApi';
import { PanelDataState } from './PanelDataState';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PortalIcon } from './PortalIcon';
import type { NavigationIcon } from '@/app/navigation/navigation.config';

export function ServicePage({
  titleKey,
  descriptionKey,
  icon = 'briefcase',
}: {
  titleKey: string;
  descriptionKey: string;
  icon?: NavigationIcon;
}) {
  const { t } = useTranslation('portal');
  const location = useLocation();
  const { t: tn } = useTranslation('navigation');
  const services = usePanelServices();
  const service = services.data?.find(entry => entry.key === serviceKeys[location.pathname.replace(/\/$/, '')]);
  const serviceUrl = !services.isError ? serviceHref(service) : undefined;
  const state = <><PanelDataState pending={services.isPending} error={services.error} retry={services.refetch} />{services.isSuccess && !serviceUrl && <p role="status">{tn('serviceUnavailable')}</p>}</>;
  const isStudent = location.pathname.startsWith('/student');

  if (!isStudent) {
    return (
      <div className="management-service-canvas">
        <section className="management-service-card">
          <span className="service-icon service-icon--blue"><PortalIcon name={icon} size={24} /></span>
          <h1>{t(titleKey)}</h1>
          <p>{t(descriptionKey)}</p>
          {state}
          {serviceUrl && <a className="management-service-open" href={serviceUrl}>{tn('openService')} ←</a>}
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
        {state}
          {serviceUrl && <a className="student-service-open" href={serviceUrl}>{tn('openService')} ←</a>}
      </section>
    </div>
  );
}
