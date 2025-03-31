from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from .api.routes import router as api_router
from .config.supabase_client import init_supabase_client, close_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for FastAPI application.
    Initializes and closes resources when the application starts and shuts down.
    """
    # Initialize the Supabase client on startup
    logger.info("Initializing Supabase client...")
    supabase = await init_supabase_client()
    app.state.supabase = supabase
    
    logger.info("Application startup complete")
    yield
    
    # Close the Supabase client on shutdown
    logger.info("Closing Supabase client...")
    await close_supabase_client(app.state.supabase)
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Trivia API",
    description="API for trivia pack and question generation",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "Trivia API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)