import { useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { runAnalysis, applyAnalysisToDraft } from '../store';
import type { AppDispatch, RootState } from '../store';
import { progressMessages } from '../api/complaints';
import { ErrorAlert, AI_DISCLAIMER } from './common';
import type { Analysis } from '../types';

function RiskCard({ a }: { a: Analysis }) {
  const r = a.risk_assessment;
  if (!r) return null;
  const rows: [string, string][] = [['Patient Safety', r.patient_safety], ['Product Quality', r.product_quality],
    ['Regulatory Impact', r.regulatory_impact], ['Business Impact', r.business_impact]];
  return (
    <div className="section">
      <h3>AI Copilot Risk Assessment</h3>
      <div className="kv"><span>Overall Risk</span><strong>{r.overall_risk}</strong></div>
      {rows.map(([k, v]) => (
        <div className="kv" key={k}><span>{k}</span><span className={`badge risk-${v}`}>{v}</span></div>
      ))}
      <div style={{ margin: '10px 0' }}>
        <div className="muted">AI Confidence: {Math.round(r.confidence * 100)}%</div>
        <div className="bar"><div style={{ width: `${r.confidence * 100}%` }} /></div>
      </div>
      {r.reasoning.map((x, i) => <p className="muted" key={i} style={{ margin: '4px 0' }}>• {x}</p>)}
      <p className="muted" style={{ margin: '6px 0 0' }}>Recommended: {r.recommended_actions.join('; ')}</p>
      <p className="muted">{AI_DISCLAIMER}</p>
    </div>
  );
}

export default function IntakePanel() {
  const dispatch = useDispatch<AppDispatch>();
  const { analysis, status, progress, error } = useSelector((s: RootState) => s.ai);
  const [tab, setTab] = useState<'upload' | 'paste' | 'email'>('paste');
  const [text, setText] = useState('');
  const [drag, setDrag] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const running = status === 'running';

  const analyze = (payload: { text?: string; file?: File }) => {
    dispatch(runAnalysis(payload)).unwrap().then(a => dispatch(applyAnalysisToDraft(a))).catch(() => {});
  };
  const onFile = (f?: File | null) => { if (f) analyze({ file: f }); };

  return (
    <div>
      <div className="panel-tabs">
        {([['paste', 'Paste Text'], ['email', 'Paste Email'], ['upload', 'Upload Document']] as const).map(([k, l]) => (
          <button key={k} className={tab === k ? 'active' : ''} onClick={() => setTab(k)}>{l}</button>
        ))}
      </div>

      {tab === 'upload' ? (
        <>
          <div className={`dropzone ${drag ? 'drag' : ''}`}
            onDragOver={e => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={e => { e.preventDefault(); setDrag(false); onFile(e.dataTransfer.files?.[0]); }}>
            Drag & drop a complaint PDF or TXT here, or{' '}
            <a href="#" onClick={e => { e.preventDefault(); fileRef.current?.click(); }}>browse</a>
          </div>
          <input ref={fileRef} type="file" accept=".pdf,.txt" hidden
            onChange={e => { onFile(e.target.files?.[0]); e.target.value = ''; }} />
        </>
      ) : (
        <textarea rows={10} placeholder={tab === 'email' ? 'Paste complaint email…' : 'Paste complaint text…'}
          value={text} onChange={e => setText(e.target.value)} style={{ marginBottom: 10 }} />
      )}

      <button className="btn primary" style={{ width: '100%' }} disabled={running || (tab !== 'upload' && text.trim().length < 10)}
        onClick={() => analyze({ text })}>
        {running ? 'Analyzing…' : 'Analyze with AI'}
      </button>

      {error && <div style={{ marginTop: 10 }}><ErrorAlert msg={error} /></div>}

      {running && (
        <div className="section" style={{ marginTop: 12 }}>
          {progressMessages.map((m, i) => (
            <div key={m} className={`progress-step ${i < progress ? 'done' : i === progress ? 'active' : ''}`}>
              {i < progress ? '✓' : i === progress ? '◌' : '○'} {m}
            </div>
          ))}
        </div>
      )}

      {analysis && status === 'done' && (
        <div style={{ marginTop: 12 }}>
          <div className="disclaimer">Analysis completed — please verify AI-generated information before saving. The form has been auto-populated.</div>
          {analysis.completeness && (
            <div className="section">
              <h3>Completeness — {analysis.completeness.score}% ({analysis.completeness.status})</h3>
              <div className="bar"><div style={{ width: `${analysis.completeness.score}%` }} /></div>
              {analysis.completeness.missing_fields.length > 0 && (
                <p className="muted">Missing: {analysis.completeness.missing_fields.join(', ')}</p>)}
              {analysis.completeness.recommended_questions.map((q, i) => <p className="muted" key={i}>❓ {q}</p>)}
            </div>
          )}
          <RiskCard a={analysis} />
          {!!analysis.duplicate_matches.length && (
            <div className="section">
              <h3>Potential Duplicates</h3>
              {analysis.duplicate_matches.map(d => (
                <div className="kv" key={d.complaint_id}>
                  <span><a href={`/complaints/${d.complaint_id}`}>{d.complaint_number}</a> — {d.reason}</span>
                  <strong>{Math.round(d.similarity_score * 100)}%</strong>
                </div>
              ))}
            </div>
          )}
          {analysis.summary && (
            <div className="section">
              <h3>AI Summary</h3>
              <p style={{ margin: '4px 0' }}>{analysis.summary.short_summary}</p>
              <p className="muted">{analysis.summary.management_summary}</p>
            </div>
          )}
          {analysis.root_cause_analysis && (
            <div className="section">
              <h3>AI Investigation Suggestions</h3>
              {analysis.root_cause_analysis.possible_causes.map((c, i) => (
                <p key={i} style={{ margin: '4px 0' }}><strong>{c.cause}</strong>{' '}
                  <span className="muted">({c.confidence})</span> — {c.rationale}</p>
              ))}
              <p className="muted">Evidence: {analysis.root_cause_analysis.recommended_evidence.join(', ')}</p>
              <p className="muted">Potential investigation areas — not confirmed root causes. {AI_DISCLAIMER}</p>
            </div>
          )}
          {analysis.capa_recommendations && (
            <div className="section">
              <h3>AI CAPA Suggestions</h3>
              <p className="muted"><strong>Corrective:</strong> {analysis.capa_recommendations.corrective_actions.join('; ')}</p>
              <p className="muted"><strong>Preventive:</strong> {analysis.capa_recommendations.preventive_actions.join('; ')}</p>
              <p className="muted">{AI_DISCLAIMER} Final CAPA must be approved by authorized Quality personnel.</p>
            </div>
          )}
          {!!analysis.errors.length && <ErrorAlert msg={analysis.errors.join(' | ')} />}
        </div>
      )}
    </div>
  );
}
