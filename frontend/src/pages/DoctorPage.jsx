import { useState, useEffect, useCallback } from 'react'
import api from '../api'
import Header from '../components/Header'
import StatusBadge from '../components/StatusBadge'
import MedicalRecordModal from '../components/MedicalRecordModal'

export default function DoctorPage({ user, onLogout }) {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [actionLoading, setActionLoading] = useState(null)
  const [recordModal, setRecordModal] = useState(null)

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

  useEffect(() => { fetchAppointments() }, [fetchAppointments])

  const updateStatus = async (appointment, newStatus) => {
    setError('')
    setSuccess('')
    setActionLoading(`${appointment.id}-${newStatus}`)
    try {
      await api.patch(`/api/appointments/${appointment.id}/status`, {
        newStatus,
        rowVersion: appointment.rowVersion,
      })
      setSuccess(`Appointment #${appointment.id} moved to ${newStatus}.`)
      fetchAppointments()
    } catch (err) {
      setError(err.response?.data?.message || 'Status update failed.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleRecordSaved = (msg) => {
    setRecordModal(null)
    setSuccess(msg)
    fetchAppointments()
  }

  return (
    <div>
      <Header user={user} onLogout={onLogout} />
      <div className="app-content">
        <div className="section-card">
          <h2>My Appointments</h2>
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          {loading && <p className="loading">Loading…</p>}
          {!loading && appointments.length === 0 && (
            <div className="empty-state">No appointments assigned to you.</div>
          )}
          {!loading && appointments.length > 0 && (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Patient</th>
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
                      <td>{new Date(a.startTime).toLocaleString()}</td>
                      <td>{new Date(a.endTime).toLocaleString()}</td>
                      <td><StatusBadge status={a.status} /></td>
                      <td>
                        <div className="action-group">
                          {a.status === 'Confirmed' && (
                            <button
                              className="btn-warning btn-sm"
                              disabled={actionLoading === `${a.id}-InProgress`}
                              onClick={() => updateStatus(a, 'InProgress')}
                            >
                              {actionLoading === `${a.id}-InProgress` ? '…' : 'Start'}
                            </button>
                          )}
                          {a.status === 'InProgress' && (
                            <>
                              <button
                                className="btn-primary btn-sm"
                                onClick={() => setRecordModal(a)}
                              >
                                Add Record &amp; Complete
                              </button>
                            </>
                          )}
                          {(a.status === 'Scheduled' || a.status === 'Completed' || a.status === 'Cancelled') && (
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
      </div>

      {recordModal && (
        <MedicalRecordModal
          appointment={recordModal}
          onClose={() => setRecordModal(null)}
          onSaved={handleRecordSaved}
        />
      )}
    </div>
  )
}
