from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional, require_role, TokenData
from app.models.skill import Skill
from app.services.skill_service import SkillService, UserService

router = APIRouter(prefix="/api/skills", tags=["skills"])


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    content: str = Field(..., min_length=1)
    platform_targets: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    @validator("slug")
    def slug_lowercase(cls, v):
        return v.lower()


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")
    content: Optional[str] = None
    platform_targets: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class SkillResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    version: str
    content: str
    platform_targets: List[str]
    tags: List[str]
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SkillListResponse(BaseModel):
    items: List[SkillResponse]
    total: int
    skip: int
    limit: int

class SkillValidationResponse(BaseModel):
    valid: bool
    errors: List[dict]


class SkillValidateRequest(BaseModel):
    content: str
    platform_targets: List[str] = []


class SkillExportResponse(BaseModel):
    content: str
    format: str


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SkillService(db)
    skill = service.create_skill(
        name=skill_data.name,
        slug=skill_data.slug,
        content=skill_data.content,
        author_id=int(current_user.sub),
        description=skill_data.description,
        version=skill_data.version,
        platform_targets=skill_data.platform_targets,
        tags=skill_data.tags,
    )
    return SkillResponse.from_orm(skill)


@router.get("", response_model=SkillListResponse)
async def list_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    platform: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    service = SkillService(db)
    author_id = int(current_user.sub) if current_user else None
    skills, total = service.list_skills(skip=skip, limit=limit, search=search, platform=platform, tag=tag, author_id=author_id)
    return SkillListResponse(
        items=[SkillResponse.from_orm(s) for s in skills],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    service = SkillService(db)
    skill = service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return SkillResponse.from_orm(skill)


@router.get("/slug/{slug}", response_model=SkillResponse)
async def get_skill_by_slug(
    slug: str,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    service = SkillService(db)
    skill = service.get_skill_by_slug(slug)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return SkillResponse.from_orm(skill)


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SkillService(db)
    skill = service.update_skill(
        skill_id=skill_id,
        author_id=int(current_user.sub),
        name=skill_data.name,
        description=skill_data.description,
        version=skill_data.version,
        content=skill_data.content,
        platform_targets=skill_data.platform_targets,
        tags=skill_data.tags,
    )
    return SkillResponse.from_orm(skill)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SkillService(db)
    service.delete_skill(skill_id, int(current_user.sub))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/validate", response_model=SkillValidationResponse)
async def validate_skill(
    request: SkillValidateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SkillService(db)
    errors = service.validate_skill(request.content, request.platform_targets)
    return SkillValidationResponse(valid=len(errors) == 0, errors=errors)


@router.get("/{skill_id}/export", response_model=SkillExportResponse)
async def export_skill(
    skill_id: int,
    format: str = Query("markdown", pattern="^(markdown|json)$"),
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    service = SkillService(db)
    content = service.export_skill(skill_id, format)
    return SkillExportResponse(content=content, format=format)


@router.get("/search/{query}", response_model=List[SkillResponse])
async def search_skills(
    query: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    service = SkillService(db)
    skills = service.search_skills(query, limit)
    return [SkillResponse.from_orm(s) for s in skills]