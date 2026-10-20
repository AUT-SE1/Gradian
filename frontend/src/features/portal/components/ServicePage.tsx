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
  const embedded = !!serviceUrl && service?.mode === 'embed';
  // Preserve storage for cross-origin services; never combine scripts and same-origin
  // privileges for a service sharing the portal origin.
  const frameSandbox = 'allow-scripts allow-forms allow-popups' + (serviceUrl && new URL(serviceUrl).origin !== window.location.origin ? ' allow-same-origin' : '');
  const destination = serviceUrl && <>
    <p role="status">{tn('serviceAvailable')}</p>
    {embedded && <><p>{tn('embedNotice')}</p><iframe key={serviceUrl} className="portal-service-frame" src={serviceUrl} title={t(titleKey)} sandbox={frameSandbox} referrerPolicy="no-referrer" /></>}
    <a className={location.pathname.startsWith('/student') ? 'student-service-open' : 'management-service-open'} href={serviceUrl} referrerPolicy="no-referrer">{tn(embedded ? 'openServiceSeparately' : 'openService')} ←</a>
  </>;
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
          {destination}
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
        <h2>{tn('openService')}</h2>
        {state}
          {destination}
      </section>
    </div>
  );
}
