from datetime import datetime, timezone
from typing import Optional, List, Tuple
import re
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, select
from fastapi import HTTPException, status

from app.models.skill import Skill, User, AuditLog
from app.core.security import get_password_hash


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


class SkillService:
    def __init__(self, db: Session):
        self.db = db

    def create_skill(
        self,
        name: str,
        content: str,
        author_id: int,
        description: Optional[str] = None,
        version: str = "1.0.0",
        platform_targets: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        slug: Optional[str] = None,
    ) -> Skill:
        # If slug is explicitly provided, check for exact conflict
        if slug is not None:
            existing = self.db.query(Skill).filter(Skill.slug == slug).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill slug already exists")
        else:
            # Auto-generate slug from name and ensure uniqueness
            slug = slugify(name)
            original_slug = slug
            counter = 1
            while self.db.query(Skill).filter(Skill.slug == slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1

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

        # Check required sections with line numbers
        required_sections = {
            "SKILL.md": "Missing required section: SKILL.md (skill definition header)",
            "version:": "Missing required field: version (semver format required)",
            "name:": "Missing required field: name (skill identifier)",
        }
        for section, message in required_sections.items():
            found = False
            for i, line in enumerate(lines, 1):
                if section in line:
                    found = True
                    break
            if not found:
                errors.append({"type": "missing_section", "message": message, "line": None})

        # Validate version format if present
        for i, line in enumerate(lines, 1):
            if "version:" in line:
                # Extract version value after "version:"
                parts = line.split("version:", 1)
                if len(parts) > 1:
                    version_str = parts[1].strip()
                    # Remove quotes if present
                    version_str = version_str.strip('"\'')
                    if not self._is_valid_semver(version_str):
                        errors.append({
                            "type": "invalid_version",
                            "message": f"Invalid version format: '{version_str}'. Expected semver (e.g., 1.0.0)",
                            "line": i
                        })
                break

        # Validate platform targets
        valid_platforms = {"iOS", "macOS", "visionOS", "watchOS", "tvOS", "linux", "windows"}
        for platform in platform_targets:
            if platform not in valid_platforms:
                errors.append({
                    "type": "invalid_platform",
                    "message": f"Unknown platform target: '{platform}'. Valid: {', '.join(sorted(valid_platforms))}",
                    "line": None
                })

        # Check for deprecated API usage and platform-specific issues
        self._check_deprecated_apis(lines, errors)
        self._check_platform_availability(lines, platform_targets, errors)

        return errors

    def _is_valid_semver(self, version: str) -> bool:
        import re
        return bool(re.match(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$", version))

    def _check_deprecated_apis(self, lines: List[str], errors: List[dict]) -> None:
        """Check for known deprecated Swift/SwiftUI APIs."""
        deprecated_patterns = [
            (r"\.onAppear\s*\(", "Consider using .task instead of .onAppear for async work"),
            (r"UIApplication\.shared", "UIApplication.shared is deprecated; use UIApplication.shared.connectedScenes"),
            (r"UIScreen\.main", "UIScreen.main is deprecated; use windowScene.screen"),
            (r"@UIApplicationMain", "@UIApplicationMain is deprecated; use @main"),
        ]
        for i, line in enumerate(lines, 1):
            for pattern, message in deprecated_patterns:
                import re
                if re.search(pattern, line):
                    errors.append({
                        "type": "deprecated_api",
                        "message": message,
                        "line": i
                    })

    def _check_platform_availability(self, lines: List[str], platform_targets: List[str], errors: List[dict]) -> None:
        """Check #available conditions against minimum deployment targets."""
        if not platform_targets:
            return

        # Minimum version map for platforms
        min_versions = {
            "iOS": (26, 0),
            "macOS": (15, 0),
            "visionOS": (2, 0),
            "watchOS": (11, 0),
            "tvOS": (18, 0),
        }

        import re
        for i, line in enumerate(lines, 1):
            # Check #available conditions
            available_match = re.search(r'#available\s*\(([^)]+)\)', line)
            if available_match:
                conditions = available_match.group(1)
                for platform, min_ver in min_versions.items():
                    if platform in platform_targets:
                        # Check if platform appears in #available with version >= minimum
                        platform_pattern = rf'{platform}\s+(\d+(?:\.\d+)*)'
                        match = re.search(platform_pattern, conditions)
                        if match:
                            try:
                                ver_parts = tuple(map(int, match.group(1).split('.')))
                                if ver_parts >= min_ver:
                                    errors.append({
                                        "type": "unnecessary_available_check",
                                        "message": f"#available check for {platform} {match.group(1)} is unnecessary (minimum target is {min_ver[0]}.{min_ver[1]})",
                                        "line": i
                                    })
                            except ValueError:
                                pass

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