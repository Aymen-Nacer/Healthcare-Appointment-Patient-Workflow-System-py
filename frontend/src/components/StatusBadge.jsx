export default function StatusBadge({ status }) {
  const classMap = {
    Scheduled: 'badge-scheduled',
    Confirmed: 'badge-confirmed',
    InProgress: 'badge-inprogress',
    Completed: 'badge-completed',
    Cancelled: 'badge-cancelled',
  }
  return (
    <span className={`badge ${classMap[status] || ''}`}>{status}</span>
  )
}
