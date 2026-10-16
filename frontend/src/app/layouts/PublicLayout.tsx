import { Outlet } from 'react-router-dom';

export function PublicLayout() {
  return (
    <div className="public-shell">
      <main className="public-main"><Outlet /></main>
    </div>
  );
}
