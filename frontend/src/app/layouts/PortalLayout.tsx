import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/app/providers/AuthProvider";
import { logout } from "@/features/auth/oidc";
import { portalApi, serviceUrl } from "@/features/portal/api/portalApi";
import { errorMessage } from "@/shared/api/authedClient";
import { QueryState } from "@/shared/api/QueryState";
import { useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useTheme } from "@/app/providers/ThemeProvider";
import { useI18n } from "@/app/providers/I18nProvider";
import type { PortalRole } from "@/shared/types/portal";

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
  const { me } = useAuth();
  const [logoutError, setLogoutError] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);
  const [offset, setOffset] = useState(0);
  const panel = useQuery({
    queryKey: ["panel", me?.sub, portal],
    queryFn: portalApi.panel,
  });
  const services = useQuery({
    queryKey: ["services", me?.sub, portal],
    queryFn: portalApi.services,
  });
  const notifications = useQuery({
    queryKey: ["notifications", me?.sub, offset],
    queryFn: () => portalApi.notifications(offset),
  });
  const { t: ui } = useTranslation("common");
  const { t } = useTranslation("navigation");
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useI18n();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
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
    <div
      className={`portal-shell portal-shell--${portal}${isSidebarCollapsed ? " portal-shell--sidebar-collapsed" : ""}${isMobileSidebarOpen ? " portal-shell--mobile-sidebar-open" : ""}`}
    >
      <button
        className="sidebar-overlay"
        type="button"
        aria-label={t("closeSidebar")}
        onClick={closeMobileSidebar}
      />
      <aside className="portal-sidebar" aria-label={t("mainMenu")}>
        <div className="sidebar-topbar">
          <Link
            className="brand"
            to={`/${portal}`}
            onClick={closeMobileSidebar}
          >
            <span className="brand-mark">گ</span>
            <span className="sidebar-label">گرادیان</span>
          </Link>
          <button
            className="sidebar-close-button"
            type="button"
            aria-label={t("closeSidebar")}
            onClick={closeMobileSidebar}
          >
            ×
          </button>
        </div>
        <button
          className="sidebar-collapse-button"
          type="button"
          aria-label={
            isSidebarCollapsed ? t("expandSidebar") : t("collapseSidebar")
          }
          aria-expanded={!isSidebarCollapsed}
          onClick={() => setIsSidebarCollapsed((current) => !current)}
        >
          <span aria-hidden="true">{isSidebarCollapsed ? "»" : "«"}</span>
          <span className="sidebar-label">
            {isSidebarCollapsed ? t("expandSidebar") : t("collapseSidebar")}
          </span>
        </button>
        <nav>
          <Link to={`/${portal}`} onClick={closeMobileSidebar}>
            <span aria-hidden="true">⌂</span>
            <span className="sidebar-label">{t("overview")}</span>
          </Link>
          {services.data?.results.map((service) => {
            const url = serviceUrl(service);
            return url ? (
              <a key={service.key} href={url} title={service.title_fa}>
                <span aria-hidden="true">↗</span>
                <span className="sidebar-label">
                  {language === "fa" ? service.title_fa : service.title_en}
                </span>
              </a>
            ) : (
              <span
                className="unavailable-service"
                key={service.key}
                title={ui("ui.unavailable")}
              >
                <span aria-hidden="true">○</span>
                <span className="sidebar-label">
                  {language === "fa" ? service.title_fa : service.title_en}
                </span>
              </span>
            );
          })}
          <QueryState
            pending={services.isPending}
            error={services.error}
            retry={services.refetch}
          />
        </nav>
        {panel.data && (
          <p className="sidebar-label">{panel.data.countdown.label}</p>
        )}
      </aside>
      <section className="portal-content">
        <header className="portal-header">
          <div className="portal-heading">
            <button
              className="mobile-menu-button"
              type="button"
              aria-label={t("openSidebar")}
              aria-expanded={isMobileSidebarOpen}
              onClick={() => setIsMobileSidebarOpen(true)}
            >
              ☰
            </button>
            <strong>{t(`portals.${portal}`)}</strong>
            <span>{panel.data?.header.full_name || me?.full_name}</span>
            {panel.data?.header.avatar_url && (
              <img
                className="avatar"
                src={panel.data.header.avatar_url}
                alt=""
              />
            )}
            <span>{panel.data?.header.field_of_study_label}</span>
          </div>
          <div className="portal-actions">
            <button type="button" onClick={toggleLanguage}>
              {language === "fa" ? "EN" : "فا"}
            </button>
            <button type="button" onClick={toggleTheme}>
              {theme === "light" ? "Dark" : "Light"}
            </button>
            <button
              onClick={() => setShowNotifications((value) => !value)}
              aria-expanded={showNotifications}
            >
              {ui("ui.notifications")} (
              {notifications.data?.unread_count ?? "…"})
            </button>
            <button
              onClick={() => {
                setLogoutError("");
                void logout().catch((failure: unknown) =>
                  setLogoutError(errorMessage(failure)),
                );
              }}
            >
              {t("logout")}
            </button>
          </div>
        </header>
        <main className="page-content">
          {logoutError && <p role="alert">{logoutError}</p>}
          <QueryState
            pending={panel.isPending}
            error={panel.error}
            retry={panel.refetch}
          />
          {showNotifications && (
            <section className="content-card">
              <h2>{ui("ui.notifications")}</h2>
              <QueryState
                pending={notifications.isPending}
                error={notifications.error}
                retry={notifications.refetch}
              />
              {notifications.data?.results.map((item) => (
                <article key={item.id}>
                  <strong>{item.title}</strong>
                  <p>{item.body}</p>
                  <time dateTime={item.created_at}>
                    {new Date(item.created_at).toLocaleString(
                      language === "fa" ? "fa-IR" : "en-US",
                    )}
                  </time>
                </article>
              ))}
              {notifications.data?.count === 0 && (
                <p>{ui("ui.noNotifications")}</p>
              )}
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - 20))}
              >
                {ui("ui.previous")}
              </button>{" "}
              <button
                disabled={!notifications.data?.next}
                onClick={() => setOffset(offset + 20)}
              >
                {ui("ui.next")}
              </button>
            </section>
          )}
          <Outlet />
        </main>
      </section>
    </div>
  );
}
