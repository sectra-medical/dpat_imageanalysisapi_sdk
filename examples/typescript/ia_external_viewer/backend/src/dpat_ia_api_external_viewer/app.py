from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from dpat_ia_api_external_viewer.settings import get_settings
from dpat_ia_api_external_viewer.routers.image_analysis import (
    router as image_analysis_router,
)

settings = get_settings()

app = FastAPI()
app.include_router(image_analysis_router, prefix="/api/image_analysis")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_app_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
