# SkillBridge AI - Backend

Backend API for SkillBridge AI - A centralized Academia-Industry Collaboration Portal.

## Tech Stack

- **Python** 3.11+
- **Flask** 3.0+
- **Flask-SQLAlchemy** 3.1+
- **Flask-Migrate** 4.0+
- **Flask-JWT-Extended** 4.6+
- **Flask-CORS** 4.0+
- **Marshmallow** 3.20+
- **SQLite** (development)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration management
│   ├── extensions.py        # Flask extensions
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── enums.py         # UserRole enum
│   │   └── user.py          # User model
│   ├── routes/              # API routes
│   │   ├── __init__.py
│   │   ├── auth_routes.py   # Authentication endpoints
│   │   └── test_routes.py   # RBAC test endpoints
│   ├── schemas/             # Validation schemas
│   │   └── auth_schema.py
│   ├── services/            # Business logic
│   │   └── auth_service.py
│   └── utils/               # Utilities
│       └── decorators.py    # RBAC decorators
├── migrations/              # Database migrations
├── config.py                # Root config
├── extensions.py            # Root extensions
├── run.py                   # Entry point
├── requirements.txt
└── .env.example
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get JWT token |
| GET | `/api/auth/me` | Get current user info (protected) |

### RBAC Test Endpoints
| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/api/test/public` | Public |
| GET | `/api/test/protected` | Any authenticated user |
| GET | `/api/test/student-only` | STUDENT only |
| GET | `/api/test/industry-only` | INDUSTRY only |
| GET | `/api/test/academician-only` | ACADEMICIAN only |
| GET | `/api/test/institution-only` | INSTITUTION only |
| GET | `/api/test/student-or-institution` | STUDENT or INSTITUTION |
| GET | `/api/test/industry-or-academician` | INDUSTRY or ACADEMICIAN |

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## User Roles

- **STUDENT** - Students seeking placements
- **INDUSTRY** - Industry professionals/companies
- **ACADEMICIAN** - Faculty/academic staff
- **INSTITUTION** - Educational institutions

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv .venv
```

3. Activate virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Copy environment file:
```bash
copy .env.example .env
```

6. Initialize database:
```bash
flask db upgrade
```

### Running the Server

```bash
# Development
flask run --port 5000 --debug

# Or using run.py
python run.py
```

The server will start at `http://localhost:5000`

## Testing the API

### Register a new user
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "STUDENT"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123"
  }'
```

### Get current user (protected)
```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer <your_access_token>"
```

### Test RBAC endpoints
```bash
# Public endpoint
curl http://localhost:5000/api/test/public

# Protected endpoint (requires token)
curl -H "Authorization: Bearer <your_access_token>" \
  http://localhost:5000/api/test/protected

# Role-specific endpoint
curl -H "Authorization: Bearer <your_student_token>" \
  http://localhost:5000/api/test/student-only
```

## Database Migrations

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

## Configuration

Environment variables (from `.env`):
- `FLASK_ENV` - Environment (development/testing/production)
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key
- `JWT_ACCESS_TOKEN_EXPIRES_HOURS` - Token expiry in hours
- `DATABASE_URL` - Database connection string
- `CORS_ORIGINS` - Comma-separated allowed origins
- `PORT` - Server port

## Security

- Passwords are hashed using Werkzeug's `generate_password_hash`
- JWT tokens for stateless authentication
- Role-based access control (RBAC) on protected endpoints
- CORS configured for frontend integration

## Testing

Run tests:
```bash
pytest
```