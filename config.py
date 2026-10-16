"""CropFlow configuration module.

Supports development, testing, and production environments with
configurable SQLite paths and agricultural default parameters.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "cropflow-dev-secret-key-default-2026")
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "cropflow.db"))
    DEBUG = False
    TESTING = False

    # Default agricultural economics parameters
    DEFAULT_ENERGY_RATE = float(os.getenv("DEFAULT_ENERGY_RATE", "0.04"))  # $ / m3
    DEFAULT_LABOR_RATE = float(os.getenv("DEFAULT_LABOR_RATE", "12.50"))   # $ / hour
    DEFAULT_PUMP_CAPACITY = float(os.getenv("DEFAULT_PUMP_CAPACITY", "25.0"))  # m3 / hour


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    DATABASE_PATH = str(BASE_DIR / "test_cropflow.db")


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    # Ensure a custom secret key is required in production
    SECRET_KEY = os.getenv("SECRET_KEY", "production-secret-must-be-set")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
