import type { NavigationIcon } from '@/app/navigation/navigation.config';

export function PortalIcon({ name, size = 20 }: { name: NavigationIcon; size?: number }) {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true };
  const paths: Record<NavigationIcon, React.ReactNode> = {
    course: <><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6h14M5 18h14"/></>,
    classroom: <><rect x="3" y="4" width="18" height="16" rx="1"/><circle cx="9" cy="10" r="2"/><path d="M5 17v-1a4 4 0 0 1 8 0v1M15 8h3M15 12h3"/></>,
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    experience: <><path d="M4 4h16v13H9l-5 4z"/><path d="m8 13 2-5 3 5 3-5"/></>,
    help: <><path d="M4 3h16v15h-6l-4 4v-4H4z"/><path d="M9 8a3 3 0 0 1 6 0c0 2-3 2-3 4M12 15h.01"/></>,
    headset: <><path d="M4 13V11a8 8 0 0 1 16 0v5c0 4-3 5-8 5"/><rect x="2" y="11" width="4" height="7" rx="2"/><rect x="18" y="11" width="4" height="7" rx="2"/><path d="M8 10a4 4 0 0 1 8 0M9 16c2 2 4 2 6 0"/></>,
    library: <><path d="m3 12 9 4 9-4M3 16l9 5 9-5M3 12v8l9 4 9-4v-8"/><circle cx="12" cy="5" r="3"/></>,
    alarm: <><circle cx="12" cy="13" r="8"/><path d="m9 13 2 2 4-5M3 4l3-2M18 2l3 2M6 20l-2 2M18 20l2 2"/></>,
    verified: <><path d="m12 2 3 2 3 .5.5 3L21 11l-1.5 3 .5 3-3 1.5-2 2.5-3-1-3 1L7 18.5 4 17l.5-3L3 11l2.5-3.5.5-3L9 4z"/><path d="m8 11 3 3 5-6"/></>,
    home: <><path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V21h13V9.5"/><path d="M9.5 21v-6h5v6"/></>,
    exam: <><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h5M8 16h7"/></>,
    book: <><path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H11v17H7.5A3.5 3.5 0 0 0 4 22z"/><path d="M20 5.5A3.5 3.5 0 0 0 16.5 2H13v17h3.5A3.5 3.5 0 0 1 20 22z"/></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18"/></>,
    users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></>,
    chart: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></>,
    message: <><path d="M21 15a4 4 0 0 1-4 4H8l-5 3 1.5-5A7 7 0 0 1 3 12V8a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/></>,
    briefcase: <><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5h6v2M3 12h18"/></>,
    video: <><rect x="3" y="5" width="14" height="14" rx="2"/><path d="m17 10 4-2v8l-4-2z"/></>,
    star: <><path d="m12 3 2.6 5.27 5.82.85-4.21 4.1.99 5.8L12 16.27 6.8 19l1-5.78-4.22-4.1 5.82-.85z"/></>,
    plus: <><path d="M12 5v14M5 12h14"/></>,
    store: <><path d="M4 10v10h16V10M3 10l2-6h14l2 6"/><path d="M3 10a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M9 20v-6h6v6"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21H9.6v-.1A1.7 1.7 0 0 0 8.5 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.1 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H2V9.6h.1A1.7 1.7 0 0 0 4.1 8.5a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 8.5 4.1a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V2h4v.1A1.7 1.7 0 0 0 15 4.1a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 8.5c.15.38.37.72.65 1 .3.27.7.42 1.1.4H21v4h-.1A1.7 1.7 0 0 0 19.4 15z"/></>,
    target: <><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M22 12h-3M12 22v-3M2 12h3"/></>,
  };
  return <svg {...common}>{paths[name]}</svg>;
}
