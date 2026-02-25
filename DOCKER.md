# 🐳 Guía Docker - DreamDuel Backend

## 📋 Servicios Incluidos

El `docker-compose.yml` configura 5 servicios:

1. **PostgreSQL 15** - Base de datos principal (puerto 5432)
2. **Redis 7** - Caché y sesiones (puerto 6379)
3. **API FastAPI** - Servidor web (puerto 8000)
4. **Celery Worker** - Tareas en segundo plano
5. **Celery Beat** - Tareas programadas

---

## 🚀 Inicio Rápido

### 1. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus valores
# Nota: Para Docker, DATABASE_URL y REDIS_URL usan nombres de servicio:
# DATABASE_URL=postgresql://postgres:postgres@db:5432/dreamduel_dev
# REDIS_URL=redis://redis:6379/0
```

### 2. Levantar todos los servicios

```bash
# Construir y levantar en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f api
```

### 3. Ejecutar migraciones

```bash
# Primera vez - crear tablas
docker-compose exec api alembic upgrade head

# Crear nueva migración
docker-compose exec api alembic revision --autogenerate -m "descripción"
```

### 4. Acceder a la aplicación

- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

---

## 🛠️ Comandos Útiles

### Gestión de Servicios

```bash
# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Detener y eliminar TODO (incluyendo volúmenes)
docker-compose down -v

# Reiniciar un servicio
docker-compose restart api

# Ver estado
docker-compose ps
```

### Logs y Monitoreo

```bash
# Ver todos los logs
docker-compose logs

# Seguir logs en tiempo real
docker-compose logs -f

# Logs de un servicio
docker-compose logs -f api

# Últimas 100 líneas
docker-compose logs --tail=100 api
```

### Ejecutar Comandos

```bash
# Ejecutar comando en contenedor
docker-compose exec api python --version

# Shell interactivo
docker-compose exec api bash

# Python REPL
docker-compose exec api python

# Acceder a PostgreSQL
docker-compose exec db psql -U postgres -d dreamduel_dev

# Acceder a Redis
docker-compose exec redis redis-cli
```

### Desarrollo

```bash
# Reconstruir servicios después de cambiar código
docker-compose up -d --build

# Ver recursos utilizados
docker-compose stats

# Limpiar imágenes no utilizadas
docker system prune -a
```

---

## 🔧 Configuración del .env para Docker

```env
# App
ENVIRONMENT=development
DEBUG=True
APP_NAME=DreamDuel
SECRET_KEY=tu-secret-key-segura

# Database (usar nombre de servicio 'db')
DATABASE_URL=postgresql://postgres:postgres@db:5432/dreamduel_dev

# Redis (usar nombre de servicio 'redis')
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET=tu-jwt-secret-seguro
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# PayPal
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=tu_paypal_client_id
PAYPAL_CLIENT_SECRET=tu_paypal_client_secret
PAYPAL_WEBHOOK_ID=
PAYPAL_MONTHLY_PLAN_ID=
PAYPAL_YEARLY_PLAN_ID=

# Cloudinary
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret

# Resend
RESEND_API_KEY=re_tu_api_key
FROM_EMAIL=noreply@dreamduel.com

# Celery (usar nombre de servicio 'redis')
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
FRONTEND_URL=http://localhost:3000
```

---

## 🏗️ Solo API (sin servicios externos)

Si solo quieres el contenedor de la API:

```bash
# Construir imagen
docker build -t dreamduel-api .

# Ejecutar (requiere PostgreSQL y Redis externos)
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379/0 \
  --env-file .env \
  dreamduel-api
```

---

## 🔍 Debugging

### Ver logs de error

```bash
# Logs de la API
docker-compose logs --tail=50 api

# Logs de Celery worker
docker-compose logs --tail=50 celery_worker

# Logs de PostgreSQL
docker-compose logs --tail=50 db
```

### Conectar a base de datos

```bash
# Desde contenedor
docker-compose exec db psql -U postgres -d dreamduel_dev

# Desde tu máquina (si tienes psql instalado)
psql -h localhost -U postgres -d dreamduel_dev
```

### Reiniciar servicios con problemas

```bash
# Reiniciar solo la API
docker-compose restart api

# Reiniciar todo
docker-compose restart

# Reconstruir y reiniciar si hay cambios en código
docker-compose up -d --build --force-recreate
```

---

## 📦 Volúmenes de Datos

Los datos persisten en volúmenes Docker:

- `postgres_data` - Base de datos PostgreSQL
- `redis_data` - Datos de Redis

```bash
# Ver volúmenes
docker volume ls

# Inspeccionar volumen
docker volume inspect backend-dreamduel-web_postgres_data

# Eliminar volúmenes (¡CUIDADO! Borra todos los datos)
docker-compose down -v
```

---

## 🚀 Producción

Para producción, usa el Dockerfile directamente:

```bash
# Construir imagen optimizada
docker build -t dreamduel-api:1.0.0 .

# Ejecutar con Gunicorn (producción)
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  --name dreamduel-api \
  dreamduel-api:1.0.0
```

O desplegar en plataformas como:
- **Railway** (configurado con `railway.toml`)
- **Heroku** (configurado con `Procfile`)
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Apps**

---

## 🧪 Testing con Docker

```bash
# Ejecutar tests dentro del contenedor
docker-compose exec api pytest

# Con cobertura
docker-compose exec api pytest --cov=app --cov-report=html

# Tests específicos
docker-compose exec api pytest tests/test_auth.py -v
```

---

## 💡 Tips

1. **Primera vez**: Siempre ejecuta migraciones después de levantar
   ```bash
   docker-compose exec api alembic upgrade head
   ```

2. **Cambios en código**: Con hot-reload activado, los cambios se reflejan automáticamente

3. **Cambios en dependencias**: Reconstruye la imagen
   ```bash
   docker-compose up -d --build
   ```

4. **Problemas de red**: Asegúrate que los puertos 5432, 6379 y 8000 estén libres

5. **Limpiar todo**: Si algo falla
   ```bash
   docker-compose down -v
   docker system prune -a
   docker-compose up -d --build
   ```

---

## 📊 Estructura Docker

```
┌─────────────────────────────────────┐
│     docker-compose.yml              │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────┐  ┌──────────┐        │
│  │PostgreSQL│  │  Redis   │        │
│  │  :5432   │  │  :6379   │        │
│  └────┬─────┘  └────┬─────┘        │
│       │             │               │
│  ┌────┴─────────────┴─────┐        │
│  │   FastAPI + Uvicorn    │        │
│  │       :8000            │        │
│  └────────────────────────┘        │
│                                     │
│  ┌──────────┐  ┌──────────┐        │
│  │  Celery  │  │  Celery  │        │
│  │  Worker  │  │   Beat   │        │
│  └──────────┘  └──────────┘        │
│                                     │
└─────────────────────────────────────┘
```

---

## ✅ Checklist de Inicio

- [ ] Copiar `.env.example` a `.env`
- [ ] Completar variables de entorno
- [ ] Ejecutar `docker-compose up -d`
- [ ] Verificar servicios: `docker-compose ps`
- [ ] Ejecutar migraciones: `docker-compose exec api alembic upgrade head`
- [ ] Verificar logs: `docker-compose logs -f`
- [ ] Acceder a http://localhost:8000/docs

---

**¿Todo listo?** 🎉

```bash
docker-compose up -d && docker-compose exec api alembic upgrade head
```

Luego visita: http://localhost:8000/docs
