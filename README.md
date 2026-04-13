# Healthcare Appointment System — Full Stack (Django + React)

A full-stack healthcare workflow system demonstrating the complete appointment lifecycle:

**Patient → Books Appointment → Admin Confirms → Doctor Processes → Diagnosis → Completed**

---

## Tech Stack

| Layer       | Technology                                  |
|-------------|---------------------------------------------|
| Backend     | Django 5.1, Django REST Framework, PyJWT     |
| Database    | PostgreSQL 16 (Docker)                       |
| Frontend    | React 18 + Vite, Axios, plain CSS            |
| Container   | Docker + Docker Compose                      |

---

## Quick Start (Docker)

```bash
docker compose up --build
```

| Service  | URL                          |
|----------|-------------------------------|
| Frontend | http://localhost:3000         |
| Backend  | http://localhost:8080         |
| PostgreSQL | localhost:5432             |

> The API auto-migrates and seeds the database on startup.

---

## Demo Credentials

| Role    | Email                          | Password   |
|---------|-------------------------------|------------|
| Admin   | admin@healthcare.com           | Admin@123  |
| Doctor  | alice.smith@healthcare.com     | Doctor@123 |
| Doctor  | bob.johnson@healthcare.com     | Doctor@123 |
| Patient | carol.white@email.com          | Patient@123|
| Patient | david.brown@email.com          | Patient@123|

---

## Workflow

1. **Patient** logs in → Books an appointment (select doctor + time)
2. **Admin** logs in → Confirms or Cancels appointment
3. **Doctor** logs in → Starts appointment (Confirmed → InProgress)
4. **Doctor** → Adds medical record (diagnosis + notes) → Marks Completed
5. **Admin** → Views audit logs of all actions

---

## Appointment Status Transitions

```
Scheduled ──(Admin)──► Confirmed ──(Doctor)──► InProgress ──(Doctor)──► Completed
    │                      │
    └──────(Admin)──────────┴──────────────────────────────────────────► Cancelled
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt

# Set environment variables or use defaults
python manage.py migrate
python manage.py seed_db
python manage.py runserver 0.0.0.0:8080
```

Runs on: http://localhost:8080

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on: http://localhost:5173

Set `VITE_API_URL=http://localhost:8080` in `frontend/.env` for local dev.

---

## API Endpoints

| Method | Endpoint                          | Role          |
|--------|-----------------------------------|---------------|
| POST   | /api/auth/login                   | Public        |
| POST   | /api/auth/register                | Public        |
| GET    | /api/doctors                      | Authenticated |
| POST   | /api/appointments                 | Patient       |
| GET    | /api/appointments                 | All roles     |
| PATCH  | /api/appointments/{id}/status     | Admin/Doctor  |
| POST   | /api/medical-records              | Doctor        |
| GET    | /api/medical-records/{apptId}     | All roles     |
| GET    | /api/audit-logs                   | Admin         |

---

## Project Structure

```
├── backend/
│   ├── config/              # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── healthcare/          # Main Django app
│   │   ├── models.py        # User, DoctorProfile, PatientProfile, Appointment, MedicalRecord, AuditLog
│   │   ├── views.py         # API views (function-based)
│   │   ├── serializers.py   # Request/Response serializers
│   │   ├── services/        # Business logic layer
│   │   ├── authentication.py # Custom JWT authentication
│   │   ├── permissions.py   # Role-based permissions
│   │   ├── urls.py          # URL routing
│   │   └── management/      # seed_db management command
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # AdminPage, DoctorPage, PatientPage, LoginPage
│   │   ├── components/      # Header, StatusBadge, MedicalRecordModal
│   │   ├── api.js           # Axios instance
│   │   └── App.jsx          # Main app with role-based routing
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```
