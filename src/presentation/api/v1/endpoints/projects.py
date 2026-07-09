from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.presentation.schemas import ProjectCreate, ProjectResponse, APIKeyCreate, APIKeyResponse
from src.presentation.api.dependencies import get_project_use_cases, get_current_user, get_db
from src.domain.entities.user import User
from src.infrastructure.database.repositories import SQLProjectRepository, SQLAPIKeyRepository

router = APIRouter()

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    proj_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    use_cases = Depends(get_project_use_cases)
):
    create_proj_uc, _ = use_cases
    project = create_proj_uc.execute(proj_in.name, proj_in.description, current_user.id)
    return project

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    repo = SQLProjectRepository(db)
    return repo.list_by_owner(current_user.id)

@router.post("/{project_id}/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    project_id: str,
    key_in: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    use_cases = Depends(get_project_use_cases)
):
    _, create_key_uc = use_cases
    try:
        api_key, raw_key = create_key_uc.execute(project_id, key_in.name, current_user.id)
        # In Pydantic response, we map properties and inject the temporary raw_key parameter
        return APIKeyResponse(
            id=api_key.id,
            project_id=api_key.project_id,
            name=api_key.name,
            key=raw_key, # Plaintext returned only once on generation
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{project_id}/api-keys", response_model=List[APIKeyResponse])
def list_api_keys(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    # Verify ownership
    proj_repo = SQLProjectRepository(db)
    project = proj_repo.get_by_id(project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        
    key_repo = SQLAPIKeyRepository(db)
    keys = key_repo.list_by_project(project_id)
    return [
        APIKeyResponse(
            id=k.id,
            project_id=k.project_id,
            name=k.name,
            is_active=k.is_active,
            created_at=k.created_at,
            last_used_at=k.last_used_at
        ) for k in keys
    ]
