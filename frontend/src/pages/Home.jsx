import TopNav from '../components/TopNav';
import { useAuth } from '../context/AuthContext';
import RoomListing from './RoomListing';
import ReceptionBookings from './ReceptionBookings';
import MyTasks from './MyTasks';
import OwnerDashboard from './OwnerDashboard';

export default function Home() {
  const { user } = useAuth();

  // Each role lands on the dashboard that matters to them.
  if (user?.role === 'CUSTOMER') {
    return <RoomListing />;
  }
  if (user?.role === 'RECEPTION') {
    return <ReceptionBookings />;
  }
  if (user?.role === 'HOUSEKEEPING') {
    return <MyTasks />;
  }
  if (user?.role === 'OWNER') {
    return <OwnerDashboard />;
  }

  return (
    <div>
      <TopNav />
    </div>
  );
}




