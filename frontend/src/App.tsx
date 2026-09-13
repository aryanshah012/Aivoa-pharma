import { Routes, Route } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import Dashboard from './pages/Dashboard';
import LogComplaint from './pages/LogComplaint';
import ComplaintsList from './pages/ComplaintsList';
import ComplaintDetails from './pages/ComplaintDetails';
export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/log" element={<LogComplaint />} />
        <Route path="/complaints" element={<ComplaintsList />} />
        <Route path="/complaints/:id" element={<ComplaintDetails />} />
      </Routes>
    </AppLayout>
  );
}
