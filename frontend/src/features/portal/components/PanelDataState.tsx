import { useTranslation } from 'react-i18next';
import { ApiError } from '@/shared/api/ApiError';

type Props = { pending: boolean; error: Error | null; retry: () => unknown; empty?: boolean };
export function PanelDataState({ pending, error, retry, empty }: Props) {
  const { t } = useTranslation('navigation');
  if (error) return <div className="portal-data-state" role="alert">{t(error instanceof ApiError && error.status === 403 ? 'dataForbidden' : error instanceof ApiError && error.status === 401 ? 'dataUnauthorized' : 'dataError')} <button type="button" onClick={() => { void retry(); }}>{t('dataRetry')}</button></div>;
  if (pending || empty) return <div className="portal-data-state" role="status">{t(pending ? 'dataLoading' : 'dataEmpty')}</div>;
  return null;
}
