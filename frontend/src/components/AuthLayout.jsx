import './auth-layout.css';

export default function AuthLayout({ eyebrow, title, subtitle, children }) {
  return (
    <div className="auth-shell">
      <aside className="auth-lobby">
        <div className="auth-lobby__mark">RK</div>
        <h1 className="auth-lobby__name">RK Residency Hub</h1>
        <p className="auth-lobby__tagline">Property management, kept simple.</p>

        <div className="key-tag" aria-hidden="true">
          <span className="key-tag__ring" />
          <span className="key-tag__number">204</span>
          <span className="key-tag__label">Front Desk Access</span>
        </div>
      </aside>

      <main className="auth-desk">
        <div className="auth-desk__inner">
          {eyebrow && <p className="auth-eyebrow">{eyebrow}</p>}
          <h2 className="auth-title">{title}</h2>
          {subtitle && <p className="auth-subtitle">{subtitle}</p>}
          {children}
        </div>
      </main>
    </div>
  );
}
