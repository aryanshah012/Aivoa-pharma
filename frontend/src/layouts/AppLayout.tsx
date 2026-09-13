import { NavLink } from 'react-router-dom';
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="layout">
      <aside className="sidebar">
        <span className="brand">⚕ AIVOA PharmaQMS AI</span>
        <NavLink to="/" end>Dashboard</NavLink>
        <NavLink to="/complaints">Complaints</NavLink>
        <NavLink to="/log">Log Customer Complaint</NavLink>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
