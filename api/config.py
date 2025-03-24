import os
from datetime import timedelta


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    DATABASE_CONFIG = {
        "dbname": os.environ.get("DB_NAME"),
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "host": os.environ.get("DB_HOST"),
        "port": os.environ.get("DB_PORT"),
    }


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    DATABASE_CONFIG = {
        "dbname": os.environ.get("DB_NAME"),
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "host": os.environ.get("DB_HOST"),
        "port": os.environ.get("DB_PORT"),
    }


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    DATABASE_CONFIG = {
        "dbname": os.environ.get("DB_NAME"),
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "host": os.environ.get("DB_HOST"),
        "port": os.environ.get("DB_PORT"),
    }


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DEBUG = True
    DATABASE_CONFIG = {
        "dbname": "test_db",
        "user": "postgres",
        "password": "postgres",
        "host": "localhost",
        "port": 5432,
    }
