import { Navigate, Route, Routes } from 'react-router-dom';
import { PublicLayout } from '@/app/layouts/PublicLayout';
import { PortalLayout } from '@/app/layouts/PortalLayout';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { LandingPage } from '@/features/landing/pages/LandingPage';
import { PortalHomePage } from '@/features/portal/pages/PortalHomePage';

export function AppRouter() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Route>
      <Route path="/student" element={<PortalLayout portal="student" />}>
        <Route index element={<PortalHomePage portal="student" />} />
      </Route>
      <Route path="/instructor" element={<PortalLayout portal="instructor" />}>
        <Route index element={<PortalHomePage portal="instructor" />} />
      </Route>
      <Route path="/counsellor" element={<PortalLayout portal="counsellor" />}>
        <Route index element={<PortalHomePage portal="counsellor" />} />
      </Route>
      <Route path="/admin" element={<PortalLayout portal="admin" />}>
        <Route index element={<PortalHomePage portal="admin" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
