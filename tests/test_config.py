"""Tests for configuration functionality."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from presidio_pii_masking.config import MaskingConfig, OperatorConfig


def test_config_defaults():
    """Test default configuration values."""
    config = MaskingConfig()

    # デフォルト値の確認
    assert config.language == "ja"
    assert config.model_name == "ja_core_news_trf"
    assert config.score_threshold == 0.5
    assert config.entity_types is None
    assert isinstance(config.operators, dict)
    assert isinstance(config.default_operator, OperatorConfig)
    assert config.default_operator.operator == "replace"


def test_operator_config():
    """Test OperatorConfig model."""
    # デフォルト値
    op_config = OperatorConfig()
    assert op_config.operator == "replace"
    assert isinstance(op_config.params, dict)
    assert len(op_config.params) == 0

    # カスタム値
    op_config = OperatorConfig(operator="mask", params={"masking_char": "*", "chars_to_mask": 4})
    assert op_config.operator == "mask"
    assert op_config.params == {"masking_char": "*", "chars_to_mask": 4}


def test_config_from_file():
    """Test loading configuration from a file."""
    # 一時設定ファイルを作成
    config_data = {
        "language": "en",
        "model_name": "en_core_web_sm",
        "score_threshold": 0.7,
        "entity_types": ["PERSON", "EMAIL_ADDRESS"],
        "operators": {
            "PERSON": {"operator": "replace", "params": {"new_value": "[PERSON-REDACTED]"}},
            "EMAIL_ADDRESS": {
                "operator": "mask",
                "params": {"masking_char": "#", "chars_to_mask": 10},
            },
        },
        "default_operator": {"operator": "hash", "params": {}},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(config_data, tmp)
        tmp_path = tmp.name

    try:
        # 設定ファイルから読み込み
        config = MaskingConfig.from_file(tmp_path)

        # 値の確認
        assert config.language == "en"
        assert config.model_name == "en_core_web_sm"
        assert config.score_threshold == 0.7
        assert config.entity_types == ["PERSON", "EMAIL_ADDRESS"]

        # オペレーターの確認
        assert "PERSON" in config.operators
        assert config.operators["PERSON"].operator == "replace"
        assert config.operators["PERSON"].params == {"new_value": "[PERSON-REDACTED]"}

        assert "EMAIL_ADDRESS" in config.operators
        assert config.operators["EMAIL_ADDRESS"].operator == "mask"
        assert config.operators["EMAIL_ADDRESS"].params == {
            "masking_char": "#",
            "chars_to_mask": 10,
        }

        # デフォルトオペレーターの確認
        assert config.default_operator.operator == "hash"
    finally:
        # 一時ファイルの削除
        os.unlink(tmp_path)


def test_config_from_env():
    """Test loading configuration from environment variables."""
    # 環境変数の保存
    old_env = {}
    for key in ["PII_LANGUAGE", "PII_MODEL_NAME", "PII_SCORE_THRESHOLD", "PII_ENTITY_TYPES"]:
        old_env[key] = os.environ.get(key)

    try:
        # 環境変数の設定
        os.environ["PII_LANGUAGE"] = "en"
        os.environ["PII_MODEL_NAME"] = "en_core_web_sm"
        os.environ["PII_SCORE_THRESHOLD"] = "0.75"
        os.environ["PII_ENTITY_TYPES"] = "PERSON,EMAIL_ADDRESS,PHONE_NUMBER"

        # 環境変数から設定を読み込み
        config = MaskingConfig.from_env()

        # 値の確認
        assert config.language == "en"
        assert config.model_name == "en_core_web_sm"
        assert config.score_threshold == 0.75
        assert config.entity_types == ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]
    finally:
        # 環境変数の復元
        for key, value in old_env.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value


def test_real_config_file():
    """Test loading the actual masking_config.yaml from the project."""
    # プロジェクトルートからの相対パスで設定ファイルを探す
    config_path = Path(__file__).parent.parent / "masking_config.yaml"

    if config_path.exists():
        config = MaskingConfig.from_file(config_path)

        # masking_config.yamlの実在する値を確認
        assert hasattr(config, "language")
        assert hasattr(config, "model_name")
        assert hasattr(config, "score_threshold")

        # オペレーターの確認
        if config.operators and "PERSON" in config.operators:
            assert hasattr(config.operators["PERSON"], "operator")
            assert hasattr(config.operators["PERSON"], "params")
    else:
        pytest.skip("masking_config.yaml not found in the project root")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
