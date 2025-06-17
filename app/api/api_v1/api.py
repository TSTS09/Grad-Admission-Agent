from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, chat, faculty, programs, users, universities

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(faculty.router, prefix="/faculty", tags=["faculty"])
api_router.include_router(programs.router, prefix="/programs", tags=["programs"])
api_router.include_router(universities.router, prefix="/universities", tags=["universities"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
