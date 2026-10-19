import { useTranslation } from "react-i18next";
import { Navigate, Route, Routes, Outlet, Link } from "react-router-dom";
import { PublicLayout } from "@/app/layouts/PublicLayout";
import { PortalLayout } from "@/app/layouts/PortalLayout";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { AuthCallbackPage } from "@/features/auth/pages/AuthCallbackPage";
import { LandingPage } from "@/features/landing/pages/LandingPage";
import { PortalHomePage } from "@/features/portal/pages/PortalHomePage";
import { useAuth } from "@/app/providers/AuthProvider";
import { errorMessage } from "@/shared/api/authedClient";
import type { PortalRole } from "@/shared/types/portal";
function RequirePanel({ panel }: { panel: PortalRole }) {
  const { t } = useTranslation("common");
  const { me, loading, error, reload } = useAuth();
  if (loading) return <p role="status">{t("ui.checkingAccess")}</p>;
  if (error)
    return (
      <section className="placeholder-page">
        <p role="alert">{errorMessage(error)}</p>
        <p>{t("ui.supportHint")}</p>
        <button onClick={() => void reload().catch(() => {})}>
          {t("ui.retry")}
        </button>{" "}
        <Link to="/login">{t("ui.loginAgain")}</Link>
      </section>
    );
  if (!me) return <Navigate to="/login" replace />;
  if (me.panel !== panel)
    return (
      <section className="placeholder-page">
        <h1>{t("ui.noAccess")}</h1>
        <p>{t("ui.otherRole")}</p>
        <Link to={me.home_path}>{t("ui.goToMyPanel")}</Link>
      </section>
    );
  return <Outlet />;
}
export function AppRouter() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
      </Route>
      {(["student", "consultant", "professor", "admin"] as const).map(
        (panel) => (
          <Route key={panel} element={<RequirePanel panel={panel} />}>
            <Route path={`/${panel}`} element={<PortalLayout portal={panel} />}>
              <Route index element={<PortalHomePage portal={panel} />} />
            </Route>
          </Route>
        ),
      )}
      <Route
        path="/instructor"
        element={<Navigate to="/professor" replace />}
      />
      <Route
        path="/counsellor"
        element={<Navigate to="/consultant" replace />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
