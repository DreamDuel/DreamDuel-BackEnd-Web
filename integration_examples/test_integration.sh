# Test Integration Script
# Prueba la integración de los generadores con el backend

echo "🧪 Testing AI Generators Integration\n"

# Colors
GREEN='\033[0.32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "${YELLOW}1. Testing Image Generator${NC}"
curl -X POST http://localhost:5001/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mi_api_key_secreta" \
  -d '{
    "promptPrompt": "a beautiful sunset over mountains",
    "style": "realistic",
    "aspect_ratio": "16:9"
  }'

echo "\n\n${YELLOW}2. Testing Story Generator${NC}"
curl -X POST http://localhost:5002/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mi_api_key_secreta" \
  -d '{
    "prompt": "A hero discovers a hidden world",
    "tags": ["fantasy", "adventure"],
    "intensity": 0.7,
    "num_scenes": 3
  }'

echo "\n\n${YELLOW}3. Testing Health Endpoints${NC}"
echo "Image Generator Health:"
curl http://localhost:5001/health

echo "\n\nStory Generator Health:"
curl http://localhost:5002/health

echo "\n\n${GREEN}✅ Tests completed!${NC}\n"
