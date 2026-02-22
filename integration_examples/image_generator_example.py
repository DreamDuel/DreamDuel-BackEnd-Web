"""
Ejemplo de Servidor de Generación de Imágenes
==============================================

Este es un ejemplo de cómo crear un servidor que el backend de DreamDuel
puede llamar para generar imágenes con IA.

Uso:
    python image_generator_example.py
    
    El servidor correrá en http://localhost:5001

Integración con DreamDuel:
    En tu .env del backend:
    AI_IMAGE_PROVIDER=custom
    CUSTOM_IMAGE_API_URL=http://localhost:5001/generate
    CUSTOM_AI_API_KEY=mi_api_key_opcional
"""

from flask import Flask, request, jsonify
import uuid
from datetime import datetime

app = Flask(__name__)

# API Key opcional para seguridad
API_KEY = "mi_api_key_secreta"  # Opcional


def generate_ai_image(prompt, style=None, aspect_ratio="1:1", negative_prompt=None):
    """
    🔥 AQUÍ VA TU LÓGICA DE GENERACIÓN DE IA
    
    Reemplaza esto con:
    - Tu modelo de Stable Diffusion local
    - Llamada a Replicate
    - Llamada a otro servicio de IA
    - Tu pipeline personalizado
    
    Ejemplo con Stable Diffusion:
        from diffusers import StableDiffusionPipeline
        pipe = StableDiffusionPipeline.from_pretrained("model_name")
        image = pipe(prompt).images[0]
        # Guardar imagen y retornar URL
    """
    
    # MOCK: Retorna una imagen de placeholder
    # TODO: Reemplazar con tu generador real
    generation_id = str(uuid.uuid4())
    
    # Simulamos que generamos la imagen
    image_url = f"https://picsum.photos/1024/1024?random={generation_id}"
    
    return {
        "image_url": image_url,
        "generation_id": generation_id,
        "metadata": {
            "prompt": prompt,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "model": "tu-modelo-v1",
            "generated_at": datetime.utcnow().isoformat()
        }
    }


@app.route('/generate', methods=['POST'])
def generate():
    """
    Endpoint principal de generación
    
    Request:
        {
            "prompt": "a cat in space",
            "style": "anime",
            "aspect_ratio": "1:1",
            "negative_prompt": "blurry, low quality",
            "character_images": ["url1", "url2"]
        }
    
    Response:
        {
            "image_url": "https://...",
            "generation_id": "uuid",
            "credits_used": 1
        }
    """
    
    # Verificar API Key (opcional)
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.replace('Bearer ', '')
        if token != API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
    
    # Obtener datos del request
    data = request.json
    prompt = data.get('prompt')
    style = data.get('style')
    aspect_ratio = data.get('aspect_ratio', '1:1')
    negative_prompt = data.get('negative_prompt')
    character_images = data.get('character_images', [])
    
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400
    
    try:
        # Generar imagen con IA
        result = generate_ai_image(
            prompt=prompt,
            style=style,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt
        )
        
        # Respuesta al backend de DreamDuel
        return jsonify({
            "image_url": result["image_url"],
            "generation_id": result["generation_id"],
            "credits_used": 1,  # Ajustar según tu lógica
            "metadata": result["metadata"]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "image-generator",
        "version": "1.0.0"
    })


@app.route('/status/<generation_id>', methods=['GET'])
def status(generation_id):
    """
    Opcional: Endpoint para verificar estado de generación asíncrona
    """
    return jsonify({
        "generation_id": generation_id,
        "status": "completed",
        "image_url": "https://..."
    })


if __name__ == '__main__':
    print("🚀 Image Generator Server starting...")
    print("📍 URL: http://localhost:5001")
    print("📝 Endpoint: POST /generate")
    print("❤️  Health: GET /health")
    print("\nEn tu .env del backend:")
    print("AI_IMAGE_PROVIDER=custom")
    print("CUSTOM_IMAGE_API_URL=http://localhost:5001/generate")
    if API_KEY != "mi_api_key_secreta":
        print(f"CUSTOM_AI_API_KEY={API_KEY}")
    print("\n🔥 Reemplaza la función generate_ai_image() con tu modelo de IA\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
