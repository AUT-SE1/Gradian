import type { PortalRole } from '@/shared/types/portal';

export type NavigationIcon =
  | 'home' | 'exam' | 'book' | 'calendar' | 'users' | 'chart' | 'message'
  | 'briefcase' | 'video' | 'star' | 'plus' | 'store' | 'settings' | 'target';

export type NavigationItem = {
  id: string;
  labelKey: string;
  path: string;
  icon: NavigationIcon;
};

export type NavigationGroup = {
  id: string;
  labelKey: string;
  items: NavigationItem[];
};

export const portalNavigation: Record<PortalRole, NavigationItem[]> = {
  student: [
    { id: 'mock-exam', labelKey: 'menu.mockExam', path: '/student/exams', icon: 'exam' },
    { id: 'topic-exam', labelKey: 'menu.topicExam', path: '/student/question-bank', icon: 'book' },
    { id: 'final-exam', labelKey: 'menu.finalExam', path: '/student/final-exams', icon: 'exam' },
    { id: 'private-class', labelKey: 'menu.privateClass', path: '/student/private-class', icon: 'video' },
    { id: 'marketplace', labelKey: 'menu.marketplace', path: '/student/marketplace', icon: 'store' },
    { id: 'consultation', labelKey: 'menu.consultation', path: '/student/consultation', icon: 'message' },
    { id: 'major-selection', labelKey: 'menu.majorSelection', path: '/student/major-selection', icon: 'target' },
    { id: 'top-ranker', labelKey: 'menu.topRanker', path: '/student/top-ranker', icon: 'star' },
    { id: 'courses', labelKey: 'menu.courses', path: '/student/courses', icon: 'video' },
    { id: 'community', labelKey: 'menu.community', path: '/student/community', icon: 'users' },
  ],
  instructor: [
    { id: 'progress', labelKey: 'menu.educationalProgress', path: '/instructor/progress', icon: 'chart' },
    { id: 'questions', labelKey: 'menu.questionManagement', path: '/instructor/questions', icon: 'exam' },
    { id: 'courses', labelKey: 'menu.courseCreation', path: '/instructor/courses', icon: 'video' },
    { id: 'private-class', labelKey: 'menu.privateClass', path: '/instructor/private-class', icon: 'users' },
    { id: 'resources', labelKey: 'menu.resourceHub', path: '/instructor/resources', icon: 'book' },
  ],
  counsellor: [
    { id: 'students', labelKey: 'menu.studentReports', path: '/counsellor/students', icon: 'chart' },
    { id: 'experiences', labelKey: 'menu.experiences', path: '/counsellor/experiences', icon: 'message' },
    { id: 'troubleshooting', labelKey: 'menu.troubleshooting', path: '/counsellor/troubleshooting', icon: 'book' },
    { id: 'sessions', labelKey: 'menu.consultationSessions', path: '/counsellor/sessions', icon: 'message' },
    { id: 'resources', labelKey: 'menu.resourceHub', path: '/counsellor/resources', icon: 'book' },
  ],
  admin: [
    { id: 'exams', labelKey: 'menu.examBank', path: '/admin/exams', icon: 'exam' },
    { id: 'sessions', labelKey: 'menu.consultationSessions', path: '/admin/sessions', icon: 'message' },
    { id: 'products', labelKey: 'menu.products', path: '/admin/products', icon: 'store' },
  ],
};

export const portalNavigationGroups: Record<'instructor' | 'counsellor' | 'admin', NavigationGroup[]> = {
  instructor: [
    { id: 'work', labelKey: 'groups.workAndLearning', items: portalNavigation.instructor.slice(0, 2) },
    { id: 'education', labelKey: 'groups.educationalServices', items: portalNavigation.instructor.slice(2) },
  ],
  counsellor: [
    { id: 'work', labelKey: 'groups.workAndLearning', items: portalNavigation.counsellor.slice(0, 3) },
    { id: 'guidance', labelKey: 'groups.guidanceServices', items: portalNavigation.counsellor.slice(3) },
  ],
  admin: [
    { id: 'work', labelKey: 'groups.workAndLearning', items: portalNavigation.admin.slice(0, 1) },
    { id: 'guidance', labelKey: 'groups.guidanceServices', items: portalNavigation.admin.slice(1) },
  ],
};
