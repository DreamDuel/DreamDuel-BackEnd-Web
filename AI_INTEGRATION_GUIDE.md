# 🤖 Guía de Integración de Generadores de IA

## 📋 Resumen

El backend está completamente preparado para integrar **2 generadores de IA separados**:

1. **Generador 1: Imágenes** → `ai_image_service.py`
2. **Generador 2: Historias/Texto** → `ai_story_service.py`

---

## 🔌 Arquitectura de Integración

```
┌──────────────────────────────────────────────────┐
│       DreamDuel Backend (FastAPI)                │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │   API Routes (/api/generate/*)             │ │
│  └────────────┬───────────────────────────────┘ │
│               │                                  │
│  ┌────────────▼───────────────────────────────┐ │
│  │   AI Service Layer (app/infrastructure/)  │ │
│  │                                            │ │
│  │  ┌─────────────────┐  ┌─────────────────┐ │ │
│  │  │ ai_image_       │  │ ai_story_       │ │ │
│  │  │ service.py      │  │ service.py      │ │ │
│  │  │                 │  │                 │ │ │
│  │  │ Multi-provider: │  │ Multi-provider: │ │ │
│  │  │ • Replicate     │  │ • OpenAI GPT    │ │ │
│  │ │ • OpenAI DALL-E │  │ • Anthropic     │ │ │
│  │  │ • Stability     │  │ • Custom API    │ │ │
│  │  │ • CUSTOM API ⭐ │  │ • CUSTOM API ⭐ │ │ │
│  │  └─────────────────┘  └─────────────────┘ │ │
│  └────────────┬───────────────┬───────────────┘ │
│               │               │                  │
└───────────────┼───────────────┼──────────────────┘
                │               │
     ┌──────────▼──────┐  ┌────▼──────────┐
     │  TU GENERADOR   │  │  TU GENERADOR │
     │  DE IMÁGENES    │  │  DE HISTORIAS │
     │  (HTTP API)     │  │  (HTTP API)   │
     └─────────────────┘  └───────────────┘
```

---

## 🎯 Opción 1: Integrar Generadores Propios (CUSTOM API)

### Configuración en .env

```env
# Generador 1: Imágenes
AI_IMAGE_PROVIDER=custom
CUSTOM_IMAGE_API_URL=http://localhost:5001/generate
CUSTOM_AI_API_KEY=tu_api_key_opcional

# Generador 2: Historias
AI_STORY_PROVIDER=custom
CUSTOM_STORY_API_URL=http://localhost:5002/generate
```

### Generador de Imágenes - Contrato de API

Tu servicio de generación de imágenes debe aceptar:

**Request (POST to CUSTOM_IMAGE_API_URL):**
```json
{
  "prompt": "a cat in space, anime style",
  "style": "anime",
  "aspect_ratio": "1:1",
  "negative_prompt": "blurry, low quality",
  "character_images": ["https://url-to-character1.jpg"]
}
```

**Response:**
```json
{
  "image_url": "https://your-storage.com/generated-image.png",
  "generation_id": "opcional-id-unico",
  "credits_used": 1
}
```

### Generador de Historias - Contrato de API

Tu servicio de generación de historias debe aceptar:

**Request (POST to CUSTOM_STORY_API_URL):**
```json
{
  "prompt": "A hero's journey through space",
  "tags": ["scifi", "adventure"],
  "intensity": 0.7,
  "num_scenes": 5,
  "characters": [
    {"name": "Hero", "description": "Brave astronaut"}
  ]
}
```

**Response:**
```json
{
  "title": "Journey Beyond Stars",
  "synopsis": "An epic space adventure...",
  "scenes": [
    {
      "scene_number": 1,
      "description": "The hero prepares for launch...",
      "image_prompt": "astronaut in futuristic spacesuit"
    },
    {
      "scene_number": 2,
      "description": "Launch sequence begins...",
      "image_prompt": "rocket launching into space"
    }
  ]
}
```

---

## 🚀 Opción 2: Usar Servicios Externos (Replicate/OpenAI)

### Para Imágenes - Replicate

```env
AI_IMAGE_PROVIDER=replicate
REPLICATE_API_KEY=r8_tu_api_key
```

**Código en `ai_image_service.py` (línea ~85):**
```python
# Descomentar esta sección:
import replicate

output = replicate.run(
    "black-forest-labs/flux-schnell",
    input={
        "prompt": f"{style or ''} {prompt}".strip(),
        "aspect_ratio": aspect_ratio
    }
)

return {
    "image_url": output[0],
    "generation_id": str(uuid.uuid4()),
    "credits_used": 1
}
```

