import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchComplaints, setFilters } from '../store';
import type { AppDispatch, RootState } from '../store';
import ComplaintTable from '../components/ComplaintTable';
import { RISK_LEVELS, STATUSES, CATEGORIES } from '../utils/constants';

export default function ComplaintsList() {
  const dispatch = useDispatch<AppDispatch>();
  const { complaints, filters, loading } = useSelector((s: RootState) => s.complaints);
  useEffect(() => { dispatch(fetchComplaints(filters)); }, [dispatch]); // eslint-disable-line react-hooks/exhaustive-deps
  const set = (k: string, v: string) => {
    const f = { ...filters, [k]: v };
    dispatch(setFilters(f));
    dispatch(fetchComplaints(f));
  };
  return (
    <div>
      <h2 className="page-title">Complaints</h2>
      <div className="filters">
        <input placeholder="Search ID, customer, product, batch" defaultValue={filters.search ?? ''}
          onKeyDown={e => { if (e.key === 'Enter') set('search', (e.target as HTMLInputElement).value); }} />
        <select value={filters.risk ?? ''} onChange={e => set('risk', e.target.value)}>
          <option value="">Risk: all</option>{RISK_LEVELS.map(r => <option key={r}>{r}</option>)}
        </select>
        <select value={filters.status ?? ''} onChange={e => set('status', e.target.value)}>
          <option value="">Status: all</option>{STATUSES.map(s => <option key={s}>{s}</option>)}
        </select>
        <select value={filters.category ?? ''} onChange={e => set('category', e.target.value)}>
          <option value="">Category: all</option>{CATEGORIES.map(c => <option key={c}>{c}</option>)}
        </select>
      </div>
      {loading ? <p className="muted">Loading…</p> : <ComplaintTable rows={complaints} />}
    </div>
  );
}
