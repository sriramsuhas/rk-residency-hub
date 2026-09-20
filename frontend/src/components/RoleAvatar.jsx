const ROLE_ICON = {
  CUSTOMER: '🧑',
  RECEPTION: '💁',
  HOUSEKEEPING: '🧹',
  OWNER: '👑',
};

const ROLE_COLOR = {
  CUSTOMER: '#4B5D45',
  RECEPTION: '#6B7FB8',
  HOUSEKEEPING: '#A97D50',
  OWNER: '#34432F',
};

/**
 * Fixed, role-specific avatar. Not user-uploadable — every account of a
 * given role shows the same icon, colored by role for quick recognition
 * across the app (nav, tables, cards).
 */
export default function RoleAvatar({ role, className = '' }) {
  const icon = ROLE_ICON[role] || '👤';
  const color = ROLE_COLOR[role] || '#77816F';

  return (
    <span
      className={`role-avatar ${className}`}
      style={{ backgroundColor: color }}
      title={role}
      aria-label={`${role} avatar`}
    >
      {icon}
    </span>
  );
}
