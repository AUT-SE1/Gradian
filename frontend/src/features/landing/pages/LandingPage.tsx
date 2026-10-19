import { useTranslation } from "react-i18next";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { httpClient } from "@/shared/api/httpClient";
import { QueryState } from "@/shared/api/QueryState";
import { login, register } from "@/features/auth/oidc";
import { errorMessage } from "@/shared/api/authedClient";
import { useAuth } from "@/app/providers/AuthProvider";
import type { Landing } from "@/shared/types/content";
export function LandingPage() {
  const { t } = useTranslation("common");
  const { me } = useAuth();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const query = useQuery({
    queryKey: ["landing"],
    queryFn: () => httpClient.get<Landing>("/landing"),
    staleTime: Infinity,
  });
  const data = query.data;
  async function start(action: () => Promise<void>) {
    setError("");
    setPending(true);
    try {
      await action();
    } catch (failure) {
      setError(errorMessage(failure));
      setPending(false);
    }
  }
  return (
    <div id="home" className="landing-page">
      <QueryState
        pending={query.isPending}
        error={query.error}
        retry={query.refetch}
      />
      {error && <p role="alert">{error}</p>}
      <nav className="landing-nav">
        {data?.navbar && (
          <>
            <strong>{data.navbar.brand}</strong>
            {data.navbar.links.map((link) => (
              <a key={link.href} href={link.href}>
                {link.label}
              </a>
            ))}
          </>
        )}
        {me ? (
          <Link className="primary-button" to={me.home_path}>
            {t("ui.myPanel")}
          </Link>
        ) : (
          <>
            <button
              className="primary-button"
              disabled={pending}
              onClick={() => void start(login)}
            >
              {data?.navbar?.login_label || t("ui.login")}
            </button>
            <button disabled={pending} onClick={() => void start(register)}>
              {data?.navbar?.register_label || t("ui.register")}
            </button>
          </>
        )}
      </nav>
      {data?.hero && (
        <section className="content-card">
          <span className="eyebrow">{data.hero.eyebrow}</span>
          <h1>{data.hero.title}</h1>
          <p>{data.hero.subtitle}</p>
          {data.hero.image_url && (
            <img className="hero-image" src={data.hero.image_url} alt="" />
          )}
          <button
            className="primary-button"
            disabled={pending}
            onClick={() => void start(register)}
          >
            {data.hero.primary_cta_label}
          </button>{" "}
          <button disabled={pending} onClick={() => void start(login)}>
            {data.hero.secondary_cta_label}
          </button>
        </section>
      )}
      <div id="statistics" className="service-grid">
        {data?.statistics?.map((item) => (
          <article className="content-card" key={item.key}>
            <strong>{item.value}</strong>
            <p>{item.label}</p>
          </article>
        ))}
      </div>
      <div id="mission" className="service-grid">
        {data?.missions?.map((item) => (
          <article className="content-card" key={item.title}>
            <h2>{item.title}</h2>
            <p>{item.description}</p>
          </article>
        ))}
      </div>
      <div id="teachers" className="service-grid">
        {data?.teachers?.map((item) => (
          <article className="content-card" key={item.name}>
            {item.avatar_url && (
              <img className="avatar" src={item.avatar_url} alt="" />
            )}
            <h2>{item.name}</h2>
            <strong>{item.title}</strong>
            <p>{item.bio}</p>
          </article>
        ))}
      </div>
      <div id="rankers" className="service-grid">
        {data?.rankers?.map((item) => (
          <article className="content-card" key={item.name}>
            {item.avatar_url && (
              <img className="avatar" src={item.avatar_url} alt="" />
            )}
            <h2>{item.name}</h2>
            <p>
              {item.rank} · {item.field}
            </p>
            <blockquote>{item.quote}</blockquote>
          </article>
        ))}
      </div>
      <div id="testimonials" className="service-grid">
        {data?.testimonials?.map((item) => (
          <article className="content-card" key={item.name}>
            {item.avatar_url && (
              <img className="avatar" src={item.avatar_url} alt="" />
            )}
            <h2>{item.name}</h2>
            <strong>{item.role}</strong>
            <blockquote>{item.text}</blockquote>
          </article>
        ))}
      </div>
      {data?.footer && (
        <footer className="content-card">
          <p>{data.footer.description}</p>
          {data.footer.links.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}{" "}
            </a>
          ))}
          <p>{data.footer.copyright}</p>
        </footer>
      )}
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
