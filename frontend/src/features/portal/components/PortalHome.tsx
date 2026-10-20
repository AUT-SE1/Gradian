import { countdownText } from '@/features/portal/api/panelAdapters';
import { usePanelServices, useStudentDashboard } from '../hooks/usePanelData';
import { serviceKeys } from '../api/serviceRoutes';
import { serviceHref } from '../api/panelApi';
import { PanelDataState } from './PanelDataState';
import { useTranslation } from 'react-i18next';
import type { PortalRole } from '@/shared/types/portal';
import { dashboardCards } from '@/features/portal/config/portalContent';
import { PortalIcon } from './PortalIcon';
import { StudentIcon } from './StudentIcon';

export function PortalHome({ portal }: { portal: PortalRole }) {
  const { t, i18n } = useTranslation('portal');
  const { t: tn } = useTranslation('navigation');
  const services = usePanelServices();
  const dashboard = useStudentDashboard();
  const data = dashboard.isError ? undefined : dashboard.data;
  const number = (value: number) => value.toLocaleString(i18n.language);

  if (portal !== 'student') {
    return <div className="management-empty-canvas"><span className="sr-only">{t(`home.${portal}.title`)}</span></div>;
  }

  return (
    <div className="student-dashboard-page">
      <PanelDataState pending={dashboard.isPending} error={dashboard.error} retry={dashboard.refetch} />
      <section className="student-welcome-card">
        <div className="student-welcome-copy">
          <h1>{data?.welcome?.message ?? t('home.student.title')}</h1>
          {data?.welcome?.tip && <p>{data.welcome.tip}</p>}
        </div>
        <div className="student-welcome-widgets">
          <article><span><StudentIcon name="streak" /></span><div><small>{t('studentDashboard.streakLabel')}</small><strong title={data?.study_streak?.message}>{data?.study_streak ? `${number(data.study_streak.current_days)} ${t('studentDashboard.day')}` : t('studentDashboard.widgetUnavailable')}</strong></div></article>
          <article><span><PortalIcon name="calendar" size={20} /></span><div><small>{t('studentDashboard.countdownLabel')}</small><strong>{data?.countdown ? countdownText(data.countdown, i18n.language) : tn('countdownUnavailable')}</strong></div></article>
        </div>
      </section>

      <div className="student-section-heading">
        <span><StudentIcon name="grid" /></span><h2>{t('studentDashboard.servicesTitle')}</h2>
      </div>

      <PanelDataState pending={services.isPending} error={services.error} retry={services.refetch} empty={services.data?.length === 0} />
      <section className="student-service-grid">
        {!services.isPending && !services.isError && services.data?.length !== 0 && dashboardCards.student.map((card) => {
          const service = services.data?.find(entry => entry.key === serviceKeys[card.path]);
          const href = serviceHref(service);
          const content = (
            <>
              <div className="student-service-card-top">
                <span className={`service-icon service-icon--${card.accent || 'blue'}`}><PortalIcon name={card.icon} size={18} /></span>
                <small>{service?.status === 'unavailable' ? tn('serviceUnavailable') : ''}</small>
              </div>
              <h3>{t(card.titleKey)}</h3>
              <p>{service?.description || t(card.descriptionKey)}</p>
              <div className="student-service-card-footer">
                <span aria-hidden="true" />
                <strong>{href ? (service?.button_label || (card.actionKey ? t(card.actionKey) : '')) : tn('serviceUnavailable')} {href ? '←' : ''}</strong>
              </div>
            </>
          );
          return href ? (
            <a className={`student-service-card student-service-card--${card.accent}`} href={href} key={card.titleKey}>{content}</a>
          ) : (
            <article className={`student-service-card student-service-card--${card.accent}`} aria-disabled="true" key={card.titleKey}>{content}</article>
          );
        })}
      </section>

      <section className="student-community-section">
        <div className="student-community-heading">
          <div><span><StudentIcon name="community" /></span><h2>{t('studentDashboard.communityTitle')}</h2></div>
          </div>
        <div className="student-community-controls">
          <div className="student-community-tabs" role="group" aria-label={t('studentDashboard.communityTitle')}>
            {['tabTop', 'tabMy', 'tabAll'].map((tab, index) => <button key={tab} type="button" disabled className={index === 0 ? 'active' : undefined}>{t(`studentDashboard.${tab}`)}</button>)}
          </div>
          <small className="student-preview-note">{t('studentDashboard.previewNotice')}</small>
        </div>
        {!dashboard.isPending && !dashboard.isError && <PanelDataState pending={false} error={null} retry={dashboard.refetch} empty={!data?.experience_feed?.length} />}
        <div className="student-post-grid">
          {data?.experience_feed?.map((post, index) => (
            <article className="student-post-card" key={post.id}>
              <div className="post-author-row">
                <span className={`post-avatar post-avatar--${index % 3 + 1}`} aria-hidden="true">{Array.from(post.author.trim())[0]}</span>
                <div><strong>{post.author}</strong><small>{post.author_title}</small></div>
              </div>
              <h3>{post.title}</h3>
              <p>{post.excerpt}</p>
              <div className="post-stats" aria-label={t('studentDashboard.previewStats')}><span><StudentIcon name="heart" /> {number(post.likes)}</span><span><StudentIcon name="comment" /> {number(post.comments)}</span></div>
            </article>
          ))}
        </div>
        <a className="student-community-cta" aria-disabled={services.isError || !serviceHref(services.data?.find(entry => entry.key === serviceKeys['/student/community']))} href={!services.isError ? serviceHref(services.data?.find(entry => entry.key === serviceKeys['/student/community'])) : undefined}>
          <span>{t('studentDashboard.communityCta')}</span><strong>{!services.isError && serviceHref(services.data?.find(entry => entry.key === serviceKeys['/student/community'])) ? `${t('studentDashboard.communityAction')} ←` : tn('serviceUnavailable')}</strong>
        </a>
      </section>
    </div>
  );
}
