"""Configuration settings for SkillBridge AI backend."""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

DATABASE_DIR = os.path.join(PROJECT_ROOT, "database")
os.makedirs(DATABASE_DIR, exist_ok=True)
DEFAULT_DATABASE_PATH = os.path.join(DATABASE_DIR, "skillbridge.db")


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "skillbridge-dev-secret-key-change-in-prod-12345")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "skillbridge-dev-jwt-secret-change-in-prod-12345")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24"))
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE_PATH}")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
    SKILL_PROFICIENCY_WEIGHT = float(os.environ.get("SKILL_PROFICIENCY_WEIGHT", "0.60"))
    SKILL_EVIDENCE_WEIGHT = float(os.environ.get("SKILL_EVIDENCE_WEIGHT", "0.40"))
    SKILL_EVIDENCE_TYPE_WEIGHTS = {
        "PROJECT": 25, "CERTIFICATION": 20, "EXPERIENCE": 30,
        "INTERNSHIP": 30, "COURSEWORK": 10, "ASSESSMENT": 10, "OTHER": 5,
    }
    SKILL_EVIDENCE_VERIFIED_MULTIPLIER = float(os.environ.get("SKILL_EVIDENCE_VERIFIED_MULTIPLIER", "1.2"))
    SKILL_GAP_MINOR_MAX = 10
    SKILL_GAP_MODERATE_MAX = 25
    ROLE_DEFAULT_REQUIRED_PROFICIENCY = 70
    LOCAL_AI_BASE_URL = os.environ.get("LOCAL_AI_BASE_URL", "http://127.0.0.1:11434")
    LOCAL_AI_MODEL = os.environ.get("LOCAL_AI_MODEL", "qwen2.5:1.5b-instruct-q5_0")
    LOCAL_AI_TIMEOUT_SECONDS = float(os.environ.get("LOCAL_AI_TIMEOUT_SECONDS", "60"))
    LOCAL_AI_MAX_INPUT_CHARS = int(os.environ.get("LOCAL_AI_MAX_INPUT_CHARS", "12000"))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    ENV = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-key"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = "production"


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
