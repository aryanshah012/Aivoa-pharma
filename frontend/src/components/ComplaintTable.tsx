import { Link } from 'react-router-dom';
import type { Complaint } from '../types';
import { StatusBadge, RiskBadge } from './common';
export default function ComplaintTable({ rows }: { rows: Complaint[] }) {
  if (!rows.length) return <p className="muted">No complaints found.</p>;
  return (
    <table>
      <thead><tr>
        <th>Complaint ID</th><th>Product</th><th>Batch</th><th>Customer</th>
        <th>Category</th><th>Risk</th><th>Status</th><th>Received</th><th></th>
      </tr></thead>
      <tbody>
        {rows.map(c => (
          <tr key={c.id}>
            <td><strong>{c.complaint_number}</strong></td>
            <td>{c.product_name}</td><td>{c.batch_number ?? '—'}</td><td>{c.customer_name}</td>
            <td>{c.complaint_type}</td>
            <td><RiskBadge r={c.final_risk_level ?? c.ai_risk_level} /></td>
            <td><StatusBadge s={c.status} /></td>
            <td>{c.received_date ?? '—'}</td>
            <td><Link to={`/complaints/${c.id}`}>Open</Link></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
