from fastapi import FastAPI
from app.db.database import engine
from app.db import models
from app.api import urls
from fastapi.responses import Response



from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LinkForge API",
    description="Enterprise Link Management & Analytics Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(urls.router)


@app.get("/")
def health_check():
    return {"status": "running"}

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)