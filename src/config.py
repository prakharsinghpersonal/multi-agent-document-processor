"""
PharmaVigil Pipeline Configuration
===================================
Centralized configuration for the document extraction and classification pipeline.
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    postgres_host: str = os.getenv("PG_HOST", "localhost")
    postgres_port: int = int(os.getenv("PG_PORT", "5432"))
    postgres_db: str = os.getenv("PG_DATABASE", "pharmavigil")
    postgres_user: str = os.getenv("PG_USER", "admin")
    postgres_password: str = os.getenv("PG_PASSWORD", "")
    astra_token: str = os.getenv("ASTRA_DB_TOKEN", "")
    astra_endpoint: str = os.getenv("ASTRA_DB_ENDPOINT", "")


@dataclass
class ModelConfig:
    """Transformer model configuration."""
    model_name: str = "distilbert-base-uncased"
    max_seq_length: int = 512
    batch_size: int = 32
    learning_rate: float = 2e-5
    num_epochs: int = 5
    focal_loss_gamma: float = 2.0
    focal_loss_alpha: float = 0.25
    embedding_dim: int = 768
    num_classes: int = 5


@dataclass
class PipelineConfig:
    """Main pipeline configuration."""
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    data_dir: str = os.getenv("DATA_DIR", "data/")
    output_dir: str = os.getenv("OUTPUT_DIR", "outputs/")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    batch_processing_size: int = 500
    max_workers: int = 4


def get_config() -> PipelineConfig:
    """Return the pipeline configuration."""
    return PipelineConfig()
