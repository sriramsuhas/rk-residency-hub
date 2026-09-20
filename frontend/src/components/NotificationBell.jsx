import { useEffect, useRef, useState } from 'react';
import { notificationsApi } from '../api/notifications';
import './NotificationBell.css';

function timeAgo(isoString) {
  const seconds = Math.floor((Date.now() - new Date(isoString)) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const containerRef = useRef(null);

  function load() {
    notificationsApi.list({ page_size: 10 }).then((res) => {
      setItems(res.data.data.items);
      setUnreadCount(res.data.data.unread_count);
    });
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  async function handleMarkRead(id) {
    await notificationsApi.markRead(id);
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }

  async function handleMarkAllRead() {
    await notificationsApi.markAllRead();
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
  }

  return (
    <div className="notif-bell" ref={containerRef}>
      <button className="notif-bell__trigger" onClick={() => setOpen((o) => !o)} aria-label="Notifications">
        🔔
        {unreadCount > 0 && <span className="notif-bell__badge">{unreadCount > 9 ? '9+' : unreadCount}</span>}
      </button>

      {open && (
        <div className="notif-bell__panel">
          <div className="notif-bell__header">
            <span>Notifications</span>
            {unreadCount > 0 && (
              <button className="notif-bell__mark-all" onClick={handleMarkAllRead}>
                Mark all read
              </button>
            )}
          </div>

          {items.length === 0 && <p className="notif-bell__empty">No notifications yet.</p>}

          <div className="notif-bell__list">
            {items.map((n) => (
              <button
                key={n.id}
                className={`notif-bell__item ${n.is_read ? '' : 'notif-bell__item--unread'}`}
                onClick={() => !n.is_read && handleMarkRead(n.id)}
              >
                <span className="notif-bell__item-title">{n.title}</span>
                <span className="notif-bell__item-message">{n.message}</span>
                <span className="notif-bell__item-time">{timeAgo(n.created_at)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
