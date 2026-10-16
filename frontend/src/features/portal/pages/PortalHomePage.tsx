import type { PortalRole } from '@/shared/types/portal';
import { PortalHome } from '@/features/portal/components/PortalHome';

export function PortalHomePage({ portal }: { portal: PortalRole }) {
  return <PortalHome portal={portal} />;
}
