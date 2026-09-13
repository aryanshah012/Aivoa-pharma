import { api } from './client';
import type { Analysis, Complaint, ComplaintDraft, DashboardStats } from '../types';

export const complaintsApi = {
  list: (params: Record<string, string>) => api.get<Complaint[]>('/api/complaints', { params }).then(r => r.data),
  get: (id: number) => api.get<Complaint>(`/api/complaints/${id}`).then(r => r.data),
  create: (draft: ComplaintDraft) => api.post<Complaint>('/api/complaints', draft).then(r => r.data),
  update: (id: number, patch: Partial<Complaint>) => api.put<Complaint>(`/api/complaints/${id}`, patch).then(r => r.data),
  analyze: (text: string) => api.post<Analysis>('/api/complaints/analyze', { text }).then(r => r.data),
  analyzeDocument: (file: File) => {
    const fd = new FormData(); fd.append('file', file);
    return api.post<Analysis>('/api/complaints/analyze-document', fd).then(r => r.data);
  },
  stats: () => api.get<DashboardStats>('/api/dashboard/stats').then(r => r.data),
  recent: () => api.get<Complaint[]>('/api/dashboard/recent').then(r => r.data),
};
export const progressMessages = [
  'Reading complaint...', 'Extracting details...', 'Checking completeness...',
  'Assessing risk...', 'Checking similar complaints...', 'Generating recommendations...', 'Summarizing...',
];
