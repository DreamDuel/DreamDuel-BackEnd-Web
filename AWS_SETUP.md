# AWS Native Setup Guide

Esta es la **branch `aws-native`** - Versión exclusiva con servicios AWS nativos.

## 🔄 Diferencias con main branch

| Servicio | Main Branch | AWS-Native Branch |
|----------|-------------|-------------------|
| **Storage** | Cloudinary | AWS S3 |
| **Email** | Resend | AWS SES |
| **Database** | PostgreSQL | PostgreSQL (compatible con RDS) |
| **Cache** | Redis | Redis (compatible con ElastiCache) |
| **Payments** | PayPal | PayPal (igual) |

## ⚙️ Configuración AWS

### 1. Crear usuario IAM

1. Ve a AWS IAM Console → Users → Create User
2. Nombre: `dreamduel-backend`
3. Attach policies:
   - `AmazonS3FullAccess`
   - `AmazonSESFullAccess`
4. Crea Access Keys → Guarda:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

### 2. Configurar S3

```bash
# Crear bucket
aws s3 mb s3://dreamduel-production --region us-east-1

# Configurar CORS (si necesitas acceso desde frontend)
aws s3api put-bucket-cors --bucket dreamduel-production --cors-configuration file://s3-cors.json
```

**s3-cors.json:**
```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://dreamduel.com", "http://localhost:3000"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

### 3. Configurar SES

1. Ve a AWS SES Console
2. **Verify email address:**
   - Verifica `noreply@dreamduel.com`
   - O verifica tu dominio completo

3. **Salir de Sandbox Mode** (para enviar a cualquier email):
   - Request production access en SES console
   - AWS puede tardar 24 horas en aprobar

**Mientras estés en Sandbox:**
- Solo puedes enviar emails a direcciones verificadas
- Verifica manualmente los emails de testing

### 4. Variables de Entorno

Agrega a tu `.env`:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1

# AWS S3 Storage
AWS_S3_BUCKET=dreamduel-production

# AWS SES Email
AWS_SES_REGION=us-east-1
FROM_EMAIL=noreply@dreamduel.com
```

## 🚀 Despliegue en AWS

### Opción 1: EC2

```bash
# Instalar dependencias
sudo yum update -y
sudo yum install python3 postgresql-devel -y

# Clonar repo
git clone https://github.com/DreamDuel/DreamDuel-BackEnd-Web.git
cd DreamDuel-BackEnd-Web
git checkout aws-native

# Instalar Python packages
pip3 install -r requirements.txt

# Configurar .env con credenciales AWS

# Ejecutar con gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Opción 2: ECS/Fargate

```bash
# Build Docker image
docker build -t dreamduel-backend .

# Tag y push a ECR
aws ecr create-repository --repository-name dreamduel-backend
docker tag dreamduel-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/dreamduel-backend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/dreamduel-backend:latest

# Deploy con Fargate (usar AWS Console o Terraform)
```

### Opción 3: Elastic Beanstalk

```bash
# Instalar EB CLI
pip install awsebcli

# Inicializar
eb init -p python-3.12 dreamduel-backend

# Crear environment
eb create dreamduel-production

# Deploy
eb deploy
```

## 🗄️ Servicios Recomendados AWS

### Database: RDS PostgreSQL

```env
DATABASE_URL=postgresql://username:password@dreamduel-db.xxx.us-east-1.rds.amazonaws.com:5432/dreamduel
```

### Cache: ElastiCache Redis

```env
REDIS_URL=redis://dreamduel-redis.xxx.cache.amazonaws.com:6379/0
```

### CDN: CloudFront (para S3)

1. Crea CloudFront distribution con S3 como origin
2. Actualiza URLs en storage_service.py:
   ```python
   url = f"https://d111111abcdef8.cloudfront.net/{key}"
   ```

## 💰 Costos Estimados (Free Tier)

| Servicio | Free Tier | Después Free Tier |
|----------|-----------|-------------------|
| **S3** | 5GB storage, 20K GET, 2K PUT | ~$0.023/GB/mes |
| **SES** | 62,000 emails/mes (desde EC2) | $0.10/1000 emails |
| **EC2 t2.micro** | 750 horas/mes | ~$8.50/mes |
| **RDS t3.micro** | 750 horas/mes | ~$15/mes |
| **ElastiCache t2.micro** | (no free tier) | ~$12/mes |

## 🔒 Seguridad

1. **Nunca hardcodees credenciales AWS**
2. Usa IAM roles en EC2/ECS en vez de access keys cuando sea posible
3. Configura bucket policies en S3 para acceso público limitado
4. Habilita CloudTrail para auditoría
5. Usa AWS Secrets Manager para credenciales sensibles

## 🧪 Testing Local

```bash
# Usar LocalStack para simular AWS localmente
pip install localstack
localstack start

# Configurar para LocalStack
export AWS_ENDPOINT_URL=http://localhost:4566
```

## 📚 Referencias

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS SES Documentation](https://docs.aws.amazon.com/ses/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

## ⚠️ Notas Importantes

- **S3 NO hace transformaciones de imágenes** como Cloudinary
  - Considera usar CloudFront + Lambda@Edge para resize
  - O usa bibliotecas como Pillow para pre-procesar
  
- **SES requiere salir de Sandbox** para producción
  - En Sandbox solo envías a emails verificados
  - Request production access toma ~24h

- **ElastiCache es caro** para desarrollo
  - Usa Redis local o Upstash Redis para dev
  - Usa ElastiCache solo en producción
