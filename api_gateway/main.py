import os
import json
import uvicorn
from fastapi import FastAPI, Request
from typing import Annotated
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException, FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.routes.router import api_router
# from core.config import API_PREFIX, APP_NAME, APP_VERSION, IS_DEBUG
from core.event_handlers import start_app_handler, stop_app_handler
from core.error_handlers import api_exception_handler
from core import cfg
from models.common_schemas import APIException

def get_app() -> FastAPI:
    API_PREFIX = "/api"
    # fast_app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=IS_DEBUG)
    fast_app = FastAPI(debug=True)
    fast_app.include_router(api_router, prefix=API_PREFIX)
    fast_app.add_event_handler("startup", start_app_handler(fast_app))
    fast_app.add_event_handler("shutdown", stop_app_handler(fast_app))
    fast_app.add_exception_handler(APIException, api_exception_handler)

    return fast_app

print("+++++++++++++++++++++++++++++++++++++++++++")

app = get_app() 
origins = ["*"]

# Handle CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    cfg.work_dir = os.getcwd()
    print("+++++++++++++++++++++++++++++++++++++++++++")
    print('Workind dir = ', cfg.work_dir)
    uvicorn.run("main:app", host="0.0.0.0", port=7000,
                reload=True, reload_dirs=cfg.work_dir)