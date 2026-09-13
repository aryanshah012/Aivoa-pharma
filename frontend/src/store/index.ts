import { configureStore, createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import type { Analysis, Complaint, ComplaintDraft, DashboardStats } from '../types';
import { complaintsApi } from '../api/complaints';

// ---------- complaint slice ----------
export const fetchComplaints = createAsyncThunk('complaints/fetch', (params: Record<string, string> = {}) => complaintsApi.list(params));
export const fetchComplaint = createAsyncThunk('complaints/fetchOne', (id: number) => complaintsApi.get(id));
export const saveComplaint = createAsyncThunk('complaints/save', (draft: ComplaintDraft) =>
  draft.id ? complaintsApi.update(draft.id, draft) : complaintsApi.create(draft));

const complaintSlice = createSlice({
  name: 'complaints',
  initialState: { complaints: [] as Complaint[], selectedComplaint: null as Complaint | null,
    draft: {} as ComplaintDraft, filters: {} as Record<string, string>,
    loading: false, saving: false, error: null as string | null },
  reducers: {
    setDraft: (s, a) => { s.draft = { ...s.draft, ...a.payload }; },
    resetDraft: (s) => { s.draft = {}; s.error = null; },
    setFilters: (s, a) => { s.filters = a.payload; },
    applyAnalysisToDraft: (s, a: { payload: Analysis }) => {
      const d = a.payload.extracted_data as Record<string, unknown>;
      s.draft = { ...s.draft, ...d,
        ai_risk_level: a.payload.risk_assessment?.overall_risk ?? null,
        ai_summary: a.payload.summary?.short_summary ?? null,
        ai_populated_fields: Object.keys(d).filter(k => d[k] !== null && d[k] !== '') };
    },
  },
  extraReducers: (b) => {
    b.addCase(fetchComplaints.pending, s => { s.loading = true; s.error = null; })
     .addCase(fetchComplaints.fulfilled, (s, a) => { s.loading = false; s.complaints = a.payload; })
     .addCase(fetchComplaints.rejected, (s, a) => { s.loading = false; s.error = a.error.message ?? 'Failed to load complaints'; })
     .addCase(fetchComplaint.fulfilled, (s, a) => { s.selectedComplaint = a.payload; })
     .addCase(saveComplaint.pending, s => { s.saving = true; })
     .addCase(saveComplaint.fulfilled, s => { s.saving = false; s.draft = {}; })
     .addCase(saveComplaint.rejected, (s, a) => { s.saving = false; s.error = a.error.message ?? 'Save failed'; });
  },
});

// ---------- AI analysis slice ----------
export const runAnalysis = createAsyncThunk('ai/run', async (input: { text?: string; file?: File }) =>
  input.file ? complaintsApi.analyzeDocument(input.file) : complaintsApi.analyze(input.text!));

const aiSlice = createSlice({
  name: 'ai',
  initialState: { analysis: null as Analysis | null, status: 'idle' as 'idle' | 'running' | 'done' | 'error',
    progress: 0, error: null as string | null },
  reducers: { resetAnalysis: (s) => { s.analysis = null; s.status = 'idle'; s.progress = 0; s.error = null; } },
  extraReducers: (b) => {
    b.addCase(runAnalysis.pending, s => { s.status = 'running'; s.progress = 1; s.error = null; })
     .addCase(runAnalysis.fulfilled, (s, a) => { s.status = 'done'; s.progress = 7; s.analysis = a.payload; })
     .addCase(runAnalysis.rejected, (s, a) => { s.status = 'error'; s.error = a.error.message ?? 'AI analysis failed'; });
  },
});

// ---------- dashboard slice ----------
export const fetchDashboard = createAsyncThunk('dashboard/fetch', async () => ({
  stats: await complaintsApi.stats(), recent: await complaintsApi.recent(),
}));

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState: { stats: null as DashboardStats | null, recent: [] as Complaint[],
    loading: false, error: null as string | null },
  reducers: {},
  extraReducers: (b) => {
    b.addCase(fetchDashboard.pending, s => { s.loading = true; })
     .addCase(fetchDashboard.fulfilled, (s, a) => { s.loading = false; s.stats = a.payload.stats; s.recent = a.payload.recent; })
     .addCase(fetchDashboard.rejected, (s, a) => { s.loading = false; s.error = a.error.message ?? 'Dashboard failed'; });
  },
});

export const { setDraft, resetDraft, setFilters, applyAnalysisToDraft } = complaintSlice.actions;
export const { resetAnalysis } = aiSlice.actions;

export const store = configureStore({
  reducer: { complaints: complaintSlice.reducer, ai: aiSlice.reducer, dashboard: dashboardSlice.reducer },
});
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
