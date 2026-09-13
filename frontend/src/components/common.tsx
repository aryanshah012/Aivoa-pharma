import type { Risk, Status } from '../types';
export const StatusBadge = ({ s }: { s: Status }) =>
  <span className={`badge status-${s.replace(/\s/g, '')}`}>{s}</span>;
export const RiskBadge = ({ r }: { r?: Risk | null }) =>
  r ? <span className={`badge risk-${r}`}>{r}</span> : <span className="muted">—</span>;
export const StatCard = ({ label, value }: { label: string; value: string | number }) => (
  <div className="card"><div className="stat-num">{value}</div><div className="stat-label">{label}</div></div>
);
export const ErrorAlert = ({ msg }: { msg: string }) => <div className="alert">{msg}</div>;
export const AI_DISCLAIMER = 'AI-generated suggestion — Quality review required.';
