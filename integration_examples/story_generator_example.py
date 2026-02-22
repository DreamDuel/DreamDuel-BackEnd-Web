"""
Ejemplo de Servidor de Generación de Historias
==============================================

Este es un ejemplo de cómo crear un servidor que el backend de DreamDuel
puede llamar para generar historias/narrativas con IA.

Uso:
    python story_generator_example.py
    
    El servidor correrá en http://localhost:5002

Integración con DreamDuel:
    En tu .env del backend:
    AI_STORY_PROVIDER=custom
    CUSTOM_STORY_API_URL=http://localhost:5002/generate
    CUSTOM_AI_API_KEY=mi_api_key_opcional
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import uvicorn

app = FastAPI(title="Story Generator Service")

# API Key opcional
API_KEY = "mi_api_key_secreta"


class Character(BaseModel):
    name: str
    description: Optional[str] = None


class StoryRequest(BaseModel):
    prompt: str
    tags: List[str] = []
    intensity: float = 0.5
    num_scenes: int = 5
    characters: Optional[List[Character]] = None


class Scene(BaseModel):
    scene_number: int
    description: str
    image_prompt: str


class StoryResponse(BaseModel):
    title: str
    synopsis: str
    scenes: List[Scene]
    generation_id: str


def generate_ai_story(
    prompt: str,
    tags: List[str],
    intensity: float,
    num_scenes: int,
    characters: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    🔥 AQUÍ VA TU LÓGICA DE GENERACIÓN DE HISTORIAS
    
    Reemplaza esto con:
    - OpenAI GPT-4
    - Anthropic Claude
    - Tu modelo LLM personalizado
    - Pipeline de generación de narrativas
    
    Ejemplo con OpenAI:
        from openai import OpenAI
        client = OpenAI(api_key="tu_key")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative storyteller"},
                {"role": "user", "content": prompt}
            ]
        )
        # Procesar respuesta y estructurar en escenas
    """
    
    # MOCK: Genera una historia de ejemplo
    # TODO: Reemplazar con tu generador real
    
    title = f"Historia: {prompt[:50]}"
    synopsis = f"Una emocionante aventura sobre {prompt}. "
    synopsis += "Con giros inesperados y personajes memorables."
    
    scenes = []
    for i in range(num_scenes):
        scenes.append({
            "scene_number": i + 1,
            "description": f"Escena {i+1}: La historia se desarrolla con {prompt}...",
            "image_prompt": f"{tags[0] if tags else 'fantasy'} scene {i+1}, {prompt}"
        })
    
    return {
        "title": title,
        "synopsis": synopsis,
        "scenes": scenes,
        "generation_id": str(uuid.uuid4()),
        "metadata": {
            "tags": tags,
            "intensity": intensity,
            "num_scenes": num_scenes,
            "model": "tu-modelo-llm-v1",
            "generated_at": datetime.utcnow().isoformat()
        }
    }


@app.post("/generate", response_model=StoryResponse)
async def generate_story(
    request: StoryRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Endpoint principal de generación de historias
    
    Request:
        {
            "prompt": "A hero's journey through space",
            "tags": ["scifi", "adventure"],
            "intensity": 0.7,
            "num_scenes": 5,
            "characters": [
                {"name": "Hero", "description": "Brave astronaut"}
            ]
        }
    
    Response:
        {
            "title": "Journey Beyond Stars",
            "synopsis": "An epic space adventure...",
            "scenes": [
                {
                    "scene_number": 1,
                    "description": "The hero prepares...",
                    "image_prompt": "astronaut in futuristic spacesuit"
                }
            ],
            "generation_id": "uuid"
        }
    """
    
    # Verificar API Key (opcional)
    if authorization:
        token = authorization.replace('Bearer ', '')
        if token != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Generar historia con IA
        result = generate_ai_story(
            prompt=request.prompt,
            tags=request.tags,
            intensity=request.intensity,
            num_scenes=request.num_scenes,
            characters=[c.dict() for c in request.characters] if request.characters else None
        )
        
        return StoryResponse(
            title=result["title"],
            synopsis=result["synopsis"],
            scenes=[
                Scene(
                    scene_number=s["scene_number"],
                    description=s["description"],
                    image_prompt=s["image_prompt"]
                ) for s in result["scenes"]
            ],
            generation_id=result["generation_id"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "story-generator",
        "version": "1.0.0"
    }


@app.get("/status/{generation_id}")
async def status(generation_id: str):
    """Opcional: Endpoint para verificar estado de generación asíncrona"""
    return {
        "generation_id": generation_id,
        "status": "completed",
        "story": "..."
    }


if __name__ == '__main__':
    print("🚀 Story Generator Server starting...")
    print("📍 URL: http://localhost:5002")
    print("📝 Endpoint: POST /generate")
    print("📚 Docs: http://localhost:5002/docs")
    print("❤️  Health: GET /health")
    print("\nEn tu .env del backend:")
    print("AI_STORY_PROVIDER=custom")
    print("CUSTOM_STORY_API_URL=http://localhost:5002/generate")
    if API_KEY != "mi_api_key_secreta":
        print(f"CUSTOM_AI_API_KEY={API_KEY}")
    print("\n🔥 Reemplaza la función generate_ai_story() con tu modelo LLM\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5002)
