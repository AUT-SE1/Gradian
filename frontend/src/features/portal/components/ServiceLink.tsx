import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { serviceHref, type Service } from '../api/panelApi';

// Embed enters the existing protected service route. Redirect leaves the portal
// as a normal full-page navigation, even when hosted on the same origin.
export function ServiceLink({ service, path, className, children }: {
  service?: Service; path: string; className: string; children: ReactNode;
}) {
  const href = serviceHref(service);
  if (!href) return <article className={className} aria-disabled="true">{children}</article>;
  return service?.mode === 'embed'
    ? <Link className={className} to={path}>{children}</Link>
    : <a className={className} href={href} referrerPolicy="no-referrer">{children}</a>;
}
