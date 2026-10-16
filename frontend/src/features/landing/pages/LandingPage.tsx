import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import nikpourImage from '@/assets/images/faculty-nikpour.png';
import rahmaniImage from '@/assets/images/faculty-rahmani.png';
import mirsadeghiImage from '@/assets/images/faculty-mirsadeghi.png';

const statKeys = ['students', 'satisfaction', 'ranks', 'authors'] as const;
const missionKeys = ['scientific', 'analytics', 'justice'] as const;
const teacherKeys = ['soltani', 'mirsadeghi', 'rahmani', 'nikpour'] as const;
const testimonialKeys = ['ghanbari', 'movahedian', 'motamedi'] as const;

const teacherImages: Record<(typeof teacherKeys)[number], string | null> = {
  soltani: null,
  mirsadeghi: mirsadeghiImage,
  rahmani: rahmaniImage,
  nikpour: nikpourImage,
};

export function LandingPage() {
  const { t } = useTranslation('common');

  return (
    <div className="landing-page">
      <header className="landing-header">
        <div className="landing-welcome">{t('landing.header.welcome')}</div>
        <nav className="landing-nav" aria-label={t('landing.header.navLabel')}>
          <span className="landing-nav-active">{t('landing.header.home')}</span>
          <span>{t('landing.header.about')}</span>
          <span>{t('landing.header.services')}</span>
          <span>{t('landing.header.contact')}</span>
        </nav>
        <Link className="landing-start-button" to="/login">{t('landing.header.start')}</Link>
      </header>

      <section className="landing-hero-section">
        <div className="landing-hero-copy">
          <h1>{t('landing.hero.title')}</h1>
          <p>{t('landing.hero.subtitle')}</p>
          <Link className="landing-portal-button" to="/login">
            <span>{t('landing.hero.portal')}</span><span aria-hidden="true">↩</span>
          </Link>
        </div>

        <div className="landing-stat-grid">
          {statKeys.map((key) => (
            <article className="landing-stat-card" key={key}>
              <strong>{t(`landing.stats.${key}.value`)}</strong>
              <span>{t(`landing.stats.${key}.label`)}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-mission-section">
        <div className="landing-mission-copy">
          <span className="landing-section-eyebrow">{t('landing.mission.eyebrow')}</span>
          <h2>{t('landing.mission.title')}</h2>
          <p>{t('landing.mission.description')}</p>
          <div className="landing-mission-badges">
            <span>{t('landing.mission.badgeOne')}</span>
            <span>{t('landing.mission.badgeTwo')}</span>
          </div>
        </div>
        <div className="landing-principles">
          {missionKeys.map((key, index) => (
            <article className={`landing-principle-card landing-principle-card--${index + 1}`} key={key}>
              <span className="landing-principle-icon" aria-hidden="true">{index === 0 ? '♙' : index === 1 ? '◉' : '◇'}</span>
              <h3>{t(`landing.mission.cards.${key}.title`)}</h3>
              <p>{t(`landing.mission.cards.${key}.description`)}</p>
              <small>{t(`landing.mission.cards.${key}.footer`)}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-faculty-section">
        <div className="landing-section-heading">
          <h2>{t('landing.faculty.title')}</h2>
          <p>{t('landing.faculty.subtitle')}</p>
        </div>
        <div className="landing-faculty-grid">
          {teacherKeys.map((key) => (
            <article className="landing-faculty-card" key={key}>
              <div className={`landing-faculty-photo${teacherImages[key] ? '' : ' landing-faculty-photo--empty'}`}>
                {teacherImages[key] ? <img src={teacherImages[key]!} alt="" /> : null}
                <span>{t(`landing.faculty.${key}.badge`)}</span>
              </div>
              <div className="landing-faculty-body">
                <small>{t(`landing.faculty.${key}.role`)}</small>
                <h3>{t(`landing.faculty.${key}.name`)}</h3>
                <p>{t(`landing.faculty.${key}.bio`)}</p>
                <strong>{t(`landing.faculty.${key}.metric`)}</strong>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-testimonials-section">
        <div className="landing-section-heading">
          <h2>{t('landing.testimonials.title')}</h2>
          <p>{t('landing.testimonials.subtitle')}</p>
        </div>
        <div className="landing-testimonials-grid">
          {testimonialKeys.map((key) => (
            <article className="landing-testimonial-card" key={key}>
              <div className="testimonial-rating"><span>۹۹</span><span>★★★★★</span></div>
              <p>{t(`landing.testimonials.${key}.text`)}</p>
              <div className="testimonial-person">
                <span>{t(`landing.testimonials.${key}.initial`)}</span>
                <div><strong>{t(`landing.testimonials.${key}.name`)}</strong><small>{t(`landing.testimonials.${key}.role`)}</small></div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
