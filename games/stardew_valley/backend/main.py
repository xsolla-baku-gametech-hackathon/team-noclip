import logging
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.models import GameStateDto, RecapResponseDto
from backend.services.cache_service import cache_service
from backend.services.heuristic_service import generate_heuristic_recap
from backend.services.llm_service import generate_llm_recap
from backend.services.xml_parser import parse_save_xml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("xsolla_recap")

app = FastAPI(
    title="Xsolla Game Recap API",
    description="Context-aware in-game recap and reminder middleware for Stardew Valley.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "Xsolla Game Recap API",
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "llm_enabled": settings.ENABLE_LLM and bool(settings.GEMINI_API_KEY),
        "model": settings.GEMINI_MODEL,
        "timeout_seconds": settings.HTTP_TIMEOUT_SECONDS,
        "cached_entries": cache_service.size,
    }


@app.post("/api/recap", response_model=RecapResponseDto)
async def generate_recap(state: GameStateDto):
    """
    Main recap endpoint invoked by the SMAPI mod on F8 press or menu open.
    First checks SHA-256 fingerprint cache for sub-millisecond instant return.
    If uncached, generates through Gemini LLM or heuristic fallback, then caches.
    """
    # 1. Check in-memory state fingerprint cache
    cached = cache_service.get(state)
    if cached is not None:
        logger.info("Fingerprint cache HIT. Returning cached recap instantly.")
        return cached

    # 2. Generate recap via LLM (or heuristic failover)
    try:
        response = await generate_llm_recap(state)
    except Exception as e:
        logger.error(f"Unhandled error during recap generation: {e}")
        response = generate_heuristic_recap(state)

    # 3. Store in cache
    cache_service.set(state, response)
    return response


@app.post("/api/recap/heuristic", response_model=RecapResponseDto)
def generate_heuristic_recap_endpoint(state: GameStateDto):
    """
    Direct endpoint for testing the instant deterministic fallback engine without LLM.
    """
    return generate_heuristic_recap(state)


@app.post("/api/recap/from-xml", response_model=RecapResponseDto)
async def generate_recap_from_xml(file: UploadFile = File(...)):
    """
    Endpoint for uploading a Stardew Valley save XML file.
    Parses the file into GameStateDto and generates a recap.
    """
    try:
        contents = await file.read()
        state = parse_save_xml(contents)
        return await generate_recap(state)
    except Exception as e:
        logger.error(f"Error parsing save XML file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse save XML: {str(e)}")


def require_admin_key(x_api_key: str = Header(default="")):
    """Requires a valid X-API-Key header matching ADMIN_API_KEY for admin-only endpoints."""
    if not settings.ADMIN_API_KEY or not secrets.compare_digest(x_api_key, settings.ADMIN_API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/api/cache/clear", dependencies=[Depends(require_admin_key)])
def clear_cache():
    """Clears all cached recap entries. Requires admin authentication."""
    cache_service.clear()
    return {"status": "cleared", "cached_entries": 0}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
    )
