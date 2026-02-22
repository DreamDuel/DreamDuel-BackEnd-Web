# DreamDuel Backend - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### Option 1: Docker (Recommended)

1. **Prerequisites**: Docker and Docker Compose installed

2. **Clone and setup**:
```bash
git clone <repo-url>
cd "BackEnd DREAMDUEL Web"
cp .env.example .env
```

3. **Edit .env file** with your API keys (Stripe, Cloudinary, Resend)

4. **Start everything**:
```bash
docker-compose up -d
```

5. **Run migrations**:
```bash
docker-compose exec api alembic upgrade head
```

6. **Access the API**: http://localhost:8000/docs

### Option 2: Local Development

1. **Prerequisites**: Python 3.11+, PostgreSQL 15+, Redis 7+

2. **Setup**:
```bash
# Clone repo
git clone <repo-url>
cd "BackEnd DREAMDUEL Web"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database and API credentials
```

3. **Database setup**:
```bash
# Make sure PostgreSQL is running
# Create database: createdb dreamduel_dev

# Run migrations
alembic upgrade head
```

4. **Start the server**:
```bash
uvicorn app.main:app --reload --port 8000
```

5. **Access the API**: http://localhost:8000/docs

## 📋 Essential Environment Variables

Minimum required in `.env`:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/dreamduel_dev
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-random-secret-at-least-32-chars
SECRET_KEY=another-random-secret-key

# For payments (get from stripe.com)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# For uploads (get from cloudinary.com)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# For emails (get from resend.com)
RESEND_API_KEY=re_...
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app

# Specific test
pytest tests/test_auth.py -v
```

## 🔧 Common Tasks

```bash
# Create migration
alembic revision --autogenerate -m "your message"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Start Celery worker
celery -A app.core.celery worker --loglevel=info

# Format code
make format

# Run linting
make lint
```

## 📚 API Endpoints

Once running, visit http://localhost:8000/docs for interactive API documentation.

Key endpoints:
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `GET /api/stories` - Browse stories
- `POST /api/stories` - Create story
- `POST /api/payments/subscribe` - Subscribe

## 🚨 Troubleshooting

**Database connection error**:
- Ensure PostgreSQL is running: `pg_ctl status`
- Check DATABASE_URL in .env
- Create database if needed: `createdb dreamduel_dev`

**Redis connection error**:
- Ensure Redis is running: `redis-cli ping`
- Check REDIS_URL in .env

**Import errors**:
- Activate virtual environment
- Reinstall: `pip install -r requirements.txt`

**Migration errors**:
- Reset database: `alembic downgrade base && alembic upgrade head`
- Or drop and recreate: `dropdb dreamduel_dev && createdb dreamduel_dev && alembic upgrade head`

## 📖 Next Steps

1. Read full [README.md](README.md) for detailed documentation
2. Configure external services (Stripe, Cloudinary, Resend)
3. Set up OAuth (Google/Apple) if needed
4. Deploy to Railway or your preferred platform
5. Implement AI generation services (currently placeholders)

## 🆘 Get Help

- Check [README.md](README.md) for full documentation
- Review API docs at `/docs`
- Check GitHub issues
- Contact development team

---

**Note**: AI generation endpoints are PLACEHOLDER implementations. See README for integration instructions.
