"""
Project Structure Verification Script
Run this to verify all necessary files exist
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

REQUIRED_FILES = [
    # Root level
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "README.md",
    "QUICKSTART.md",
    "Dockerfile",
    "docker-compose.yml",
    "Procfile",
    "railway.toml",
    "Makefile",
    "alembic.ini",
    "pyproject.toml",
    "setup.cfg",
    
    # GitHub
    ".github/workflows/ci-cd.yml",
    
    # App core
    "app/__init__.py",
    "app/main.py",
    "app/core/__init__.py",
    "app/core/config.py",
    "app/core/security.py",
    "app/core/exceptions.py",
    "app/core/dependencies.py",
    "app/core/middleware.py",
    "app/core/celery.py",
    "app/core/tasks.py",
    
    # API
    "app/api/__init__.py",
    "app/api/router.py",
    "app/api/v1/__init__.py",
    
    # API Routes
    "app/api/v1/routes/__init__.py",
    "app/api/v1/routes/auth.py",
    "app/api/v1/routes/users.py",
    "app/api/v1/routes/stories.py",
    "app/api/v1/routes/comments.py",
    "app/api/v1/routes/payments.py",
    "app/api/v1/routes/upload.py",
    "app/api/v1/routes/generate.py",
    "app/api/v1/routes/analytics.py",
    
    # API Schemas
    "app/api/v1/schemas/__init__.py",
    "app/api/v1/schemas/auth.py",
    "app/api/v1/schemas/user.py",
    "app/api/v1/schemas/story.py",
    "app/api/v1/schemas/comment.py",
    "app/api/v1/schemas/payment.py",
    "app/api/v1/schemas/upload.py",
    "app/api/v1/schemas/generate.py",
    "app/api/v1/schemas/analytics.py",
    
    # Infrastructure
    "app/infrastructure/__init__.py",
    "app/infrastructure/database/__init__.py",
    "app/infrastructure/database/session.py",
    "app/infrastructure/database/models.py",
    "app/infrastructure/cache/__init__.py",
    "app/infrastructure/cache/redis_client.py",
    "app/infrastructure/external_services/__init__.py",
    "app/infrastructure/external_services/stripe_service.py",
    "app/infrastructure/external_services/storage_service.py",
    "app/infrastructure/external_services/email_service.py",
    "app/infrastructure/external_services/ai_image_service.py",
    "app/infrastructure/external_services/ai_story_service.py",
    
    # Utils
    "app/utils/__init__.py",
    "app/utils/pagination.py",
    "app/utils/validators.py",
    "app/utils/helpers.py",
    
    # Migrations
    "migrations/__init__.py",
    "migrations/env.py",
    "migrations/script.py.mako",
    
    # Tests
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/test_auth.py",
]


def verify_project_structure():
    """Verify all required files exist"""
    missing_files = []
    existing_files = []
    
    for file_path in REQUIRED_FILES:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    print("=" * 80)
    print("PROJECT STRUCTURE VERIFICATION")
    print("=" * 80)
    print(f"\nTotal required files: {len(REQUIRED_FILES)}")
    print(f"Existing files: {len(existing_files)}")
    print(f"Missing files: {len(missing_files)}")
    
    if missing_files:
        print("\n⚠️  MISSING FILES:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("\n✅ All required files exist!")
        return True


def verify_env_example():
    """Verify .env.example has all required variables"""
    env_example = PROJECT_ROOT / ".env.example"
    
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "JWT_SECRET",
        "STRIPE_SECRET_KEY",
        "CLOUDINARY_CLOUD_NAME",
        "RESEND_API_KEY",
    ]
    
    if not env_example.exists():
        print("\n⚠️  .env.example not found")
        return False
    
    content = env_example.read_text()
    missing_vars = [var for var in required_vars if var not in content]
    
    if missing_vars:
        print("\n⚠️  Missing environment variables in .env.example:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    else:  
        print("\n✅ All required environment variables present in .env.example")
        return True


if __name__ == "__main__":
    structure_ok = verify_project_structure()
    env_ok = verify_env_example()
    
    print("\n" + "=" * 80)
    if structure_ok and env_ok:
        print("✅ PROJECT VERIFICATION PASSED!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and fill in your values")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run migrations: alembic upgrade head")
        print("4. Start server: uvicorn app.main:app --reload")
    else:
        print("❌ PROJECT VERIFICATION FAILED!")
        print("Please fix the issues above before proceeding.")
    print("=" * 80)
