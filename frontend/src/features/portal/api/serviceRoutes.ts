// Explicit mapping verified against backend/seed/content/services.yaml.
// A title, team number or old hardcoded port is never a service identifier.
export const serviceKeys: Record<string, string> = {
  '/student/exams': 'student.simulated-exam', '/student/question-bank': 'student.topic-exam',
  '/student/final-exams': 'student.final-exam-12th', '/student/private-class': 'student.private-class',
  '/student/marketplace': 'student.marketplace', '/student/consultation': 'student.counseling-planning',
  '/student/major-selection': 'student.major-selection', '/student/top-ranker': 'student.top-ranker-experiences',
  '/student/courses': 'student.courses', '/student/community': 'student.experience-exchange',
  '/instructor/profile': 'professor.profile', '/instructor/progress': 'professor.progress-dashboard',
  '/instructor/questions': 'professor.exam-question-management', '/instructor/courses': 'professor.create-course',
  '/instructor/private-class': 'professor.private-class', '/instructor/resources': 'professor.resources-hub',
  '/counsellor/profile': 'consultant.profile', '/counsellor/students': 'consultant.student-reports',
  '/counsellor/experiences': 'consultant.add-experiences', '/counsellor/troubleshooting': 'consultant.resolve-problems',
  '/counsellor/sessions': 'consultant.counseling-sessions', '/counsellor/resources': 'consultant.resources-hub',
  '/admin/exams': 'admin.exam-bank', '/admin/sessions': 'admin.counseling-sessions', '/admin/products': 'admin.store-management',
};
