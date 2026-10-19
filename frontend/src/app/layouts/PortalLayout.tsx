import { countdownText } from '@/features/portal/api/panelAdapters';
import { startTransition, useId } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthProvider';
import { authApi } from '@/features/auth/api/authApi';
import { portalNavigationGroups } from '@/app/navigation/navigation.config';
import { PortalIcon } from '@/features/portal/components/PortalIcon';
import { useMobileSidebar } from '@/app/hooks/useMobileSidebar';
import { PortalHeaderActions } from './PortalHeaderActions';
import { usePanelData, usePanelServices } from '@/features/portal/hooks/usePanelData';
import { serviceKeys } from '@/features/portal/api/serviceRoutes';
import { serviceHref } from '@/features/portal/api/panelApi';
import { PanelDataState } from '@/features/portal/components/PanelDataState';
import type { PortalRole } from '@/shared/types/portal';

type Props = { portal: PortalRole };

export function PortalLayout({ portal }: Props) {
  const { t, i18n } = useTranslation('navigation');
  const { session, setSession } = useAuth();
  const navigate = useNavigate();
  const sidebar = useMobileSidebar();
  const sidebarId = useId();
  const sidebarTitleId = useId();
  const mainId = useId();
  const panel = usePanelData();
  const services = usePanelServices();
  const displayName = panel.data?.header.full_name.trim() || t('unknownUser');

  function logout() {
    const idToken = session?.idToken;
    sidebar.close();
    // Leave the protected route before clearing the session so /login does not
    // start a fresh sign-in while the end-session request is pending.
    startTransition(() => {
      navigate('/', { replace: true });
      setSession(null);
    });
    void authApi.logout(idToken);
  }

  if (portal === 'student') {
    return (
      <div className="student-portal-shell">
        <a className="portal-skip-link" href={`#${mainId}`}>{t('skipToContent')}</a>
        <header className="student-portal-header">
          <Link className="student-brand-block" to="/student" aria-label={t('portalHome')}>
            <strong>{t('brandFa')}</strong><small>{t('studentPanel')}</small>
          </Link>
          <PortalHeaderActions portal={portal} displayName={displayName} onLogout={logout} />
        </header>
        <main className="student-page-content" id={mainId} tabIndex={-1}><Outlet /></main>
      </div>
    );
  }

  return (
    <div className={`management-portal-shell management-portal-shell--${portal}${sidebar.isOpen ? ' is-sidebar-open' : ''}`}>
      <a className="portal-skip-link" href={`#${mainId}`}>{t('skipToContent')}</a>
      <button className="management-sidebar-overlay" type="button" tabIndex={-1} aria-hidden="true" onClick={sidebar.close} />
      <aside className="management-sidebar" id={sidebarId} ref={sidebar.sidebarRef} tabIndex={-1}
        role={sidebar.isMobile ? 'dialog' : undefined} aria-modal={sidebar.isOpen ? true : undefined}
        aria-labelledby={sidebarTitleId} aria-hidden={sidebar.isMobile && !sidebar.isOpen ? true : undefined}
        inert={sidebar.isMobile && !sidebar.isOpen}>
        <h2 className="sr-only" id={sidebarTitleId}>{t('mainMenu')}</h2>
        <div className="management-brand-row">
          <Link className="management-logo" to={`/${portal}`} onClick={sidebar.close} aria-label={t('portalHome')}>{t('brandFa')}</Link>
          <button className="management-sidebar-close" type="button" onClick={sidebar.close} aria-label={t('closeSidebar')}>×</button>
        </div>
        {portal !== 'admin' && (
          <NavLink className="profile-complete-nav" to={`/${portal}/profile`} onClick={sidebar.close}>
            <span><PortalIcon name="settings" size={15} />{t('profileComplete')}</span><small aria-hidden="true">←</small>
          </NavLink>
        )}
        <nav className="management-nav" aria-label={t('mainMenu')}>
          <PanelDataState pending={services.isPending} error={services.error} retry={services.refetch} empty={services.data?.length === 0} />
          {portalNavigationGroups[portal].map((group) => (
            <div className="management-nav-group" key={group.id}>
              <span className="management-nav-label">{t(group.labelKey)}</span>
              {group.items.map((item) => {
                const service = services.data?.find(entry => entry.key === serviceKeys[item.path]);
                if (services.isPending || services.isError || !serviceHref(service)) return <span className="management-nav-disabled" key={item.id} aria-disabled="true"><PortalIcon name={item.icon} size={17} /><span>{t(item.labelKey)}<small>{t('serviceUnavailable')}</small></span></span>;
                return (
                <NavLink key={item.id} to={item.path} onClick={sidebar.close}>
                  <PortalIcon name={item.icon} size={17} /><span>{t(item.labelKey)}</span>
                </NavLink>
              ); })}
            </div>
          ))}
        </nav>
        <div className="sidebar-countdown-widget">
          <span className="sidebar-countdown-icon" aria-hidden="true"><PortalIcon name="calendar" size={22} /></span>
          <div><strong>{t('countdownTitle')}</strong><small>{panel.data ? (countdownText(panel.data.countdown, i18n.language)) : t('countdownUnavailable')}</small><PanelDataState pending={panel.isPending} error={panel.error} retry={panel.refetch} /></div>
        </div>
      </aside>
      <section className="management-content" inert={sidebar.isOpen}>
        <header className="management-header">
          <button className="mobile-menu-button" type="button" ref={sidebar.triggerRef} aria-label={t('openSidebar')} aria-expanded={sidebar.isOpen} aria-controls={sidebarId} aria-haspopup="dialog" onClick={sidebar.open}>☰</button>
          <PortalHeaderActions portal={portal} displayName={displayName} onLogout={logout} />
        </header>
        <main className="management-workspace" id={mainId} tabIndex={-1}><Outlet /></main>
      </section>
    </div>
  );
}
