from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.sql import text
from datetime import datetime
import redis
from src.presentation.schemas import HealthResponse
from src.presentation.api.dependencies import get_db
from src.config import settings

router = APIRouter()

@router.get("", response_model=HealthResponse)
def health_check(db = Depends(get_db)):
    """
    Performs live queries against PostgreSQL and Redis to verify complete backend operational state.
    """
    db_status = "healthy"
    redis_status = "healthy"
    
    # 1. Database Check
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        
    # 2. Redis Check
    try:
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=1)
        r.ping()
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    if "unhealthy" in db_status or "unhealthy" in redis_status:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": db_status,
                "redis": redis_status,
                "timestamp": datetime.utcnow()
            }
        )

    return HealthResponse(
        status="healthy",
        database=db_status,
        redis=redis_status,
        timestamp=datetime.utcnow()
    )
