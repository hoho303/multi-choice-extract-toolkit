from fastapi import APIRouter

from api.routes import file
from services.starter import init_api
from core import cfg
from fastapi.staticfiles import StaticFiles

api_router = APIRouter()

api_router.include_router(file.router, tags=["file"], prefix="/file")

@api_router.on_event("startup")
async def startup_event():
    # Thực hiện các công việc chuẩn bị khi router bắt đầu chạy):
    init_api()
    print("Router started")
    return None