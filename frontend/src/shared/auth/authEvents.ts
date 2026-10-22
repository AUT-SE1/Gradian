// Only authenticated requests report a 401, with their original token. An old
// request must never invalidate a different user's new session.
const listeners = new Set<(accessToken: string) => void>();

export function reportUnauthorized(accessToken: string) {
  for (const listener of listeners) listener(accessToken);
}

export function onUnauthorized(listener: (accessToken: string) => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
