from fastapi import FastAPI
from .video_stream import router as video_router

api_server = FastAPI(title="Video Streaming API")
api_server.include_router(video_router, prefix="/api/video") 