import { useState } from 'react';
import { Link, Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/app/providers/ThemeProvider';
import { useI18n } from '@/app/providers/I18nProvider';
import type { PortalRole } from '@/shared/types/portal';

type Props = { portal: PortalRole };

export function PortalLayout({ portal }: Props) {
  const { t } = useTranslation('navigation');
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useI18n();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  function closeMobileSidebar() {
    setIsMobileSidebarOpen(false);
  }

  return (
    <div className={`portal-shell portal-shell--${portal}${isSidebarCollapsed ? ' portal-shell--sidebar-collapsed' : ''}${isMobileSidebarOpen ? ' portal-shell--mobile-sidebar-open' : ''}`}>
      <button
        className="sidebar-overlay"
        type="button"
        aria-label={t('closeSidebar')}
        onClick={closeMobileSidebar}
      />
      <aside className="portal-sidebar" aria-label={t('mainMenu')}>
        <div className="sidebar-topbar">
          <Link className="brand" to={`/${portal}`} onClick={closeMobileSidebar}>
            <span className="brand-mark">گ</span>
            <span className="sidebar-label">گرادیان</span>
          </Link>
          <button
            className="sidebar-close-button"
            type="button"
            aria-label={t('closeSidebar')}
            onClick={closeMobileSidebar}
          >
            ×
          </button>
        </div>
        <button
          className="sidebar-collapse-button"
          type="button"
          aria-label={isSidebarCollapsed ? t('expandSidebar') : t('collapseSidebar')}
          aria-expanded={!isSidebarCollapsed}
          onClick={() => setIsSidebarCollapsed((current) => !current)}
        >
          <span aria-hidden="true">{isSidebarCollapsed ? '»' : '«'}</span>
          <span className="sidebar-label">{isSidebarCollapsed ? t('expandSidebar') : t('collapseSidebar')}</span>
        </button>
        <nav>
          <Link to={`/${portal}`} onClick={closeMobileSidebar}>
            <span aria-hidden="true">⌂</span>
            <span className="sidebar-label">{t('overview')}</span>
          </Link>
        </nav>
      </aside>
      <section className="portal-content">
        <header className="portal-header">
          <div className="portal-heading">
            <button
              className="mobile-menu-button"
              type="button"
              aria-label={t('openSidebar')}
              aria-expanded={isMobileSidebarOpen}
              onClick={() => setIsMobileSidebarOpen(true)}
            >
              ☰
            </button>
            <strong>{t(`portals.${portal}`)}</strong>
          </div>
          <div className="portal-actions">
            <button type="button" onClick={toggleLanguage}>{language === 'fa' ? 'EN' : 'فا'}</button>
            <button type="button" onClick={toggleTheme}>{theme === 'light' ? 'Dark' : 'Light'}</button>
            <Link to="/" onClick={closeMobileSidebar}>{t('logout')}</Link>
          </div>
        </header>
        <main className="page-content"><Outlet /></main>
      </section>
    </div>
  );
}
