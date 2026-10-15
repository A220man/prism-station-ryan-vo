import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.skill import User, Skill


# Mock password hashing for tests to avoid bcrypt issues
def mock_get_password_hash(password: str) -> str:
    return f"mock_hash_{password}"


def mock_verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashed_password == f"mock_hash_{plain_password}"


@pytest.fixture(autouse=True)
def mock_password_hashing():
    with patch("app.core.security.get_password_hash", mock_get_password_hash):
        with patch("app.core.security.verify_password", mock_verify_password):
            with patch("app.services.skill_service.get_password_hash", mock_get_password_hash):
                with patch("app.api.auth.get_password_hash", mock_get_password_hash):
                    yield
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    hashed = mock_get_password_hash("testpass")
    user = User(
        email="test@example.com",
        hashed_password=hashed,
        full_name="Test User",
        roles=["user"],
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"sub": str(test_user.id), "email": test_user.email, "roles": test_user.roles})
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoints:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "prism-station"

    def test_db_health_check(self):
        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestAuthEndpoints:
    def test_register(self):
        response = client.post(
            "/api/auth/register",
            json={"email": "newuser@example.com", "password": "pass1234", "full_name": "New User"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"

    def test_register_duplicate_email(self, test_user):
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "pass1234"},
        )
        assert response.status_code == 409

    def test_login(self, test_user):
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "testpass"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, test_user):
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    def test_get_me(self, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_me_unauthorized(self):
        response = client.get("/api/auth/me")
        assert response.status_code == 401


class TestSkillEndpoints:
    def test_create_skill(self, auth_headers):
        response = client.post(
            "/api/skills",
            json={
                "name": "Test Skill",
                "slug": "test-skill",
                "description": "A test skill",
                "version": "1.0.0",
                "content": "# Test Skill\n\nThis is a test skill content.",
                "platform_targets": ["iOS", "macOS"],
                "tags": ["swiftui", "testing"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Skill"
        assert data["slug"] == "test-skill"

    def test_create_skill_duplicate_slug(self, auth_headers):
        client.post(
            "/api/skills",
            json={
                "name": "Test Skill",
                "slug": "test-skill",
                "version": "1.0.0",
                "content": "content",
            },
            headers=auth_headers,
        )
        response = client.post(
            "/api/skills",
            json={
                "name": "Test Skill 2",
                "slug": "test-skill",
                "version": "1.0.0",
                "content": "content",
            },
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_list_skills(self, auth_headers, test_user, db_session):
        skill = Skill(
            name="Test Skill",
            slug="test-skill",
            version="1.0.0",
            content="content",
            author_id=test_user.id,
        )
        db_session.add(skill)
        db_session.commit()

        response = client.get("/api/skills", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_get_skill(self, auth_headers, test_user, db_session):
        skill = Skill(
            name="Test Skill",
            slug="test-skill",
            version="1.0.0",
            content="content",
            author_id=test_user.id,
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)

        response = client.get(f"/api/skills/{skill.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Skill"

    def test_get_skill_not_found(self, auth_headers):
        response = client.get("/api/skills/999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_skill(self, auth_headers, test_user, db_session):
        skill = Skill(
            name="Test Skill",
            slug="test-skill",
            version="1.0.0",
            content="content",
            author_id=test_user.id,
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)

        response = client.patch(
            f"/api/skills/{skill.id}",
            json={"name": "Updated Skill", "version": "1.1.0"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Skill"
        assert data["version"] == "1.1.0"

    def test_update_skill_unauthorized(self, auth_headers, db_session):
        other_user = User(
            email="other@example.com",
            hashed_password=mock_get_password_hash("otherpass"),
            roles=["user"],
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        skill = Skill(
            name="Other Skill",
            slug="other-skill",
            version="1.0.0",
            content="content",
            author_id=other_user.id,
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)

        response = client.patch(
            f"/api/skills/{skill.id}",
            json={"name": "Hacked"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_delete_skill(self, auth_headers, test_user, db_session):
        skill = Skill(
            name="Test Skill",
            slug="test-skill",
            version="1.0.0",
            content="content",
            author_id=test_user.id,
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)

        response = client.delete(f"/api/skills/{skill.id}", headers=auth_headers)
        assert response.status_code == 204

        response = client.get(f"/api/skills/{skill.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_validate_skill(self, auth_headers):
        response = client.post(
            "/api/skills/validate",
            json={
                "content": "# Test Skill\n\nversion: 1.0.0\nname: Test",
                "platform_targets": ["iOS", "macOS"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "errors" in data

    def test_export_skill_markdown(self, auth_headers, test_user, db_session):
        skill = Skill(
            name="Test Skill",
            slug="test-skill",
            version="1.0.0",
            content="# Test Skill\n\nContent here.",
            description="A test skill",
            platform_targets=["iOS"],
            tags=["test"],
            author_id=test_user.id,
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)

        response = client.get(f"/api/skills/{skill.id}/export?format=markdown", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "markdown"
        assert "Test Skill" in data["content"]

    def test_export_skill_json(self, auth_headers, test_user, db_session):
        skill = Skill(
            name="Test Skill",
            slug="test-skill",
            version="1.0.0",
            content="content",
            author_id=test_user.id,
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)

        response = client.get(f"/api/skills/{skill.id}/export?format=json", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"
        assert "Test Skill" in data["content"]

    def test_search_skills(self, auth_headers, test_user, db_session):
        skill1 = Skill(name="SwiftUI Skill", slug="swiftui-skill", version="1.0.0", content="SwiftUI content", author_id=test_user.id)
        skill2 = Skill(name="UIKit Skill", slug="uikit-skill", version="1.0.0", content="UIKit content", author_id=test_user.id)
        db_session.add_all([skill1, skill2])
        db_session.commit()

        response = client.get("/api/skills/search/SwiftUI?limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "SwiftUI Skill"