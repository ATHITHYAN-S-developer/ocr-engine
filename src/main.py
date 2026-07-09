from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.config import settings
from src.presentation.api.v1.router import api_router
from src.domain.exceptions import DomainException, EntityNotFoundException, UnauthorizedException, InvalidCredentialsException
from src.infrastructure.database.session import engine, Base

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade pluggable OCR Engine service.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount frontend static portal
app.mount("/portal", StaticFiles(directory="src/presentation/static", html=True), name="portal")

# Initialize database tables on startup (Development/Fallback mode)
@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create tables on startup (DB might be offline): {e}")

# Global Custom Domain Exception Handling
@app.exception_handler(DomainException)
def domain_exception_handler(request: Request, exc: DomainException):
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, EntityNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (UnauthorizedException, InvalidCredentialsException)):
        status_code = status.HTTP_401_UNAUTHORIZED
        
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc), "error_type": exc.__class__.__name__}
    )

@app.get("/")
def read_root():
    return {
        "service": settings.APP_NAME,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
