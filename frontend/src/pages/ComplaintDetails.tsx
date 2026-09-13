import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { fetchComplaint } from '../store';
import { complaintsApi } from '../api/complaints';
import type { AppDispatch, RootState } from '../store';
import { StatusBadge, RiskBadge, ErrorAlert } from '../components/common';
import { STATUSES, RISK_LEVELS } from '../utils/constants';

export default function ComplaintDetails() {
  const { id } = useParams();
  const dispatch = useDispatch<AppDispatch>();
  const c = useSelector((s: RootState) => s.complaints.selectedComplaint);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (id) dispatch(fetchComplaint(Number(id))); }, [id, dispatch]);

  if (!c) return <p className="muted">Loading…</p>;
  const logs = c.audit_logs ?? [];
  const capa = c.capa_actions ?? [];
  const rows: [string, unknown][] = [
    ['Customer', c.customer_name], ['Location', c.customer_location ?? '—'],
    ['Email', c.customer_email ?? '—'], ['Product', c.product_name],
    ['Type / Strength', `${c.product_type ?? '—'} / ${c.strength_or_grade ?? '—'}`],
    ['Batch / Lot', `${c.batch_number ?? '—'} / ${c.lot_number ?? '—'}`],
    ['Category', c.complaint_type], ['Quantity Affected', c.quantity_affected ?? '—'],
    ['Market', c.market ?? '—'], ['Patient Impact', c.patient_impact ?? '—'],
    ['Adverse Event', c.adverse_event_reported ? 'Yes' : 'No'],
    ['Severity / Priority', `${c.initial_severity ?? '—'} / ${c.priority ?? '—'}`],
  ];

  const patch = (body: Record<string, string>) =>
    complaintsApi.update(c.id, body)
      .then(() => dispatch(fetchComplaint(c.id)))
      .catch(e => setError(e?.response?.data?.detail ?? 'Update failed'));

  return (
    <div>
      <h2 className="page-title">
        {c.complaint_number}{' '}<StatusBadge s={c.status} />{' '}<RiskBadge r={c.final_risk_level ?? c.ai_risk_level} />
      </h2>
      {error && <ErrorAlert msg={error} />}
      <div className="section">
        <h3>Complaint Record</h3>
        {rows.map(([k, v]) => <div className="kv" key={k}><span>{k}</span><span>{String(v)}</span></div>)}
        <p style={{ marginTop: 10 }}>{c.description}</p>
        {c.ai_summary && <p className="muted"><strong>AI Summary:</strong> {c.ai_summary}</p>}
        <div className="filters" style={{ marginTop: 14 }}>
          <select value={c.status} onChange={e => patch({ status: e.target.value })}>
            {STATUSES.map(s => <option key={s}>{s}</option>)}
          </select>
          <select value={c.final_risk_level ?? ''} onChange={e => patch({ final_risk_level: e.target.value })}>
            <option value="">Final risk: unset</option>
            {RISK_LEVELS.map(r => <option key={r}>{r}</option>)}
          </select>
        </div>
      </div>
      {!!capa.length && (
        <div className="section"><h3>CAPA Actions</h3>
          {capa.map(a => (
            <div className="kv" key={a.id}>
              <span>{a.action_type} ({a.source}) — {a.status}</span><span>{a.description}</span>
            </div>
          ))}
        </div>
      )}
      <div className="section">
        <h3>Audit Trail</h3>
        {logs.length ? logs.map(l => (
          <div className="timeline-item" key={l.id}>
            <strong>{l.event_type}</strong>
            {l.old_value && l.new_value ? ` — ${l.old_value} → ${l.new_value}` : ''}
            {l.detail ? <div className="muted">{l.detail}</div> : null}
            <div className="muted">{new Date(l.created_at).toLocaleString()} · {l.actor}</div>
          </div>
        )) : <p className="muted">No audit events yet.</p>}
      </div>
    </div>
  );
}
