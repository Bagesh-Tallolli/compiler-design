from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.upload import router as upload_router

app = FastAPI(title="Semantic Diff - Backend")

# Allow local frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
