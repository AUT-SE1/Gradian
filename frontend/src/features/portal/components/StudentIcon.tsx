// Decorative dashboard icons; no platform-dependent text glyphs.
export function StudentIcon({ name }: { name: 'streak' | 'grid' | 'community' | 'heart' | 'comment' | 'bookmark' | 'attachment' }) {
  const shapes = {
    streak: <path d="M13 3c1 5-4 5-2 9 2-1 3-3 3-3 5 5 4 11-2 12-7 0-9-8-4-12 0 3 1 4 1 4-1-5 4-6 4-10Z" />,
    grid: <><rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="3" width="6" height="6" rx="1"/><rect x="3" y="15" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/></>,
    community: <><path d="M4 4h16v13H9l-5 4V4Z"/><path d="M8 8h8M8 12h6"/></>,
    heart: <path d="M12 21 4 13C-3 6 7-2 12 6c5-8 15 0 8 7Z"/>,
    comment: <path d="M3 4h18v13H9l-6 4V4Z"/>,
    bookmark: <path d="M6 3h12v18l-6-4-6 4V3Z"/>,
    attachment: <><rect x="9" y="2" width="6" height="13" rx="3"/><path d="M6 11v1a6 6 0 0 0 12 0v-1M12 18v4M9 22h6"/></>,
  };
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{shapes[name]}</svg>;
}
