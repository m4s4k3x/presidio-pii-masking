"""Configuration management for PII masking."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field


class OperatorConfig(BaseModel):
    """Anonymization operator configuration."""

    operator: str = "replace"
    params: Dict[str, Any] = Field(default_factory=dict)


class MaskingConfig(BaseModel):
    """Configuration for PII masking."""

    # NLP engine configuration
    language: str = "ja"
    model_name: str = "ja_core_news_trf"
    score_threshold: float = 0.5

    # Entity types to detect/anonymize (None for all supported types)
    entity_types: Optional[List[str]] = None

    # Operator configurations per entity type
    operators: Dict[str, OperatorConfig] = Field(default_factory=dict)

    # Default operator for entities without specific configuration
    default_operator: OperatorConfig = Field(
        default_factory=lambda: OperatorConfig(operator="replace")
    )

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "MaskingConfig":
        """Load configuration from a YAML file.

        Args:
            file_path: Path to the configuration file

        Returns:
            Loaded configuration object
        """
        with open(file_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        # Convert operators dict to OperatorConfig objects
        if "operators" in config_data:
            operators = {}
            for entity_type, op_config in config_data["operators"].items():
                operators[entity_type] = OperatorConfig(**op_config)
            config_data["operators"] = operators

        # Convert default_operator to OperatorConfig if present
        if "default_operator" in config_data:
            config_data["default_operator"] = OperatorConfig(**config_data["default_operator"])

        return cls(**config_data)

    @classmethod
    def from_env(cls) -> "MaskingConfig":
        """Load configuration from environment variables.

        Returns:
            Configuration object with values from environment variables
        """
        config = cls()

        # Basic settings
        if os.getenv("PII_LANGUAGE"):
            config.language = os.getenv("PII_LANGUAGE", "ja")

        if os.getenv("PII_MODEL_NAME"):
            config.model_name = os.getenv("PII_MODEL_NAME", "ja_core_news_trf")

        if os.getenv("PII_SCORE_THRESHOLD"):
            config.score_threshold = float(os.getenv("PII_SCORE_THRESHOLD", "0.5"))

        # Entity types
        if os.getenv("PII_ENTITY_TYPES"):
            config.entity_types = os.getenv("PII_ENTITY_TYPES", "").split(",")

        return config
