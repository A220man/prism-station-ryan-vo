from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, select
from fastapi import HTTPException, status

from app.models.skill import Skill, User, AuditLog
from app.core.security import get_password_hash


class SkillService:
    def __init__(self, db: Session):
        self.db = db

    def create_skill(
        self,
        name: str,
        slug: str,
        content: str,
        author_id: int,
        description: Optional[str] = None,
        version: str = "1.0.0",
        platform_targets: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Skill:
        existing = self.db.query(Skill).filter(Skill.slug == slug).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill slug already exists")

        skill = Skill(
            name=name,
            slug=slug,
            content=content,
            author_id=author_id,
            description=description,
            version=version,
            platform_targets=platform_targets or [],
            tags=tags or [],
        )
        self.db.add(skill)
        self.db.flush()
        self._log_audit(author_id, "create", "skill", str(skill.id), {"name": name, "slug": slug})
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def get_skill(self, skill_id: int) -> Optional[Skill]:
        return self.db.query(Skill).filter(Skill.id == skill_id).first()

    def get_skill_by_slug(self, slug: str) -> Optional[Skill]:
        return self.db.query(Skill).filter(Skill.slug == slug).first()

    def list_skills(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        platform: Optional[str] = None,
        tag: Optional[str] = None,
        author_id: Optional[int] = None,
    ) -> Tuple[List[Skill], int]:
        query = self.db.query(Skill)

        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(Skill.name.ilike(search_term), Skill.content.ilike(search_term)))

        if platform:
            query = query.filter(Skill.platform_targets.contains([platform]))

        if tag:
            query = query.filter(Skill.tags.contains([tag]))

        if author_id:
            query = query.filter(Skill.author_id == author_id)

        total = query.count()
        skills = query.order_by(Skill.updated_at.desc()).offset(skip).limit(limit).all()
        return skills, total

    def update_skill(
        self,
        skill_id: int,
        author_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None,
        content: Optional[str] = None,
        platform_targets: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Skill:
        skill = self.get_skill(skill_id)
        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

        if skill.author_id != author_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this skill")

        changes = {}
        if name is not None:
            changes["name"] = {"old": skill.name, "new": name}
            skill.name = name
        if description is not None:
            changes["description"] = {"old": skill.description, "new": description}
            skill.description = description
        if version is not None:
            changes["version"] = {"old": skill.version, "new": version}
            skill.version = version
        if content is not None:
            changes["content"] = {"old": skill.content[:100], "new": content[:100]}
            skill.content = content
        if platform_targets is not None:
            changes["platform_targets"] = {"old": skill.platform_targets, "new": platform_targets}
            skill.platform_targets = platform_targets
        if tags is not None:
            changes["tags"] = {"old": skill.tags, "new": tags}
            skill.tags = tags

        skill.updated_at = datetime.now(timezone.utc)
        self._log_audit(author_id, "update", "skill", str(skill_id), changes)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def delete_skill(self, skill_id: int, author_id: int) -> None:
        skill = self.get_skill(skill_id)
        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

        if skill.author_id != author_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this skill")

        self._log_audit(author_id, "delete", "skill", str(skill_id), {"name": skill.name, "slug": skill.slug})
        self.db.delete(skill)
        self.db.commit()

    def validate_skill(self, content: str, platform_targets: List[str]) -> List[dict]:
        errors = []
        lines = content.split("\n")

        required_sections = ["SKILL.md", "version:", "name:"]
        for section in required_sections:
            if not any(section in line for line in lines):
                errors.append({"type": "missing_section", "message": f"Missing required section: {section}"})

        valid_platforms = {"iOS", "macOS", "visionOS", "watchOS", "tvOS", "linux", "windows"}
        for platform in platform_targets:
            if platform not in valid_platforms:
                errors.append({"type": "invalid_platform", "message": f"Unknown platform target: {platform}"})

        for i, line in enumerate(lines, 1):
            if "iOS 26" in line and "iOS 26" not in line:
                pass

        return errors

    def search_skills(self, query: str, limit: int = 10) -> List[Skill]:
        search_term = f"%{query}%"
        return (
            self.db.query(Skill)
            .filter(or_(Skill.name.ilike(search_term), Skill.content.ilike(search_term)))
            .limit(limit)
            .all()
        )

    def export_skill(self, skill_id: int, format: str = "markdown") -> str:
        skill = self.get_skill(skill_id)
        if not skill:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

        if format == "markdown":
            return self._export_markdown(skill)
        elif format == "json":
            import json
            return json.dumps(self._skill_to_dict(skill), indent=2)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported format")

    def _export_markdown(self, skill: Skill) -> str:
        lines = [
            f"# {skill.name}",
            f"**Version:** {skill.version}",
            f"**Platforms:** {', '.join(skill.platform_targets) if skill.platform_targets else 'Any'}",
            f"**Tags:** {', '.join(skill.tags) if skill.tags else 'None'}",
            "",
            "## Description",
            skill.description or "No description provided.",
            "",
            "## Content",
            skill.content,
        ]
        return "\n".join(lines)

    def _skill_to_dict(self, skill: Skill) -> dict:
        return {
            "id": skill.id,
            "name": skill.name,
            "slug": skill.slug,
            "description": skill.description,
            "version": skill.version,
            "content": skill.content,
            "platform_targets": skill.platform_targets,
            "tags": skill.tags,
            "author_id": skill.author_id,
            "created_at": skill.created_at.isoformat() if skill.created_at else None,
            "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
        }

    def _log_audit(self, user_id: int, action: str, resource_type: str, resource_id: str, details: dict) -> None:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
        self.db.add(audit)


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, email: str, password: str, full_name: Optional[str] = None) -> User:
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            roles=["user"],
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_oidc_sub(self, sub: str) -> Optional[User]:
        return self.db.query(User).filter(User.oidc_sub == sub).first()

    def update_user_oidc(self, user_id: int, oidc_sub: str) -> User:
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.oidc_sub = oidc_sub
        self.db.commit()
        self.db.refresh(user)
        return user

    def verify_password(self, user: User, password: str) -> bool:
        from app.core.security import verify_password
        return verify_password(password, user.hashed_password)