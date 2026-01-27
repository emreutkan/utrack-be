# UTrack Backend

A comprehensive fitness tracking backend API built with Django REST Framework. Track workouts, exercises, supplements, body measurements, and achievements.

## Features

- **User Management**: Registration, authentication, profile management with JWT tokens
- **Workout Tracking**: Create, update, and track workouts with exercises and sets
- **Exercise Database**: Comprehensive exercise library with muscle groups and equipment types
- **Supplement Tracking**: Log supplements with dosage, frequency, and daily tracking
- **Body Measurements**: Track body measurements and calculate body fat percentage
- **Achievements System**: Earn achievements based on workout milestones and personal records
- **Recovery Analytics**: Muscle recovery tracking and CNS load calculations
- **Social Features**: Leaderboards and exercise rankings (PRO feature)
- **Data Export**: Export all user data in JSON format

## Tech Stack

- **Framework**: Django 5.2.9
- **API**: Django REST Framework 3.16.1
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL (production) / SQLite (development)
- **Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Social Auth**: django-allauth (Google, Apple)

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL (for production)
- Virtual environment (recommended)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd utrack_backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**
   ```env
   SECRET_KEY=your-secret-key-here
   LOCALHOST=True
   DEBUG=True
   FRONTEND_URL=http://localhost:3000
   
   # Email Configuration (for production)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   
   # Database (for production)
   POSTGRES_USER=your_db_user
   POSTGRES_PASSWORD=your_db_password
   POSTGRES_DB=utrack_db
   DB_HOST=localhost
   DB_PORT=5432
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Populate initial data (optional)**
   ```bash
   python manage.py populate_exercises
   python manage.py populate_supplements
   python manage.py seed_achievements
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000`

### Docker Setup

1. **Build and run containers**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

## API Endpoints Overview

### Authentication
- `POST /api/user/register/` - Register new user
- `POST /api/user/login/` - Login (returns JWT tokens)
- `POST /api/user/logout/` - Logout
- `POST /api/user/request-password-reset/` - Request password reset email
- `POST /api/user/reset-password/` - Reset password with token

### User Profile
- `GET /api/user/profile/` - Get user profile
- `PUT /api/user/profile/` - Update user profile
- `POST /api/user/update-weight/` - Update weight and track history
- `GET /api/user/weight-history/` - Get weight history

### Workouts
- `GET /api/workout/` - List workouts (paginated)
- `POST /api/workout/create/` - Create new workout
- `GET /api/workout/<id>/` - Get workout details
- `PUT /api/workout/<id>/` - Update workout
- `DELETE /api/workout/<id>/` - Delete workout
- `POST /api/workout/<id>/complete/` - Complete workout
- `GET /api/workout/active/` - Get active workout

### Exercises
- `GET /api/exercise/list/` - List all exercises (paginated, searchable)
- `GET /api/exercise/<id>/` - Get exercise details

### Supplements
- `GET /api/supplements/list/` - List all supplements (paginated, searchable)
- `GET /api/supplements/user/list/` - Get user's supplements
- `POST /api/supplements/user/add/` - Add user supplement
- `GET /api/supplements/user/log/list/` - Get supplement logs
- `POST /api/supplements/user/log/add/` - Log supplement intake
- `GET /api/supplements/user/log/today/` - Get today's logs

### Body Measurements
- `GET /api/measurements/` - Get body measurements (paginated)
- `POST /api/measurements/create/` - Create measurement
- `POST /api/measurements/calculate-body-fat/men/` - Calculate body fat (men)
- `POST /api/measurements/calculate-body-fat/women/` - Calculate body fat (women)

### Achievements
- `GET /api/achievements/list/` - List achievements with progress (paginated)
- `GET /api/achievements/user/` - Get user's earned achievements
- `GET /api/achievements/prs/` - Get personal records summary
- `GET /api/achievements/prs/<exercise_id>/` - Get PR for specific exercise
- `GET /api/achievements/leaderboard/<exercise_id>/` - Get leaderboard (PRO)

### Health Check
- `GET /api/health/` - Health check endpoint (database, cache)

## Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test user
python manage.py test supplements
python manage.py test workout
python manage.py test body_measurements
python manage.py test achievements
```

## Environment Variables

### Required
- `SECRET_KEY` - Django secret key
- `LOCALHOST` - "True" for local development, "False" for production

### Optional (Development)
- `DEBUG` - Enable debug mode (default: True if LOCALHOST=True)
- `FRONTEND_URL` - Frontend URL for email links

### Optional (Production)
- `EMAIL_HOST` - SMTP server host
- `EMAIL_PORT` - SMTP server port
- `EMAIL_USE_TLS` - Use TLS for email
- `EMAIL_HOST_USER` - Email username
- `EMAIL_HOST_PASSWORD` - Email password
- `DEFAULT_FROM_EMAIL` - Default sender email
- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_DB` - PostgreSQL database name
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts

## Deployment

### Production Checklist

1. Set `LOCALHOST=False` in `.env`
2. Set `DEBUG=False`
3. Configure `ALLOWED_HOSTS`
4. Set up PostgreSQL database
5. Configure email settings
6. Set up static files collection
7. Configure SSL/HTTPS
8. Set up proper logging
9. Configure CORS for production
10. Set up monitoring and health checks

### Static Files

```bash
python manage.py collectstatic
```

### Database Migrations

```bash
python manage.py migrate
```

## Project Structure

```
utrack_backend/
├── achievements/          # Achievements and personal records
├── body_measurements/     # Body measurements and body fat calculations
├── core/                  # Core utilities and health checks
├── exercise/              # Exercise database
├── supplements/           # Supplement tracking
├── user/                  # User management and authentication
├── workout/               # Workout tracking and analytics
├── utrack/                # Main project settings
├── media/                 # User-uploaded files
├── staticfiles/           # Collected static files
└── logs/                  # Application logs
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Anonymous users**: 10 requests/minute, 100 requests/hour
- **Authenticated users**: 60 requests/minute, 1000 requests/hour
- **PRO users**: 200 requests/minute
- **Login**: 5 attempts/minute
- **Registration**: 3 attempts/hour
- **Password reset**: 3 requests/hour

## Error Handling

All API errors follow a standardized format:

```json
{
  "error": "ERROR_CODE",
  "message": "User-friendly error message",
  "details": {
    // Additional error details
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.
