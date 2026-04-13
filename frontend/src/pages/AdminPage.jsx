import { useState, useEffect, useCallback } from 'react'
import api from '../api'
import Header from '../components/Header'
import StatusBadge from '../components/StatusBadge'

const TABS = ['Appointments', 'Audit Logs']

export default function AdminPage({ user, onLogout }) {
  const [tab, setTab] = useState('Appointments')
  const [appointments, setAppointments] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [actionLoading, setActionLoading] = useState(null)

  const fetchAppointments = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/api/appointments')
      setAppointments(res.data)
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load appointments.')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchAuditLogs = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/api/audit-logs')
      setAuditLogs(res.data)
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load audit logs.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'Appointments') fetchAppointments()
    else fetchAuditLogs()
  }, [tab, fetchAppointments, fetchAuditLogs])

  const updateStatus = async (appointment, newStatus) => {
    setError('')
    setSuccess('')
    setActionLoading(`${appointment.id}-${newStatus}`)
    try {
      await api.patch(`/api/appointments/${appointment.id}/status`, {
        newStatus,
        rowVersion: appointment.rowVersion,
      })
      setSuccess(`Appointment #${appointment.id} updated to ${newStatus}.`)
      fetchAppointments()
    } catch (err) {
      setError(err.response?.data?.message || 'Status update failed.')
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div>
      <Header user={user} onLogout={onLogout} />
      <div className="app-content">
        <div className="tab-bar">
          {TABS.map(t => (
            <button key={t} className={`tab-btn${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
              {t}
            </button>
          ))}
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {tab === 'Appointments' && (
          <div className="section-card">
            <h2>All Appointments</h2>
            {loading && <p className="loading">Loading…</p>}
            {!loading && appointments.length === 0 && (
              <div className="empty-state">No appointments found.</div>
            )}
            {!loading && appointments.length > 0 && (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Patient</th>
                      <th>Doctor</th>
                      <th>Start</th>
                      <th>End</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {appointments.map(a => (
                      <tr key={a.id}>
                        <td>{a.id}</td>
                        <td>{a.patientName}</td>
                        <td>Dr. {a.doctorName}</td>
                        <td>{new Date(a.startTime).toLocaleString()}</td>
                        <td>{new Date(a.endTime).toLocaleString()}</td>
                        <td><StatusBadge status={a.status} /></td>
                        <td>
                          <div className="action-group">
                            {a.status === 'Scheduled' && (
                              <button
                                className="btn-success btn-sm"
                                disabled={actionLoading === `${a.id}-Confirmed`}
                                onClick={() => updateStatus(a, 'Confirmed')}
                              >
                                {actionLoading === `${a.id}-Confirmed` ? '…' : 'Confirm'}
                              </button>
                            )}
                            {(a.status === 'Scheduled' || a.status === 'Confirmed') && (
                              <button
                                className="btn-danger btn-sm"
                                disabled={actionLoading === `${a.id}-Cancelled`}
                                onClick={() => updateStatus(a, 'Cancelled')}
                              >
                                {actionLoading === `${a.id}-Cancelled` ? '…' : 'Cancel'}
                              </button>
                            )}
                            {(a.status === 'InProgress' || a.status === 'Completed' || a.status === 'Cancelled') && (
                              <span style={{ color: '#999', fontSize: 12 }}>—</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {tab === 'Audit Logs' && (
          <div className="section-card">
            <h2>Audit Logs</h2>
            {loading && <p className="loading">Loading…</p>}
            {!loading && auditLogs.length === 0 && (
              <div className="empty-state">No audit logs found.</div>
            )}
            {!loading && auditLogs.length > 0 && (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Action</th>
                      <th>Entity ID</th>
                      <th>User ID</th>
                      <th>Timestamp</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map(log => (
                      <tr key={log.id}>
                        <td>{log.id}</td>
                        <td>{log.action}</td>
                        <td>{log.entityId}</td>
                        <td>{log.performedByUserId}</td>
                        <td>{new Date(log.timestamp).toLocaleString()}</td>
                        <td style={{ maxWidth: 240, fontSize: 12, color: '#555' }}>
                          {log.metadata || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
