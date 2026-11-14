import logging
"""Provider-agnostic LLM service for skill analysis."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import httpx
import json

from app.core.config import get_settings


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    model: str
    provider: str
    usage: Optional[dict] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion from prompt."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name for this provider."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name."""
        pass


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible provider (OpenAI, Ollama, LM Studio, etc.)."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={"model": self.model, "messages": messages, "temperature": 0.3},
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage")

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.get_provider_name(),
            usage=usage,
        )

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "openai-compatible"

    async def close(self):
        await self.client.aclose()


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)

    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.3,
        }
        if system_prompt:
            body["system"] = system_prompt

        response = await self.client.post(
            f"{self.base_url}/v1/messages",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()

        content = data["content"][0]["text"]
        usage = data.get("usage")

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.get_provider_name(),
            usage=usage,
        )

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "anthropic"

    async def close(self):
        await self.client.aclose()


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://generativelanguage.googleapis.com").rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)

    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        body = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2000},
        }

        response = await self.client.post(
            f"{self.base_url}/v1beta/models/{self.model}:generateContent",
            headers=headers,
            params=params,
            json=body,
        )
        response.raise_for_status()
        data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata")

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.get_provider_name(),
            usage=usage,
        )

    def get_model_name(self) -> str:
        return self.model

    def get_provider_name(self) -> str:
        return "gemini"

    async def close(self):
        await self.client.aclose()


def create_llm_provider() -> Optional[LLMProvider]:
    """Create LLM provider from settings."""
    settings = get_settings()

    if not settings.llm_provider or not settings.llm_model or not settings.llm_api_key:
        return None

    provider = settings.llm_provider.lower()
    model = settings.llm_model
    api_key = settings.llm_api_key
    base_url = settings.llm_base_url

    if provider in ("openai", "ollama", "lmstudio", "openai-compatible"):
        if not base_url:
            base_url = "https://api.openai.com/v1" if provider == "openai" else "http://localhost:11434/v1"
        return OpenAICompatibleProvider(base_url, api_key, model)
    elif provider == "anthropic":
        return AnthropicProvider(api_key, model, base_url)
\n    elif provider == "mock":\
        return MockProvider(api_key, model)
    elif provider == "gemini":
        return GeminiProvider(api_key, model, base_url)

    return None


class LLMService:
    """Service for LLM-powered skill analysis."""

    def __init__(self):
        self.provider = create_llm_provider()

    def is_available(self) -> bool:
        return self.provider is not None

    async def analyze_skill(self, skill_content: str, platform_targets: list[str]) -> str:
        """Analyze skill content for best practices and cross-platform compatibility."""
        if not self.provider:
            raise RuntimeError("LLM provider not configured")

        system_prompt = """You are an expert iOS/macOS/visionOS/watchOS/tvOS developer specializing in SwiftUI and cross-platform development.
Analyze the provided skill file content and provide advisory suggestions for:
1. Best practices for SwiftUI development
2. Cross-platform compatibility improvements
3. Deprecated API usage detection
4. Modern SwiftUI patterns (iOS 17+, macOS 14+)
5. Accessibility considerations
6. Performance optimizations

Format your response as structured markdown with clear sections. All suggestions are advisory only - never execute code changes automatically."""

        prompt = f"""Analyze this skill file for a developer building cross-platform SwiftUI applications.

Platform targets: {', '.join(platform_targets) if platform_targets else 'Not specified'}

Skill content:
```
{skill_content}
```

Provide advisory analysis with specific, actionable suggestions."""

        response = await self.provider.complete(prompt, system_prompt)
        return response.content

    async def suggest_cross_platform_improvements(self, skill_content: str, platform_targets: list[str]) -> str:
        """Suggest improvements for cross-platform compatibility."""
        if not self.provider:
            raise RuntimeError("LLM provider not configured")

        system_prompt = """You are an expert in cross-platform SwiftUI development for iOS, macOS, visionOS, watchOS, and tvOS.
Analyze the skill content and suggest specific improvements for cross-platform compatibility.
Focus on: view modifiers, navigation patterns, layout systems, platform-specific APIs, and availability handling."""

        prompt = f"""Suggest cross-platform compatibility improvements for this skill:

Platform targets: {', '.join(platform_targets) if platform_targets else 'Not specified'}

Skill content:
```
{skill_content}
```

Provide specific, actionable suggestions with code examples where helpful."""

        response = await self.provider.complete(prompt, system_prompt)
        return response.content

    async def detect_deprecated_apis(self, skill_content: str, platform_targets: list[str]) -> str:
        """Detect deprecated API usage in skill content."""
        if not self.provider:
            raise RuntimeError("LLM provider not configured")

        system_prompt = """You are an expert in Swift/SwiftUI API deprecation timelines.
Analyze the skill content and identify any deprecated API usage.
Consider the minimum deployment targets for each platform target.
Report findings with specific line references and migration suggestions."""

        prompt = f"""Detect deprecated APIs in this skill content:

Platform targets: {', '.join(platform_targets) if platform_targets else 'Not specified'}

Skill content:
```
{skill_content}
```

List any deprecated APIs found with migration paths."""

        response = await self.provider.complete(prompt, system_prompt)
        return response.content

    async def close(self):
        if self.provider and hasattr(self.provider, 'close'):
            await self.provider.close()

