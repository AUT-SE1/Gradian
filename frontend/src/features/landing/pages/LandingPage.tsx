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
    </div>
  );
}
