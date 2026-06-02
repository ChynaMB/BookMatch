from fastapi import FastAPI
from src.routes.recommendations import router as recommendations_router

app = FastAPI()

app.include_router(recommendations_router)