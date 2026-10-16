import type { PortalRole } from '@/shared/types/portal';
import type { NavigationIcon } from '@/app/navigation/navigation.config';

export type DashboardCard = {
  titleKey: string;
  descriptionKey: string;
  icon: NavigationIcon;
  path: string;
  accent?: string;
  eyebrowKey?: string;
  metaKey?: string;
  actionKey?: string;
  serviceUrl?: string;
};

export const dashboardCards: Record<PortalRole, DashboardCard[]> = {
  student: [
    { titleKey: 'cards.mockExam.title', descriptionKey: 'cards.mockExam.description', icon: 'exam', path: '/student/exams', serviceUrl: 'http://localhost:8001/app', accent: 'orange', eyebrowKey: 'cards.mockExam.eyebrow', metaKey: 'cards.mockExam.meta', actionKey: 'cards.mockExam.action' },
    { titleKey: 'cards.topicExam.title', descriptionKey: 'cards.topicExam.description', icon: 'book', path: '/student/question-bank', serviceUrl: 'http://localhost:8002/app', accent: 'blue', eyebrowKey: 'cards.topicExam.eyebrow', metaKey: 'cards.topicExam.meta', actionKey: 'cards.topicExam.action' },
    { titleKey: 'cards.finalExam.title', descriptionKey: 'cards.finalExam.description', icon: 'exam', path: '/student/final-exams', serviceUrl: 'http://localhost:8003/app', accent: 'violet', eyebrowKey: 'cards.finalExam.eyebrow', metaKey: 'cards.finalExam.meta', actionKey: 'cards.finalExam.action' },
    { titleKey: 'cards.privateClass.title', descriptionKey: 'cards.privateClass.description', icon: 'video', path: '/student/private-class', serviceUrl: 'http://localhost:8004/app', accent: 'cyan', eyebrowKey: 'cards.privateClass.eyebrow', metaKey: 'cards.privateClass.meta', actionKey: 'cards.privateClass.action' },
    { titleKey: 'cards.marketplace.title', descriptionKey: 'cards.marketplace.description', icon: 'book', path: '/student/marketplace', serviceUrl: 'http://localhost:8006/app', accent: 'blue', eyebrowKey: 'cards.marketplace.eyebrow', metaKey: 'cards.marketplace.meta', actionKey: 'cards.marketplace.action' },
    { titleKey: 'cards.consultation.title', descriptionKey: 'cards.consultation.description', icon: 'message', path: '/student/consultation', serviceUrl: 'http://localhost:8005/app', accent: 'violet', eyebrowKey: 'cards.consultation.eyebrow', metaKey: 'cards.consultation.meta', actionKey: 'cards.consultation.action' },
    { titleKey: 'cards.majorSelection.title', descriptionKey: 'cards.majorSelection.description', icon: 'target', path: '/student/major-selection', serviceUrl: 'http://localhost:8009/app', accent: 'cyan', eyebrowKey: 'cards.majorSelection.eyebrow', metaKey: 'cards.majorSelection.meta', actionKey: 'cards.majorSelection.action' },
    { titleKey: 'cards.topRanker.title', descriptionKey: 'cards.topRanker.description', icon: 'star', path: '/student/top-ranker', serviceUrl: 'http://localhost:8010/app', accent: 'blue', eyebrowKey: 'cards.topRanker.eyebrow', metaKey: 'cards.topRanker.meta', actionKey: 'cards.topRanker.action' },
    { titleKey: 'cards.courses.title', descriptionKey: 'cards.courses.description', icon: 'video', path: '/student/courses', serviceUrl: 'http://localhost:8008/app', accent: 'blue', eyebrowKey: 'cards.courses.eyebrow', metaKey: 'cards.courses.meta', actionKey: 'cards.courses.action' },
  ],
  instructor: [],
  counsellor: [],
  admin: [],
};
