import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { setDraft, resetDraft, saveComplaint } from '../store';
import type { RootState, AppDispatch } from '../store';
import IntakePanel from '../components/IntakePanel';
import { ErrorAlert, AI_DISCLAIMER } from '../components/common';
import { SOURCES, PRODUCT_TYPES, CATEGORIES, SEVERITIES, PRIORITIES } from '../utils/constants';
import { missingRequired, warnings } from '../utils/validation';
import type { ComplaintDraft } from '../types';

type FieldProps = {
  label: string; name: keyof ComplaintDraft; draft: ComplaintDraft;
  onChange: (k: keyof ComplaintDraft, v: unknown) => void;
  type?: string; options?: string[]; textarea?: boolean; full?: boolean;
};

function Field({ label, name, draft, onChange, type = 'text', options, textarea, full }: FieldProps) {
  const ai = draft.ai_populated_fields?.includes(name);
  const value = (draft[name] as string | number | undefined) ?? '';
  return (
    <div className={full ? 'full' : ''}>
      <label>{label}{ai && <span className="ai-tag">AI extracted</span>}</label>
      {options ? (
        <select value={String(value)} onChange={e => onChange(name, e.target.value || null)}>
          <option value="">—</option>
          {options.map(o => <option key={o}>{o}</option>)}
        </select>
      ) : textarea ? (
        <textarea rows={4} value={String(value)} onChange={e => onChange(name, e.target.value)} />
      ) : (
        <input type={type} value={value}
          onChange={e => onChange(name, type === 'number'
            ? (e.target.value === '' ? null : Number(e.target.value))
            : e.target.value)} />
      )}
    </div>
  );
}

export default function LogComplaint() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { draft, saving, error } = useSelector((s: RootState) => s.complaints);
  const set = (k: keyof ComplaintDraft, v: unknown) => dispatch(setDraft({ [k]: v }));

  const missing = missingRequired(draft);
  const warns = warnings(draft);
  const canSave = !missing.length && !saving;

  const save = () => {
    if (!canSave) return;
    dispatch(saveComplaint(draft)).unwrap()
      .then(() => navigate('/complaints'))
      .catch(() => {});
  };

  return (
    <div>
      <h2 className="page-title">Log Customer Complaint</h2>
      {error && <ErrorAlert msg={error} />}
      {!!missing.length && (
        <div className="disclaimer">Required before saving: {missing.map(m => m.replace(/_/g, ' ')).join(', ')}</div>
      )}
      {warns.map(w => <div className="disclaimer" key={w}>{w}</div>)}
      <div className="grid2">
        <div>
          <div className="section">
            <h3>1. Origin &amp; Customer Details</h3>
            <div className="form-grid">
              <Field label="Complaint Source" name="complaint_source" draft={draft} onChange={set} options={SOURCES} />
              <Field label="Customer Name *" name="customer_name" draft={draft} onChange={set} />
              <Field label="Customer Email" name="customer_email" draft={draft} onChange={set} />
              <Field label="Customer Phone" name="customer_phone" draft={draft} onChange={set} />
              <Field label="Customer Location" name="customer_location" draft={draft} onChange={set} />
              <Field label="Country" name="country" draft={draft} onChange={set} />
            </div>
          </div>
          <div className="section">
            <h3>2. Product &amp; Batch Identification</h3>
            <div className="form-grid">
              <Field label="Product Name *" name="product_name" draft={draft} onChange={set} />
              <Field label="Product Type" name="product_type" draft={draft} onChange={set} options={PRODUCT_TYPES} />
              <Field label="Strength / Grade" name="strength_or_grade" draft={draft} onChange={set} />
              <Field label="Batch Number" name="batch_number" draft={draft} onChange={set} />
              <Field label="Lot Number" name="lot_number" draft={draft} onChange={set} />
              <Field label="Manufacturing Date" name="manufacturing_date" type="date" draft={draft} onChange={set} />
              <Field label="Expiry Date" name="expiry_date" type="date" draft={draft} onChange={set} />
              <Field label="Quantity Affected" name="quantity_affected" type="number" draft={draft} onChange={set} />
            </div>
          </div>
          <div className="section">
            <h3>3. Complaint Details</h3>
            <div className="form-grid">
              <Field label="Complaint Category *" name="complaint_type" draft={draft} onChange={set} options={CATEGORIES} />
              <Field label="Complaint Date" name="complaint_date" type="date" draft={draft} onChange={set} />
              <Field label="Received Date" name="received_date" type="date" draft={draft} onChange={set} />
              <Field label="Market" name="market" draft={draft} onChange={set} />
              <Field label="Detailed Description *" name="description" draft={draft} onChange={set} textarea full />
            </div>
          </div>
          <div className="section">
            <h3>4. Initial Assessment &amp; Priority</h3>
            <div className="form-grid">
              <Field label="Initial Severity" name="initial_severity" draft={draft} onChange={set} options={SEVERITIES} />
              <Field label="Priority" name="priority" draft={draft} onChange={set} options={PRIORITIES} />
              <Field label="Patient Impact" name="patient_impact" draft={draft} onChange={set} />
              <div>
                <label>Adverse Event Reported</label>
                <select value={String(draft.adverse_event_reported ?? false)}
                  onChange={e => set('adverse_event_reported', e.target.value === 'true')}>
                  <option value="false">No</option><option value="true">Yes</option>
                </select>
              </div>
            </div>
            {draft.ai_risk_level && (
              <p className="muted" style={{ marginTop: 10 }}>AI suggested risk:{' '}
                <strong>{draft.ai_risk_level}</strong> — {AI_DISCLAIMER}</p>
            )}
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn" onClick={() => dispatch(resetDraft())}>Reset Form</button>
            <button className="btn" disabled title="Coming soon">Save Draft</button>
            <button className="btn primary" disabled={!canSave} onClick={save}>
              {saving ? 'Saving…' : 'Save Complaint'}
            </button>
          </div>
        </div>
        <div className="section">
          <h3>AI Complaint Intake Assistant</h3>
          <IntakePanel />
        </div>
      </div>
    </div>
  );
}
