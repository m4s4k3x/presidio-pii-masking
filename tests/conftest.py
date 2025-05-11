"""Common fixtures and utilities for tests."""

import os
import tempfile
from pathlib import Path

import pytest

from presidio_pii_masking import PIIMasker
from presidio_pii_masking.config import MaskingConfig


@pytest.fixture
def sample_text():
    """サンプルテキストを返すフィクスチャ."""
    return """山田太郎さんの連絡先情報：
電話番号：090-1234-5678
メールアドレス：taro.yamada@example.com
自宅住所：東京都千代田区霞が関1-1-1
生年月日：1990年4月1日
"""


@pytest.fixture
def temp_text_file(sample_text):
    """テキストファイルを作成して一時ファイルパスを返すフィクスチャ."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(sample_text)
        tmp_path = tmp.name

    yield tmp_path

    # テスト後にファイルを削除
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def temp_output_file():
    """出力用の一時ファイルパスを提供するフィクスチャ."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name

    yield tmp_path

    # テスト後にファイルを削除
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def temp_config_file():
    """テスト用の設定ファイルを作成するフィクスチャ."""
    config_content = """
language: ja
model_name: ja_core_news_trf
score_threshold: 0.6

entity_types:
  - PERSON
  - PHONE_NUMBER
  - EMAIL_ADDRESS

operators:
  PERSON:
    operator: replace
    params:
      new_value: "[個人名]"
  PHONE_NUMBER:
    operator: mask
    params:
      masking_char: "*"
      chars_to_mask: 8
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(config_content)
        tmp_path = tmp.name

    yield tmp_path

    # テスト後にファイルを削除
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def default_masker():
    """デフォルト設定のPIIMaskerインスタンスを返すフィクスチャ."""
    return PIIMasker()


@pytest.fixture
def custom_masker():
    """カスタム設定のPIIMaskerインスタンスを返すフィクスチャ."""
    return PIIMasker(language="ja", model_name="ja_core_news_trf", score_threshold=0.7)


@pytest.fixture
def config_from_file(temp_config_file):
    """設定ファイルから読み込んだMaskingConfigを返すフィクスチャ."""
    return MaskingConfig.from_file(temp_config_file)


def pytest_configure(config):
    """pytestの設定（オプションの追加など）."""
    # カスタムマーカーの登録（必要に応じて）
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