### Para Historias - OpenAI GPT

```env
AI_STORY_PROVIDER=openai
OPENAI_API_KEY=sk-tu_api_key
```

**Código en `ai_story_service.py` (línea ~35):**
```python
# Descomentar esta sección:
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{
        "role": "system",
        "content": "You are a creative storyteller..."
    }, {
        "role": "user",
        "content": prompt
    }]
)

# Parse response and return structured story
```

---

## 🛠️ Implementación Paso a Paso

### Si tienes tus propios generadores:

1. **Levantar tus servicios de IA:**
   ```bash
   # En terminal 1 - Generador de imágenes
   cd tu-generador-imagenes
   python app.py  # o tu comando de inicio
   # Debe correr en http://localhost:5001
   
   # En terminal 2 - Generador de historias
   cd tu-generador-historias
   python app.py
   # Debe correr en http://localhost:5002
   ```

2. **Configurar .env del backend:**
   ```env
   AI_IMAGE_PROVIDER=custom
   CUSTOM_IMAGE_API_URL=http://localhost:5001/generate
   
   AI_STORY_PROVIDER=custom
   CUSTOM_STORY_API_URL=http://localhost:5002/generate
   ```

3. **Iniciar backend:**
   ```bash
   docker compose up -d
   ```

4. **Probar integración:**
   ```bash
   # Generar imagen
   curl -X POST http://localhost:8000/api/generate/image \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "a beautiful landscape",
       "style": "realistic"
     }'
   
   # Generar historia
   curl -X POST http://localhost:8000/api/generate/story \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "An adventure in space",
       "num_scenes": 5
     }'
   ```

---

## 📝 Archivos Clave

### Backend Files:
- `app/infrastructure/external_services/ai_image_service.py` - Servicio de imágenes
- `app/infrastructure/external_services/ai_story_service.py` - Servicio de historias
- `app/api/v1/routes/generate.py` - Endpoints de generación
- `app/core/config.py` - Configuración de providers

### Configuración:
- `.env` - Variables de entorno
- `docker-compose.yml` - Orquestación de servicios

---

## 🔧 Opciones de Deployment

### Opción A: Todo en Docker

**docker-compose.yml extendido:**
```yaml
services:
  # Backend DreamDuel
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - image_generator
      - story_generator
  
  # Tu generador de imágenes
  image_generator:
    build: ./path-to-your-image-generator
    ports:
      - "5001:5001"
  
  # Tu generador de historias
  story_generator:
    build: ./path-to-your-story-generator
    ports:
      - "5002:5002"
```

### Opción B: Generadores externos

Si tus generadores ya están desplegados en otro servidor:

```env
CUSTOM_IMAGE_API_URL=https://tu-servicio-imagenes.com/api/generate
CUSTOM_STORY_API_URL=https://tu-servicio-historias.com/api/generate
CUSTOM_AI_API_KEY=tu_api_key_compartida
```

---

## ✅ Checklist de Integración

- [ ] Generador de imágenes acepta POST con `prompt`, `style`, `aspect_ratio`
- [ ] Generador de imágenes retorna `image_url`
- [ ] Generador de historias acepta POST con `prompt`, `tags`, `num_scenes`
- [ ] Generador de historias retorna `title`, `synopsis`, `scenes[]`
- [ ] Variables configuradas en `.env`
- [ ] Backend puede conectarse a ambos servicios
- [ ] Tested con `curl` o Postman
- [ ] Autenticación funcionando (si es necesaria)

---

## 🐛 Troubleshooting

### Error: "Connection refused"
- Verifica que tus generadores estén corriendo
- Verifica URLs en .env
- Si usas Docker, usa nombres de servicio en lugar de localhost

### Error: "API key not configured"
- Verifica que `CUSTOM_AI_API_KEY` esté en`.env` si tu servicio lo requiere

### Error: "Invalid response"
- Verifica que el formato de respuesta coincida con el contrato
- Revisa logs del backend: `docker compose logs -f api`

---

## 📚 Ejemplos

Ver carpeta `integration_examples/` para:
- Ejemplo de servidor de imágenes Flask
- Ejemplo de servidor de historias FastAPI
- Scripts de testing

---

## 🆘 Soporte

Si tienes problemas:
1. Revisa logs: `docker compose logs -f api`
2. Verifica conectividad: `curl http://localhost:5001/health`
3. Revisa archivos de servicio en `app/infrastructure/external_services/`

---

**¡Listo para integrar!** 🚀
