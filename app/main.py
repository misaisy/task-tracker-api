import logging
from fastapi import FastAPI
from app.settings import settings

log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Task Tracker API", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    logger.info("=== Task Tracker API starting ===")
    logger.info("Environment: %s", settings.APP_ENV)
    logger.info("Port: %s", settings.APP_PORT)
    logger.info("Debug mode: %s", settings.DEBUG)
    logger.info("Log level: %s", settings.LOG_LEVEL)

@app.get("/health")
async def health():
    return {"status": "ok"}