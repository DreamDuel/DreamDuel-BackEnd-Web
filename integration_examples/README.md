# Ejemplos de Integración de Generadores de IA

Esta carpeta contiene ejemplos de cómo crear tus propios servicios de IA que se integran con el backend de DreamDuel.

## 📁 Contenido

1. `image_generator_example.py` - Servidor Flask de ejemplo para generación de imágenes
2. `story_generator_example.py` - Servidor FastAPI de ejemplo para generación de historias  
3. `test_integration.sh` - Script para probar la integración

## 🚀 Uso Rápido

### 1. Instalar dependencias

```bash
cd integration_examples
pip install flask fastapi uvicorn requests
```

### 2. Levantar generador de imágenes

```bash
python image_generator_example.py
# Corre en http://localhost:5001
```

### 3. Levantar generador de historias

```bash
python story_generator_example.py
# Corre en http://localhost:5002
```

### 4. Configurar backend

En tu `.env`:
```env
AI_IMAGE_PROVIDER=custom
CUSTOM_IMAGE_API_URL=http://localhost:5001/generate

AI_STORY_PROVIDER=custom
CUSTOM_STORY_API_URL=http://localhost:5002/generate
```

### 5. Iniciar backend

```bash
docker compose up -d
```

## 📝 Notas

- Estos son **ejemplos simplificados** que retornan datos mock
- Reemplaza la lógica mock con tus modelos de IA reales
- Los ejemplos muestran la estructura de API esperada por el backend

## 🔧 Personalización

1. **Para imágenes**: Modifica `image_generator_example.py` línea 20-30
2. **Para historias**: Modifica `story_generator_example.py` línea 25-40
3. Integra tus modelos de IA (Stable Diffusion, GPT, etc.)
