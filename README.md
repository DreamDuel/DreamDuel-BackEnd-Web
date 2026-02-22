# DreamDuel Backend API

Backend API for DreamDuel - An AI-powered visual storytelling platform that transforms user prompts into engaging, illustrated narratives.

## 🚀 Features

- **Authentication & Authorization**: JWT-based authentication with OAuth 2.0 support (Google/Apple)
- **Story Management**: Full CRUD for AI-generated stories with scenes, characters, and metadata
- **Payment Integration**: Stripe subscription management and one-time payments
- **File Storage**: Cloudinary integration for image uploads with auto-optimization
- **Email Service**: Transactional emails via Resend with HTML templates
- **Analytics**: User behavior tracking and story performance metrics
- **Caching**: Redis-based caching for improved performance
- **Background Jobs**: Celery for async task processing
- **Rate Limiting**: Request throttling to prevent abuse
- **Monitoring**: Sentry integration for error tracking

## 🏗️ Architecture

Built with Clean Architecture / Hexagonal Architecture principles:

```
app/
├── api/                    # API layer
│   └── v1/
│       ├── routes/        # API endpoints
│       └── schemas/       # Pydantic models
├── core/                  # Application core
│   ├── config.py         # Configuration
│   ├── security.py       # Authentication
│   ├── celery.py         # Background jobs
│   └── middleware.py     # Middleware
├── infrastructure/        # External services
│   ├── database/         # Database models
│   ├── external_services/ # Third-party integrations
│   └── cache/            # Redis client
└── utils/                # Utilities
```

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL + SQLAlchemy 2.0.25
- **Migrations**: Alembic 1.13.1
- **Authentication**: JWT (python-jose) + OAuth 2.0
- **Payments**: Stripe 7.12.0
- **Storage**: Cloudinary 1.38.0
- **Email**: Resend 0.7.0
- **Cache**: Redis 5.0.1
- **Background Jobs**: Celery 5.3.4
- **Testing**: pytest 7.4.4
- **Monitoring**: Sentry SDK

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd BackEnd\ DREAMDUEL\ Web
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run database migrations**
```bash
alembic upgrade head
```

6. **Start the development server**
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Using Docker

1. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI application (port 8000)
- Celery worker
- Celery beat scheduler

2. **Run migrations inside container**
```bash
docker-compose exec api alembic upgrade head
```

3. **View logs**
```bash
docker-compose logs -f api
```

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## 🚢 Deployment

### Railway (Recommended)

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
railway login
```

2. **Initialize project**
```bash
railway init
```

3. **Add environment variables**
```bash
railway variables set DATABASE_URL=<your-postgres-url>
railway variables set REDIS_URL=<your-redis-url>
railway variables set JWT_SECRET=<random-secret>
railway variables set STRIPE_SECRET_KEY=<your-stripe-key>
# ... add all required variables
```

4. **Deploy**
```bash
railway up
```

### Manual Deployment

1. **Set environment variables on your server**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run migrations**
```bash
alembic upgrade head
```

4. **Start with Gunicorn**
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## 📚 API Documentation

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/password-reset` - Request password reset
- `POST /api/auth/verify-email` - Verify email address

### Users

- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update user profile
- `POST /api/users/{id}/follow` - Follow user
- `DELETE /api/users/{id}/follow` - Unfollow user
- `GET /api/users/{id}/stories` - Get user's stories

### Stories

- `GET /api/stories` - List stories (paginated)
- `GET /api/stories/trending` - Get trending stories
- `GET /api/stories/{id}` - Get story details
- `POST /api/stories` - Create new story
- `PUT /api/stories/{id}` - Update story
- `DELETE /api/stories/{id}` - Delete story
- `POST /api/stories/{id}/like` - Like/unlike story
- `POST /api/stories/{id}/save` - Save/unsave story

### Payments

- `POST /api/payments/subscribe` - Create subscription
- `POST /api/payments/cancel` - Cancel subscription
- `POST /api/payments/webhook` - Stripe webhook handler

### Analytics

- `POST /api/analytics/event` - Track analytics event
- `GET /api/analytics/user/metrics` - Get user metrics
- `GET /api/analytics/story/{id}` - Get story analytics

Full API documentation available at `/docs` when running the server.

## 🔐 Environment Variables

Required environment variables (see `.env.example`):

```env
# App
ENVIRONMENT=development
DEBUG=True
APP_NAME=DreamDuel
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dreamduel

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Resend
RESEND_API_KEY=re_...

# Sentry (optional)
SENTRY_DSN=https://...

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 🤖 AI Generation (Placeholder)

The AI generation endpoints (`/api/generate/*`) are currently **PLACEHOLDER** implementations returning mock data. To integrate with actual AI services:

1. Choose your AI provider (Replicate, OpenAI DALL-E, Stable Diffusion, etc.)
2. Implement the service in `app/infrastructure/external_services/ai_image_service.py`
3. Update the generation endpoints in `app/api/v1/routes/generate.py`

See TODO comments in the code for specific integration points.

## 📝 Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback last migration:
```bash
alembic downgrade -1
```

## 🔄 Background Jobs

Celery tasks are defined in `app/core/celery.py`:

- `send_email_async` - Send emails in background
- `generate_story_images_async` - Generate AI images (placeholder)
- `process_analytics_batch` - Batch process analytics
- `cleanup_expired_tokens` - Clean up expired tokens

Start Celery worker:
```bash
celery -A app.core.celery worker --loglevel=info
```

Start Celery beat (for periodic tasks):
```bash
celery -A app.core.celery beat --loglevel=info
```

## 🛡️ Security

- JWT tokens with secure secret keys
- Password hashing with bcrypt
- Rate limiting (60 requests/minute per IP)
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention via ORM
- Stripe webhook signature verification

## 📊 Monitoring

- Health check endpoint: `GET /health`
- Metrics endpoint: `GET /metrics` (placeholder for Prometheus)
- Sentry for error tracking and performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software for DreamDuel.

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Contact the development team

---

Built with ❤️ using FastAPI and Python
