import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers.auth_router import router as auth_router
from routers.admin_router import router as admin_router
from routers.horarios_router import router as horarios_router
from routers.pacientes_router import router as pacientes_router
from utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

if settings.ENVIRONMENT == "development":
    origins = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ]
else:
    origins = [settings.FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(horarios_router)
app.include_router(pacientes_router)

@app.get("/")
async def root():
    return {"message": "***** Bienvenido a MediConnect *****"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
