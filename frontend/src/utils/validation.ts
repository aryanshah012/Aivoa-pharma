import type { ComplaintDraft } from '../types';

export const REQUIRED_KEYS = ['customer_name', 'product_name', 'complaint_type', 'description'] as const;

export function missingRequired(draft: ComplaintDraft): string[] {
  return REQUIRED_KEYS.filter(k => !draft[k] || String(draft[k]).trim() === '');
}

export function warnings(draft: ComplaintDraft): string[] {
  const w: string[] = [];
  if (!draft.batch_number) w.push('Batch number is missing — strongly recommended for investigations.');
  if (draft.description && draft.description.length < 30) w.push('Description looks short — add observable details.');
  return w;
}
