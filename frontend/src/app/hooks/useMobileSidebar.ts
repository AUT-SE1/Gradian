import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';

const MOBILE_QUERY = '(max-width: 780px)';
const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function useMobileSidebar() {
  const { key: locationKey } = useLocation();
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches);
  const [requestedOpen, setRequestedOpen] = useState(false);
  const sidebarRef = useRef<HTMLElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const isOpen = isMobile && requestedOpen;
  const close = useCallback(() => setRequestedOpen(false), []);
  const open = useCallback(() => setRequestedOpen(true), []);

  useEffect(() => {
    const media = window.matchMedia(MOBILE_QUERY);
    const onChange = () => {
      setIsMobile(media.matches);
      close();
    };
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, [close]);

  // Also handles back/forward navigation, not only clicks in the menu.
  useEffect(close, [locationKey, close]);

  useEffect(() => {
    const sidebar = sidebarRef.current;
    if (!isOpen || !sidebar) return;
    const trigger = triggerRef.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const items = () => Array.from(sidebar.querySelectorAll<HTMLElement>(FOCUSABLE))
      .filter((element) => element.getClientRects().length > 0);
    const focusFirst = () => (items()[0] ?? sidebar).focus({ preventScroll: true });
    // Wait until the drawer is visible; avoid scrolling the document while its
    // entrance transform is still animating.
    const focusFrame = requestAnimationFrame(focusFirst);

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault();
        close();
      } else if (event.key === 'Tab') {
        const targets = items();
        const first = targets[0];
        const last = targets.at(-1);
        if (!first || !last) {
          event.preventDefault();
          sidebar?.focus();
        } else if (event.shiftKey && (document.activeElement === first || document.activeElement === sidebar)) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    }
    function onFocusIn(event: FocusEvent) {
      if (event.target instanceof Node && !sidebar?.contains(event.target)) focusFirst();
    }
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('focusin', onFocusIn);
    return () => {
      cancelAnimationFrame(focusFrame);
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('focusin', onFocusIn);
      document.body.style.overflow = previousOverflow;
      // Resizing to desktop hides the trigger; never focus a hidden control.
      if (trigger?.isConnected && trigger.getClientRects().length) trigger.focus();
    };
  }, [isOpen, close]);

  return { isMobile, isOpen, sidebarRef, triggerRef, open, close };
}
