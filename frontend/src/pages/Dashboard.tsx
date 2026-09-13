import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { fetchDashboard } from '../store';
import type { AppDispatch, RootState } from '../store';
import { StatCard } from '../components/common';
import ComplaintTable from '../components/ComplaintTable';
export default function Dashboard() {
  const dispatch = useDispatch<AppDispatch>();
  const { stats, recent, loading } = useSelector((s: RootState) => s.dashboard);
  useEffect(() => { dispatch(fetchDashboard()); }, [dispatch]);
  if (loading || !stats) return <p className="muted">Loading dashboard…</p>;
  return (
    <div>
      <div className="header">
        <h1>QMS Dashboard</h1>
        <Link to="/log" className="btn primary" style={{ textDecoration: 'none' }}>+ Log Customer Complaint</Link>
      </div>
      <div className="cards">
        <StatCard label="Total Complaints" value={stats.total_complaints} />
        <StatCard label="Open" value={stats.open_complaints} />
        <StatCard label="Under Investigation" value={stats.under_investigation} />
        <StatCard label="Critical / High Risk" value={stats.critical_high_risk} />
        <StatCard label="Closed" value={stats.closed_complaints} />
        <StatCard label="Avg Resolution (days)" value={stats.avg_resolution_days ?? '—'} />
      </div>
      <h2 className="page-title">Recent Complaints</h2>
      <ComplaintTable rows={recent} />
    </div>
  );
}
