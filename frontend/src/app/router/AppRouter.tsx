import type { ReactNode } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { PublicLayout } from '@/app/layouts/PublicLayout';
import { PortalLayout } from '@/app/layouts/PortalLayout';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { AuthCallbackPage } from '@/features/auth/pages/AuthCallbackPage';
import { LandingPage } from '@/features/landing/pages/LandingPage';
import { PortalHomePage } from '@/features/portal/pages/PortalHomePage';
import { ServicePage } from '@/features/portal/components/ServicePage';
import { useAuth } from '@/app/providers/AuthProvider';
import { isUsableSession } from '@/shared/auth/session';
import type { PortalRole } from '@/shared/types/portal';

function ProtectedPortal({ portal, children }: { portal: PortalRole; children: ReactNode }) {
  const { session } = useAuth();
  if (!isUsableSession(session)) return <Navigate to="/login" replace />;
  if (session.user.primaryRole !== portal) {
    return <Navigate to={`/${session.user.primaryRole}`} replace />;
  }
  return <>{children}</>;
}

function LegacyPortalRedirect({ from, to }: { from: string; to: string }) {
  const location = useLocation();
  return <Navigate to={{ pathname: to + location.pathname.slice(from.length), search: location.search, hash: location.hash }} replace />;
}

export function AppRouter() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
      </Route>

      <Route path="/student" element={<ProtectedPortal portal="student"><PortalLayout portal="student" /></ProtectedPortal>}>
        <Route index element={<PortalHomePage portal="student" />} />
        <Route path="exams" element={<ServicePage titleKey="pages.exams.title" descriptionKey="pages.exams.description" icon="exam" serviceUrl="http://localhost:8001/app" />} />
        <Route path="question-bank" element={<ServicePage titleKey="pages.questionBank.title" descriptionKey="pages.questionBank.description" icon="book" serviceUrl="http://localhost:8002/app" />} />
        <Route path="final-exams" element={<ServicePage titleKey="pages.finalExams.title" descriptionKey="pages.finalExams.description" icon="exam" serviceUrl="http://localhost:8003/app" />} />
        <Route path="private-class" element={<ServicePage titleKey="pages.privateClass.title" descriptionKey="pages.privateClass.description" icon="video" serviceUrl="http://localhost:8004/app" />} />
        <Route path="marketplace" element={<ServicePage titleKey="pages.marketplace.title" descriptionKey="pages.marketplace.description" icon="store" serviceUrl="http://localhost:8006/app" />} />
        <Route path="consultation" element={<ServicePage titleKey="pages.consultation.title" descriptionKey="pages.consultation.description" icon="message" serviceUrl="http://localhost:8005/app" />} />
        <Route path="major-selection" element={<ServicePage titleKey="pages.majorSelection.title" descriptionKey="pages.majorSelection.description" icon="target" serviceUrl="http://localhost:8009/app" />} />
        <Route path="top-ranker" element={<ServicePage titleKey="pages.topRanker.title" descriptionKey="pages.topRanker.description" icon="star" serviceUrl="http://localhost:8010/app" />} />
        <Route path="courses" element={<ServicePage titleKey="pages.courses.title" descriptionKey="pages.courses.description" icon="video" serviceUrl="http://localhost:8008/app" />} />
        <Route path="community" element={<ServicePage titleKey="pages.community.title" descriptionKey="pages.community.description" icon="users" serviceUrl="http://localhost:8010/app" />} />
      </Route>

      <Route path="/instructor" element={<ProtectedPortal portal="instructor"><PortalLayout portal="instructor" /></ProtectedPortal>}>
        <Route index element={<PortalHomePage portal="instructor" />} />
        <Route path="profile" element={<ServicePage titleKey="pages.profile.title" descriptionKey="pages.profile.description" icon="settings" serviceUrl="http://localhost:8010/app" />} />
        <Route path="progress" element={<ServicePage titleKey="pages.progress.title" descriptionKey="pages.progress.description" icon="chart" serviceUrl="http://localhost:8007/app" />} />
        <Route path="questions" element={<ServicePage titleKey="pages.questionManagement.title" descriptionKey="pages.questionManagement.description" icon="exam" serviceUrl="http://localhost:8008/app" />} />
        <Route path="courses" element={<ServicePage titleKey="pages.courseCreation.title" descriptionKey="pages.courseCreation.description" icon="video" serviceUrl="http://localhost:8010/app" />} />
        <Route path="private-class" element={<ServicePage titleKey="pages.privateClass.title" descriptionKey="pages.privateClass.description" icon="users" serviceUrl="http://localhost:8004/app" />} />
        <Route path="resources" element={<ServicePage titleKey="pages.resources.title" descriptionKey="pages.resources.description" icon="book" serviceUrl="http://localhost:8006/app" />} />
      </Route>

      <Route path="/counsellor" element={<ProtectedPortal portal="counsellor"><PortalLayout portal="counsellor" /></ProtectedPortal>}>
        <Route index element={<PortalHomePage portal="counsellor" />} />
        <Route path="profile" element={<ServicePage titleKey="pages.profile.title" descriptionKey="pages.profile.description" icon="settings" serviceUrl="http://localhost:8010/app" />} />
        <Route path="students" element={<ServicePage titleKey="pages.studentReports.title" descriptionKey="pages.studentReports.description" icon="chart" serviceUrl="http://localhost:8007/app" />} />
        <Route path="experiences" element={<ServicePage titleKey="pages.experiences.title" descriptionKey="pages.experiences.description" icon="star" serviceUrl="http://localhost:8010/app" />} />
        <Route path="troubleshooting" element={<ServicePage titleKey="pages.troubleshooting.title" descriptionKey="pages.troubleshooting.description" icon="message" serviceUrl="http://localhost:8008/app" />} />
        <Route path="sessions" element={<ServicePage titleKey="pages.sessions.title" descriptionKey="pages.sessions.description" icon="calendar" serviceUrl="http://localhost:8005/app" />} />
        <Route path="resources" element={<ServicePage titleKey="pages.resources.title" descriptionKey="pages.resources.description" icon="book" serviceUrl="http://localhost:8006/app" />} />
      </Route>

      <Route path="/admin" element={<ProtectedPortal portal="admin"><PortalLayout portal="admin" /></ProtectedPortal>}>
        <Route index element={<PortalHomePage portal="admin" />} />
        <Route path="exams" element={<ServicePage titleKey="pages.examManagement.title" descriptionKey="pages.examManagement.description" icon="exam" serviceUrl="http://localhost:8002/app" />} />
        <Route path="sessions" element={<ServicePage titleKey="pages.sessions.title" descriptionKey="pages.sessions.description" icon="calendar" serviceUrl="http://localhost:8005/app" />} />
        <Route path="products" element={<ServicePage titleKey="pages.products.title" descriptionKey="pages.products.description" icon="store" serviceUrl="http://localhost:8006/app" />} />
      </Route>

      <Route path="/professor/*" element={<LegacyPortalRedirect from="/professor" to="/instructor" />} />
      <Route path="/consultant/*" element={<LegacyPortalRedirect from="/consultant" to="/counsellor" />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
