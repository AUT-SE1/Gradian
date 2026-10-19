import { useId, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import type { PortalRole } from '@/shared/types/portal';

type Props = { portal: PortalRole; displayName: string; onLogout: () => void };

export function PortalHeaderActions({ portal, displayName, onLogout }: Props) {
  const { t } = useTranslation('navigation');
  const dialogRef = useRef<HTMLDialogElement>(null);
  const notificationId = useId();
  const titleId = useId();
  const student = portal === 'student';

  return (
    <>
      <div className={student ? 'student-header-actions' : 'management-header-actions'}>
        <button className="portal-bell" type="button" aria-label={t('notifications')} aria-haspopup="dialog" aria-controls={notificationId} onClick={() => dialogRef.current?.showModal()}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
          </svg>
        </button>
        <div className={student ? 'student-user-summary' : 'management-user-summary'}>
          <strong title={displayName}>{displayName}</strong><small>{t(`roleLabels.${portal}`)}</small>
        </div>
        <button className="portal-logout-icon" type="button" onClick={onLogout} aria-label={t('logout')}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M9 5H4v14h5M8 12h13m-4-4 4 4-4 4" />
          </svg>
        </button>
      </div>
      <dialog className="portal-notifications-dialog" id={notificationId} ref={dialogRef} aria-labelledby={titleId} onClick={(event) => {
        const rect = event.currentTarget.getBoundingClientRect();
        if (event.target === event.currentTarget && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) event.currentTarget.close();
      }}>
        <div className="portal-dialog-heading"><h2 id={titleId}>{t('notifications')}</h2><button type="button" onClick={() => dialogRef.current?.close()} aria-label={t('closeNotifications')}>×</button></div>
        <p>{t('notificationsUnavailable')}</p>
      </dialog>
    </>
  );
}
