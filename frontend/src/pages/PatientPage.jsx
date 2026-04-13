import { useState, useEffect, useCallback } from 'react'
import api from '../api'
import Header from '../components/Header'
import StatusBadge from '../components/StatusBadge'

export default function PatientPage({ user, onLogout }) {
  const [appointments, setAppointments] = useState([])
  const [doctors, setDoctors] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [doctorId, setDoctorId] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [booking, setBooking] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [apptRes, docRes] = await Promise.all([
        api.get('/api/appointments'),
        api.get('/api/doctors'),
      ])
      setAppointments(apptRes.data)
      setDoctors(docRes.data)
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load data.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const handleBook = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setBooking(true)
    try {
      await api.post('/api/appointments', {
        doctorId: parseInt(doctorId),
        startTime,
        endTime,
      })
      setSuccess('Appointment booked successfully!')
      setDoctorId('')
      setStartTime('')
      setEndTime('')
      fetchData()
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to book appointment.')
    } finally {
      setBooking(false)
    }
  }

  return (
    <div>
      <Header user={user} onLogout={onLogout} />
      <div className="app-content">
        <div className="section-card">
          <h2>Book an Appointment</h2>
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}
          <form onSubmit={handleBook}>
            <div className="form-group">
              <label>Doctor</label>
              <select value={doctorId} onChange={e => setDoctorId(e.target.value)} required>
                <option value="">-- Select a doctor --</option>
                {doctors.map(d => (
                  <option key={d.doctorProfileId} value={d.doctorProfileId}>
                    Dr. {d.name} — {d.specialty}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Start Time</label>
                <input
                  type="datetime-local"
                  value={startTime}
                  onChange={e => setStartTime(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>End Time</label>
                <input
                  type="datetime-local"
                  value={endTime}
                  onChange={e => setEndTime(e.target.value)}
                  required
                />
              </div>
            </div>
            <button type="submit" className="btn-primary" disabled={booking}>
              {booking ? 'Booking…' : 'Book Appointment'}
            </button>
          </form>
        </div>

        <div className="section-card">
          <h2>My Appointments</h2>
          {loading && <p className="loading">Loading…</p>}
          {!loading && appointments.length === 0 && (
            <div className="empty-state">No appointments yet.</div>
          )}
          {!loading && appointments.length > 0 && (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Doctor</th>
                    <th>Specialty</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {appointments.map(a => (
                    <tr key={a.id}>
                      <td>{a.id}</td>
                      <td>Dr. {a.doctorName}</td>
                      <td>{a.doctorSpecialty}</td>
                      <td>{new Date(a.startTime).toLocaleString()}</td>
                      <td>{new Date(a.endTime).toLocaleString()}</td>
                      <td><StatusBadge status={a.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
