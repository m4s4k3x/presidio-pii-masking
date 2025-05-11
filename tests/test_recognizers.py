"""Tests for custom recognizers."""

import pytest
from presidio_analyzer import RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider

from presidio_pii_masking.custom_recognizers import (
    EmailRecognizer, JapanesePersonRecognizer, JapanesePhoneNumberRecognizer,
    register_custom_recognizers)


def get_nlp_engine():
    """Get NLP engine for testing."""
    nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "ja", "model_name": "ja_core_news_trf"}],
    }
    provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
    return provider.create_engine()


def test_register_custom_recognizers():
    """Test custom recognizers registration."""
    registry = RecognizerRegistry()
    register_custom_recognizers(registry)

    recognizer_names = [r.name for r in registry.recognizers]

    # カスタム認識器が登録されていることを確認
    assert any("PhoneNumber" in name for name in recognizer_names)
    assert any("Email" in name for name in recognizer_names)
    assert any("Person" in name for name in recognizer_names)


def test_japanese_phone_number_recognizer():
    """Test Japanese phone number recognizer."""
    recognizer = JapanesePhoneNumberRecognizer()

    # 基本的な携帯電話番号
    text = "私の電話番号は090-1234-5678です。"
    results = recognizer.analyze(text, ["PHONE_NUMBER"], None)
    assert len(results) == 1
    assert results[0].entity_type == "PHONE_NUMBER"

    # 固定電話番号
    text = "会社の電話は03-1234-5678です。"
    results = recognizer.analyze(text, ["PHONE_NUMBER"], None)
    assert len(results) == 1
    assert results[0].entity_type == "PHONE_NUMBER"

    # スペース区切りの電話番号
    text = "連絡先は090 1234 5678です。"
    results = recognizer.analyze(text, ["PHONE_NUMBER"], None)
    assert len(results) == 1
    assert results[0].entity_type == "PHONE_NUMBER"

    # ハイフンなしの電話番号
    text = "電話は09012345678です。"
    results = recognizer.analyze(text, ["PHONE_NUMBER"], None)
    assert len(results) == 1
    assert results[0].entity_type == "PHONE_NUMBER"

    # 電話番号でないテキスト
    text = "これは電話番号ではありません。"
    results = recognizer.analyze(text, ["PHONE_NUMBER"], None)
    assert len(results) == 0


def test_email_recognizer():
    """Test email address recognizer."""
    recognizer = EmailRecognizer()

    # 基本的なメールアドレス
    text = "私のメールはuser@example.comです。"
    results = recognizer.analyze(text, ["EMAIL_ADDRESS"], None)
    assert len(results) == 1
    assert results[0].entity_type == "EMAIL_ADDRESS"

    # 複雑なメールアドレス
    text = "問い合わせは.user.name+tag-123@sub.example-domain.co.jpまで。"
    results = recognizer.analyze(text, ["EMAIL_ADDRESS"], None)
    assert len(results) == 1
    assert results[0].entity_type == "EMAIL_ADDRESS"

    # 複数のメールアドレス
    text = "メールはuser1@example.comとuser2@example.orgです。"
    results = recognizer.analyze(text, ["EMAIL_ADDRESS"], None)
    assert len(results) == 2
    assert all(result.entity_type == "EMAIL_ADDRESS" for result in results)

    # メールアドレスでないテキスト
    text = "これはメールアドレスではありません。"
    results = recognizer.analyze(text, ["EMAIL_ADDRESS"], None)
    assert len(results) == 0


def test_japanese_person_recognizer():
    """Test Japanese person name recognizer."""
    # NLPエンジンが必要なのでスキップ設定
    nlp_engine = get_nlp_engine()
    if not nlp_engine:
        pytest.skip("NLP engine not available")

    # テキストの解析
    text = "山田太郎と佐藤花子が会議に参加します。"
    doc = nlp_engine.process_text(text, "ja")

    # SpaCyのNERタグを確認
    entities = doc.entities
    person_entities = [e for e in entities if e.label_ == "PERSON"]

    # 人名が検出されるか確認
    if not person_entities:
        pytest.skip("SpaCy NER did not detect person entities in the test text")

    # 認識器のテスト
    recognizer = JapanesePersonRecognizer()
    results = recognizer.analyze(text, ["PERSON"], nlp_engine.process_text(text, "ja"))

    # 結果の確認
    assert len(results) > 0
    for result in results:
        assert result.entity_type == "PERSON"


def test_japanese_person_name_pattern_matching():
    """Test Japanese person name pattern matching logic."""
    recognizer = JapanesePersonRecognizer()

    # パターンマッチングのロジックをテスト
    valid_names = ["山田太郎", "佐藤花子", "田中一郎", "鈴木次郎", "高橋三郎"]
    invalid_names = ["会社です", "電話番号", "メールアドレス", "あり", "なし"]

    for name in valid_names:
        assert recognizer._is_valid_person_name(name) is True

    for name in invalid_names:
        assert recognizer._is_valid_person_name(name) is False


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
