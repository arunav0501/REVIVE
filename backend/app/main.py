from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api import api_router
from backend.app.api.health import router as health_router
from backend.app.database.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema tables exist on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="REVIVE API",
    description="Backend service for REVIVE: Review Intelligence & Virtual Intervention Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root level health routes and /api prefixed routes
app.include_router(health_router, prefix="", tags=["System"])
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "REVIVE: Review Intelligence & Virtual Intervention Engine API",
        "status": "operational",
        "docs_url": "/docs",
        "health_url": "/health",
        "api_prefix": "/api",
    }
