"""Tests for PII masking functionality."""

import pytest

from presidio_pii_masking import PIIMasker


def test_detect_pii():
    """Test PII detection."""
    masker = PIIMasker()

    # テスト用のテキスト
    text = "山田太郎の電話番号は090-1234-5678です。メールはtaro.yamada@example.comです。"

    # PIIを検出
    results = masker.detect_pii(text)

    # 少なくとも3つの個人情報（名前、電話番号、メール）が検出されることを確認
    assert len(results) >= 3

    # 検出されたエンティティタイプを確認
    entity_types = [result["entity_type"] for result in results]
    assert "PERSON" in entity_types
    assert "PHONE_NUMBER" in entity_types
    assert "EMAIL_ADDRESS" in entity_types


def test_anonymize_text_default():
    """Test text anonymization with default settings."""
    masker = PIIMasker()

    # テスト用のテキスト
    text = "山田太郎の電話番号は090-1234-5678です。メールはtaro.yamada@example.comです。"

    # デフォルト設定で匿名化
    anonymized = masker.anonymize_text(text)

    # 個人情報が置換されていることを確認
    assert "山田太郎" not in anonymized
    assert "090-1234-5678" not in anonymized
    assert "taro.yamada@example.com" not in anonymized

    # エンティティタイプのプレースホルダーが含まれていることを確認
    assert "<PERSON>" in anonymized
    assert "<PHONE_NUMBER>" in anonymized
    assert "<EMAIL_ADDRESS>" in anonymized


def test_anonymize_text_custom_operators():
    """Test text anonymization with custom operators."""
    masker = PIIMasker()

    # テスト用のテキスト
    text = "山田太郎の電話番号は090-1234-5678です。"

    # カスタムオペレーターで匿名化
    anonymized = masker.anonymize_text(
        text,
        operators={
            "PERSON": {"operator": "replace", "params": {"new_value": "名無しさん"}},
            "PHONE_NUMBER": {
                "operator": "mask",
                "params": {"masking_char": "*", "chars_to_mask": 8, "from_end": False},
            },
        },
    )

    # カスタム置換が適用されていることを確認
    assert "名無しさん" in anonymized
    assert "<PERSON>" not in anonymized

    # 電話番号が部分的にマスクされていることを確認
    assert "090" not in anonymized
    assert "********5678" in anonymized or "*******-5678" in anonymized


def test_anonymize_specific_entity_types():
    """Test anonymization of specific entity types only."""
    masker = PIIMasker()

    # テスト用のテキスト
    text = "山田太郎の電話番号は090-1234-5678です。メールはtaro.yamada@example.comです。"

    # 電話番号のみを匿名化
    anonymized = masker.anonymize_text(text, entity_types=["PHONE_NUMBER"])

    # 電話番号は匿名化されているが名前とメールアドレスはそのままであることを確認
    assert "山田太郎" in anonymized
    assert "090-1234-5678" not in anonymized
    assert "<PHONE_NUMBER>" in anonymized
    assert "taro.yamada@example.com" in anonymized


# 追加テスト：初期化パラメータのテスト
def test_init_parameters():
    """Test initialization with different parameters."""
    # デフォルトパラメータ
    masker_default = PIIMasker()
    assert masker_default.language == "ja"
    assert masker_default.model_name == "ja_core_news_trf"
    assert masker_default.score_threshold == 0.5

    # カスタムパラメータ
    masker_custom = PIIMasker(language="en", model_name="en_core_web_sm", score_threshold=0.7)
    assert masker_custom.language == "en"
    assert masker_custom.model_name == "en_core_web_sm"
    assert masker_custom.score_threshold == 0.7


# 追加テスト：エッジケース
def test_edge_cases():
    """Test edge cases like empty input."""
    masker = PIIMasker()

    # 空のテキスト
    empty_text = ""
    assert masker.anonymize_text(empty_text) == empty_text
    assert masker.detect_pii(empty_text) == []

    # PIIを含まないテキスト
    no_pii_text = "これはPIIを含まないテキストです。"
    assert masker.anonymize_text(no_pii_text) == no_pii_text

    # 特殊文字を含むテキスト
    special_chars_text = "!@#$%^&*()_+{}|:\"<>?[]\\;',./~`"
    assert masker.anonymize_text(special_chars_text) == special_chars_text


# 追加テスト：異なるエンティティタイプの検出
def test_different_entity_types():
    """Test detection of various entity types."""
    masker = PIIMasker()

    # 複数のエンティティタイプを含むテキスト
    text = """
    山田太郎（連絡先：090-1234-5678、taro.yamada@example.com）
    住所：東京都千代田区霞が関1-1-1
    生年月日：1990年4月1日
    クレジットカード：4111-1111-1111-1111
    """

    results = masker.detect_pii(text)
    entity_types = [result["entity_type"] for result in results]

    # 基本的なエンティティタイプの検出を確認
    assert "PERSON" in entity_types
    assert "PHONE_NUMBER" in entity_types
    assert "EMAIL_ADDRESS" in entity_types

    # その他のエンティティタイプも検出されることを確認（環境によって異なる可能性あり）
    potential_entities = ["ADDRESS", "DATE_TIME", "CREDIT_CARD", "LOCATION"]
    assert any(entity in entity_types for entity in potential_entities)


# 追加テスト：複数の置換オペレーターのテスト
def test_multiple_replace_operators():
    """Test multiple replacement operators."""
    masker = PIIMasker()

    text = "山田太郎と佐藤花子の電話番号は090-1234-5678と080-8765-4321です。"

    # 複数のエンティティに異なる置換オペレーターを適用
    anonymized = masker.anonymize_text(
        text,
        operators={
            "PERSON": {"operator": "replace", "params": {"new_value": "[人物]"}},
            "PHONE_NUMBER": {"operator": "replace", "params": {"new_value": "[電話番号]"}},
        },
    )

    # 名前と電話番号が置換されていることを確認
    assert "山田太郎" not in anonymized
    assert "佐藤花子" not in anonymized
    assert "090-1234-5678" not in anonymized
    assert "080-8765-4321" not in anonymized

    # 置換値が適用されていることを確認
    assert "[人物]" in anonymized
    assert "[電話番号]" in anonymized


# 追加テスト：マスク操作のパラメータテスト
def test_mask_operator_parameters():
    """Test different parameters for the mask operator."""
    masker = PIIMasker()

    text = "電話番号：090-1234-5678"

    # 前からマスク
    anonymized1 = masker.anonymize_text(
        text,
        operators={
            "PHONE_NUMBER": {
                "operator": "mask",
                "params": {"masking_char": "*", "chars_to_mask": 8, "from_end": False},
            },
        },
    )
    assert "********5678" in anonymized1 or "*******-5678" in anonymized1

    # 後ろからマスク
    anonymized2 = masker.anonymize_text(
        text,
        operators={
            "PHONE_NUMBER": {
                "operator": "mask",
                "params": {"masking_char": "*", "chars_to_mask": 8, "from_end": True},
            },
        },
    )
    assert "090-1234****" in anonymized2 or "090-1*******" in anonymized2

    # 異なるマスク文字
    anonymized3 = masker.anonymize_text(
        text,
        operators={
            "PHONE_NUMBER": {
                "operator": "mask",
                "params": {"masking_char": "X", "chars_to_mask": 8, "from_end": False},
            },
        },
    )
    assert "XXXXXXXX5678" in anonymized3 or "XXXXXXX-5678" in anonymized3


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
