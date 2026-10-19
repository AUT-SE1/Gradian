import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { PortalRole } from '@/shared/types/portal';
import { dashboardCards } from '@/features/portal/config/portalContent';
import { PortalIcon } from './PortalIcon';

const postKeys = ['rahbar', 'amirhossein', 'zahra'] as const;

export function PortalHome({ portal }: { portal: PortalRole }) {
  const { t } = useTranslation('portal');

  if (portal !== 'student') {
    return <div className="management-empty-canvas"><span className="sr-only">{t(`home.${portal}.title`)}</span></div>;
  }

  return (
    <div className="student-dashboard-page">
      <section className="student-welcome-card">
        <div className="student-welcome-copy">
          <h1>{t('studentDashboard.welcomeTitle')}</h1>
          <p>{t('studentDashboard.welcomeSubtitle')}</p>
        </div>
        <div className="student-welcome-widgets">
          <article><span>◇</span><div><small>{t('studentDashboard.streakLabel')}</small><strong>۱۸ {t('studentDashboard.day')}</strong></div></article>
          <article><span>▣</span><div><small>{t('studentDashboard.countdownLabel')}</small><strong>۹۴ {t('studentDashboard.day')}</strong></div></article>
        </div>
      </section>

      <div className="student-section-heading">
        <span>⌘</span><h2>{t('studentDashboard.servicesTitle')}</h2>
      </div>

      <section className="student-service-grid">
        {dashboardCards.student.map((card) => {
          const content = (
            <>
              <div className="student-service-card-top">
                <span className={`service-icon service-icon--${card.accent || 'blue'}`}><PortalIcon name={card.icon} size={18} /></span>
                <small>{card.eyebrowKey ? t(card.eyebrowKey) : ''}</small>
              </div>
              <h3>{t(card.titleKey)}</h3>
              <p>{t(card.descriptionKey)}</p>
              <div className="student-service-card-footer">
                <span>{card.metaKey ? t(card.metaKey) : ''}</span>
                <strong>{card.actionKey ? t(card.actionKey) : ''} ←</strong>
              </div>
            </>
          );
          return card.serviceUrl ? (
            <a className="student-service-card" href={card.serviceUrl} key={card.titleKey}>{content}</a>
          ) : (
            <Link className="student-service-card" to={card.path} key={card.titleKey}>{content}</Link>
          );
        })}
      </section>

      <section className="student-community-section">
        <div className="student-community-heading">
          <div><span>▣</span><h2>{t('studentDashboard.communityTitle')}</h2></div>
          <div className="student-community-tabs"><span className="active">{t('studentDashboard.tabTop')}</span><span>{t('studentDashboard.tabMy')}</span><span>{t('studentDashboard.tabAll')}</span></div>
        </div>
        <div className="student-post-grid">
          {postKeys.map((key, index) => (
            <article className="student-post-card" key={key}>
              <div className="post-author-row">
                <span className={`post-avatar post-avatar--${index + 1}`}>{t(`studentDashboard.posts.${key}.initial`)}</span>
                <div><strong>{t(`studentDashboard.posts.${key}.name`)}</strong><small>{t(`studentDashboard.posts.${key}.meta`)}</small></div>
              </div>
              <h3>{t(`studentDashboard.posts.${key}.title`)}</h3>
              <p>{t(`studentDashboard.posts.${key}.text`)}</p>
              <small className="post-tags">{t(`studentDashboard.posts.${key}.tags`)}</small>
              <div className="post-stats"><span>♡ {index === 0 ? '۳۳۹' : index === 1 ? '۷۳' : '۵۳'}</span><span>□ {index === 0 ? '۶۵' : index === 1 ? '۳۳' : '۲۸'}</span><span>⌑</span></div>
            </article>
          ))}
        </div>
        <a className="student-community-cta" href="http://localhost:8010/app">
          <span>{t('studentDashboard.communityCta')}</span><strong>{t('studentDashboard.communityAction')} ←</strong>
        </a>
      </section>
    </div>
  );
}
