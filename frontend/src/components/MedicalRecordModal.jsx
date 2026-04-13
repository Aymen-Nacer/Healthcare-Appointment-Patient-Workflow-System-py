import { useState } from 'react'
import api from '../api'

export default function MedicalRecordModal({ appointment, onClose, onSaved }) {
  const [diagnosis, setDiagnosis] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/api/medical-records', {
        appointmentId: appointment.id,
        diagnosis,
        notes,
      })
      await api.patch(`/api/appointments/${appointment.id}/status`, {
        newStatus: 'Completed',
        rowVersion: appointment.rowVersion,
      })
      onSaved(`Medical record saved and appointment #${appointment.id} marked as Completed.`)
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save medical record.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <h3>Medical Record — Appointment #{appointment.id}</h3>
        <p style={{ fontSize: 13, color: '#555', marginBottom: 16 }}>
          Patient: <strong>{appointment.patientName}</strong>
        </p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Diagnosis</label>
            <input
              type="text"
              value={diagnosis}
              onChange={e => setDiagnosis(e.target.value)}
              placeholder="Enter diagnosis"
              required
            />
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Additional notes (optional)"
            />
          </div>
          <div className="modal-actions">
            <button type="button" onClick={onClose} disabled={loading}
              style={{ background: '#eee', color: '#333' }}>
              Cancel
            </button>
            <button type="submit" className="btn-success" disabled={loading}>
              {loading ? 'Saving…' : 'Save & Complete'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
