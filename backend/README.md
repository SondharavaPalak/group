# EduSuite LMS

Backend: Django + DRF (SQLite)
Frontend: CRA React (JavaScript only)

Quickstart

- Backend
  - Install Python deps: pip3 install --user --break-system-packages "Django==4.2.*" djangorestframework django-cors-headers PyPDF2
  - cd backend
  - python3 manage.py migrate
  - python3 manage.py createsuperuser
  - python3 manage.py runserver 0.0.0.0:8000

- Frontend
  - cd frontend
  - REACT_APP_API_BASE=http://localhost:8000/api npm start

Notes

- Media uploads served at /media/ in DEBUG
- Token auth: POST /api/auth/token/ {username,password}
- AI question generator: POST /api/ai/generate-questions/ with {text} or multipart with a 'file' PDF