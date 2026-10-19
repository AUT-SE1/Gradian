import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/app/providers/AuthProvider";
import { portalApi, serviceUrl } from "../api/portalApi";
import { QueryState } from "@/shared/api/QueryState";
import type { PortalRole } from "@/shared/types/portal";
export function PortalHomePage({ portal }: { portal: PortalRole }) {
  const { me } = useAuth();
  const { t: ui } = useTranslation("common");
  const { t, i18n } = useTranslation("navigation");
  const services = useQuery({
    queryKey: ["services", me?.sub, portal],
    queryFn: portalApi.services,
  });
  const dashboard = useQuery({
    queryKey: ["dashboard", me?.sub, portal],
    queryFn: portalApi.dashboard,
    enabled: portal === "student",
  });
  return (
    <section className="panel-page">
      <h1>{t(`portals.${portal}`)}</h1>
      {portal === "student" && (
        <>
          <QueryState
            pending={dashboard.isPending}
            error={dashboard.error}
            retry={dashboard.refetch}
          />
          {dashboard.data && (
            <>
              {dashboard.data.welcome && (
                <article className="content-card">
                  <h2>{dashboard.data.welcome.message}</h2>
                  <p>{dashboard.data.welcome.tip}</p>
                </article>
              )}
              <p>{dashboard.data.countdown.label}</p>
              {dashboard.data.study_streak && (
                <article className="content-card">
                  <h2>{ui("ui.studyStreak")}</h2>
                  <p>{dashboard.data.study_streak.message}</p>
                  <p>
                    {ui("ui.streakCounts", {
                      current: dashboard.data.study_streak.current_days,
                      best: dashboard.data.study_streak.best_days,
                    })}
                  </p>
                  <ul>
                    {dashboard.data.study_streak.week.map((day) => (
                      <li key={day.day}>
                        {day.day}: {day.done ? "✓" : "—"}
                      </li>
                    ))}
                  </ul>
                </article>
              )}
              {dashboard.data.experience_feed?.map((item) => (
                <article className="content-card" key={item.id}>
                  <h2>{item.title}</h2>
                  <p>{item.excerpt}</p>
                  <small>
                    {item.author} — {item.author_title} |{" "}
                    {ui("ui.feedCounts", {
                      likes: item.likes,
                      comments: item.comments,
                    })}
                  </small>
                </article>
              ))}
            </>
          )}
        </>
      )}
      <h2>{ui("ui.services")}</h2>
      <QueryState
        pending={services.isPending}
        error={services.error}
        retry={services.refetch}
      />
      {services.data?.count === 0 && <p>{ui("ui.noServices")}</p>}
      <div className="service-grid">
        {services.data?.results.map((service) => {
          const url = serviceUrl(service);
          return (
            <article className="content-card" key={service.key}>
              <h3>
                {i18n.language.startsWith("fa")
                  ? service.title_fa
                  : service.title_en}
              </h3>
              <p>{service.description}</p>
              {url ? (
                <a className="primary-button" href={url}>
                  {service.button_label}
                </a>
              ) : (
                <button disabled>{ui("ui.unavailable")}</button>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
import type { PortalRole } from '@/shared/types/portal';
import { PortalHome } from '@/features/portal/components/PortalHome';

export function PortalHomePage({ portal }: { portal: PortalRole }) {
  return <PortalHome portal={portal} />;
}
