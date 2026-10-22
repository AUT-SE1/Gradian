import { useId, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { usePanelData, useNotifications } from '@/features/portal/hooks/usePanelData';
import { PAGE_SIZE } from '@/features/portal/api/panelApi';
import { PanelDataState } from '@/features/portal/components/PanelDataState';
import type { PortalRole } from '@/shared/types/portal';

type Props = { portal: PortalRole; displayName: string; onLogout: () => void };

export function PortalHeaderActions({ portal, displayName, onLogout }: Props) {
  const [offset, setOffset] = useState(0);
  const [failedAvatar, setFailedAvatar] = useState('');
  const panel = usePanelData();
  const notifications = useNotifications(offset);
  const { t, i18n } = useTranslation('navigation');
  const dialogRef = useRef<HTMLDialogElement>(null);
  const notificationId = useId();
  const titleId = useId();
  const student = portal === 'student';

  const header = panel.data?.header;
  const avatar = header?.avatar_url;
  const roleLabel = portal === 'counsellor' && header?.consultant_type ? t(header.consultant_type === 'top_ranker' ? 'topRankerRole' : 'consultantRole') : t(`roleLabels.${portal}`);
  return (
    <>
      <div className={student ? 'student-header-actions' : 'management-header-actions'}>
        <button className="portal-bell" type="button" aria-label={t('notifications')} aria-haspopup="dialog" aria-controls={notificationId} onClick={() => dialogRef.current?.showModal()}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
          </svg>
          {!!notifications.data?.unread_count && !notifications.isError && <span className="portal-unread-dot" aria-label={t('unreadCount', { count: notifications.data.unread_count })} />}
        </button>
        {avatar && avatar !== failedAvatar && /^https?:|^\//.test(avatar) && <img className="portal-user-avatar" src={avatar} alt="" referrerPolicy="no-referrer" onError={() => setFailedAvatar(avatar)} />}
        <div className={student ? 'student-user-summary' : 'management-user-summary'}>
          <strong title={displayName}>{displayName}</strong><small>{portal === 'student' && header?.field_of_study_label ? header.field_of_study_label : roleLabel}</small>
        </div>
        <button className="portal-logout-icon" type="button" onClick={onLogout} aria-label={t('logout')}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M9 5H4v14h5M8 12h13m-4-4 4 4-4 4" />
          </svg>
        </button>
      </div>
      <PanelDataState pending={panel.isPending} error={panel.error} retry={panel.refetch} />
      <dialog className="portal-notifications-dialog" id={notificationId} ref={dialogRef} aria-labelledby={titleId} onClick={(event) => {
        const rect = event.currentTarget.getBoundingClientRect();
        if (event.target === event.currentTarget && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) event.currentTarget.close();
      }}>
        <div className="portal-dialog-heading"><h2 id={titleId}>{t('notifications')}</h2><button type="button" onClick={() => dialogRef.current?.close()} aria-label={t('closeNotifications')}>×</button></div>
        <PanelDataState pending={notifications.isPending} error={notifications.error} retry={notifications.refetch} empty={notifications.data?.results.length === 0} />
        {!notifications.isError && notifications.data && <>
          <p>{t('unreadCount', { count: notifications.data.unread_count })}</p>
          <ul className="portal-notification-list">{notifications.data.results.map(item => <li key={item.id} data-unread={!item.is_read}>
            <strong>{item.title}</strong><p>{item.body}</p><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString(i18n.language)}</time>
          </li>)}</ul>
          <div className="portal-notification-pagination">
            <button type="button" disabled={!notifications.data.previous} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>{t('previousPage')}</button>
            <button type="button" disabled={!notifications.data.next} onClick={() => setOffset(offset + PAGE_SIZE)}>{t('nextPage')}</button>
          </div>
        </>}
      </dialog>
    </>
  );
}
