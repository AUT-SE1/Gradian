import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthProvider';
import { authApi } from '@/features/auth/api/authApi';
import { portalNavigationGroups } from '@/app/navigation/navigation.config';
import { PortalIcon } from '@/features/portal/components/PortalIcon';
import type { PortalRole } from '@/shared/types/portal';

type Props = { portal: PortalRole };

function BellIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
      <path d="M10 21h4" />
    </svg>
  );
}

const fallbackNames: Record<PortalRole, string> = {
  student: 'علیرضا رضایی',
  instructor: 'سارا احمدی‌تبار',
  counsellor: 'سارا احمدی‌تبار',
  admin: 'سارا احمدی‌تبار',
};

export function PortalLayout({ portal }: Props) {
  const { t } = useTranslation('navigation');
  const { session, setSession } = useAuth();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const displayName = session?.user.displayName || fallbackNames[portal];

  function logout() {
    const idToken = session?.idToken;
    setSession(null);
    setIsMobileSidebarOpen(false);
    void authApi.logout(idToken);
  }

  if (portal === 'student') {
    return (
      <div className="student-portal-shell">
        <header className="student-portal-header">
          <div className="student-brand-block">
            <strong>{t('brandFa')}</strong>
            <small>{t('studentPanel')}</small>
          </div>
          <div className="student-header-actions">
            <button className="portal-bell" type="button" aria-label={t('notifications')}><span /><BellIcon /></button>
            <div className="student-user-summary"><strong>{displayName}</strong><small>{t('studentField')}</small></div>
            <button className="portal-logout-icon" type="button" onClick={logout} aria-label={t('logout')}>↪</button>
          </div>
        </header>
        <main className="student-page-content"><Outlet /></main>
      </div>
    );
  }

  const groups = portalNavigationGroups[portal];

  return (
    <div className={`management-portal-shell management-portal-shell--${portal}${isMobileSidebarOpen ? ' is-sidebar-open' : ''}`}>
      <button className="management-sidebar-overlay" type="button" aria-label={t('closeSidebar')} onClick={() => setIsMobileSidebarOpen(false)} />
      <aside className="management-sidebar">
        <div className="management-logo">{t('brandFa')}</div>
        {portal !== 'admin' && (
          <NavLink className="profile-complete-nav" to={`/${portal}/profile`} onClick={() => setIsMobileSidebarOpen(false)}>
            <span><PortalIcon name="settings" size={15} />{t('profileComplete')}</span><small>۸۰٪ ←</small>
          </NavLink>
        )}
        <nav className="management-nav" aria-label={t('mainMenu')}>
          {groups.map((group) => (
            <div className="management-nav-group" key={group.id}>
              <span className="management-nav-label">{t(group.labelKey)}</span>
              {group.items.map((item) => (
                <NavLink key={item.id} to={item.path} onClick={() => setIsMobileSidebarOpen(false)}>
                  <PortalIcon name={item.icon} size={17} />
                  <span>{t(item.labelKey)}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-countdown-widget">
          <span className="sidebar-countdown-icon">◉</span>
          <div><strong>{t('countdownTitle')}</strong><small>{t('countdownValue')}</small></div>
        </div>
      </aside>

      <section className="management-content">
        <header className="management-header">
          <button className="mobile-menu-button" type="button" aria-label={t('openSidebar')} onClick={() => setIsMobileSidebarOpen(true)}>☰</button>
          <div className="management-header-actions">
            <button className="portal-logout-icon" type="button" onClick={logout} aria-label={t('logout')}>↪</button>
            <div className="management-user-summary"><strong>{displayName}</strong><small>{t(`roleLabels.${portal}`)}</small></div>
            <button className="portal-bell" type="button" aria-label={t('notifications')}><span /><BellIcon /></button>
          </div>
        </header>
        <main className="management-workspace"><Outlet /></main>
      </section>
    </div>
  );
}
