from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.claims import router as claims_router
from backend.app.api.predictions import router as predictions_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.rag import router as rag_router
from backend.app.api.agent import router as agent_router
from backend.app.api.generator import router as generator_router
from backend.app.api.simulator import router as simulator_router
from backend.app.api.closed_loop import router as closed_loop_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["System"])
api_router.include_router(claims_router, prefix="", tags=["Claims"])
api_router.include_router(predictions_router, prefix="", tags=["Predictions"])
api_router.include_router(dashboard_router, prefix="", tags=["Dashboard"])
api_router.include_router(rag_router, prefix="", tags=["RAG Knowledge Engine"])
api_router.include_router(agent_router, prefix="", tags=["AI Follow-Up Agent"])
api_router.include_router(generator_router, prefix="", tags=["Follow-Up Artifact Generator"])
api_router.include_router(simulator_router, prefix="", tags=["Payer Response Simulator"])
api_router.include_router(closed_loop_router, prefix="", tags=["Closed Loop Autonomous Recovery Engine"])







