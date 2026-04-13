export default function Header({ user, onLogout }) {
  return (
    <div className="app-header">
      <h1>Healthcare Appointment System</h1>
      <div className="user-info">
        <span>{user.name} ({user.role})</span>
        <button className="btn-logout" onClick={onLogout}>Logout</button>
      </div>
    </div>
  )
}
