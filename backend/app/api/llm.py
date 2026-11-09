"""LLM-powered skill analysis endpoints."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.llm_service import LLMService
from app.core.security import get_current_user
from app.models.skill import User


router = APIRouter(prefix="/api/llm", tags=["llm"])


class SkillAnalysisRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Skill content to analyze")
    platform_targets: List[str] = Field(default_factory=list, description="Target platforms")


class SkillAnalysisResponse(BaseModel):
    analysis: str
    provider: str
    model: str


class CrossPlatformRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Skill content")
    platform_targets: List[str] = Field(default_factory=list)


class CrossPlatformResponse(BaseModel):
    suggestions: str
    provider: str
    model: str


class DeprecatedAPIRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Skill content")
    platform_targets: List[str] = Field(default_factory=list)


class DeprecatedAPIResponse(BaseModel):
    findings: str
    provider: str
    model: str


class LLMStatusResponse(BaseModel):
    available: bool
    provider: Optional[str] = None
    model: Optional[str] = None


@router.get("/status", response_model=LLMStatusResponse)
async def llm_status():
    """Check if LLM integration is configured and available."""
    service = LLMService()
    available = service.is_available()
    provider = None
    model = None
    if available and service.provider:
        provider = service.provider.get_provider_name()
        model = service.provider.get_model_name()
    await service.close()
    return LLMStatusResponse(available=available, provider=provider, model=model)


@router.post("/analyze", response_model=SkillAnalysisResponse)
async def analyze_skill(
    request: SkillAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze skill for best practices and cross-platform compatibility (advisory only)."""
    service = LLMService()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider not configured. Set LLM_PROVIDER, LLM_MODEL, and LLM_API_KEY environment variables.",
        )

    try:
        analysis = await service.analyze_skill(request.content, request.platform_targets)
        return SkillAnalysisResponse(
            analysis=analysis,
            provider=service.provider.get_provider_name(),
            model=service.provider.get_model_name(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM analysis failed: {str(e)}",
        )
    finally:
        await service.close()


@router.post("/cross-platform", response_model=CrossPlatformResponse)
async def cross_platform_suggestions(
    request: CrossPlatformRequest,
    current_user: User = Depends(get_current_user),
):
    """Get cross-platform compatibility suggestions for a skill (advisory only)."""
    service = LLMService()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider not configured. Set LLM_PROVIDER, LLM_MODEL, and LLM_API_KEY environment variables.",
        )

    try:
        suggestions = await service.suggest_cross_platform_improvements(request.content, request.platform_targets)
        return CrossPlatformResponse(
            suggestions=suggestions,
            provider=service.provider.get_provider_name(),
            model=service.provider.get_model_name(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM analysis failed: {str(e)}",
        )
    finally:
        await service.close()


@router.post("/deprecated-apis", response_model=DeprecatedAPIResponse)
async def deprecated_api_detection(
    request: DeprecatedAPIRequest,
    current_user: User = Depends(get_current_user),
):
    """Detect deprecated API usage in skill content (advisory only)."""
    service = LLMService()
    if not service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider not configured. Set LLM_PROVIDER, LLM_MODEL, and LLM_API_KEY environment variables.",
        )

    try:
        findings = await service.detect_deprecated_apis(request.content, request.platform_targets)
        return DeprecatedAPIResponse(
            findings=findings,
            provider=service.provider.get_provider_name(),
            model=service.provider.get_model_name(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM analysis failed: {str(e)}",
        )
    finally:
        await service.close()

