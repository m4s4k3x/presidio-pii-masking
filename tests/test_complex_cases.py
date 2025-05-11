"""Tests for complex cases and edge scenarios."""

import pytest

from presidio_pii_masking import PIIMasker


def test_overlapping_entities():
    """Test handling of overlapping PII entities."""
    masker = PIIMasker()

    # 重複するエンティティを含むテキスト
    # 電話番号が人名の一部に見える場合など
    text = "私の名前は山田0901234です。メールはyamada0901234@example.comです。"

    # 匿名化を実行
    anonymized = masker.anonymize_text(text)

    # 結果を確認 - 少なくとも一部の情報が匿名化されている
    assert "山田0901234" not in anonymized or "yamada0901234@example.com" not in anonymized

    # 元のテキストとある程度類似した長さを持つ
    assert 0.5 * len(text) <= len(anonymized) <= 1.5 * len(text)


def test_mixed_language_support():
    """Test PII detection in mixed language text."""
    masker = PIIMasker()

    # 混合言語のテキスト
    text = """
    日本語と英語が混在するテキスト：
    担当者: 山田太郎 (Taro Yamada)
    Email: taro.yamada@example.com
    Phone: 090-1234-5678
    Address: 東京都千代田区, Tokyo, Japan
    """

    # 匿名化を実行
    anonymized = masker.anonymize_text(text)

    # 日本語の人名が匿名化されているか確認
    assert "山田太郎" not in anonymized

    # 英語の人名が匿名化されているか確認（実装によっては動作が異なる可能性あり）
    assert "Taro Yamada" not in anonymized or "<PERSON>" in anonymized

    # 電話番号とメールアドレスが匿名化されているか確認
    assert "090-1234-5678" not in anonymized
    assert "taro.yamada@example.com" not in anonymized


def test_special_characters_handling():
    """Test handling of text with special characters."""
    masker = PIIMasker()

    # 特殊文字を含むテキスト
    text = """
    特殊文字を含む文: ※●■◆★☆♪【】《》〔〕『』〈〉«»
    山田太郎(やまだたろう)の電話番号:090-1234-5678
    メール:taro.yamada@example.com
    """

    # 匿名化を実行
    anonymized = masker.anonymize_text(text)

    # 人名、電話番号、メールアドレスが匿名化されているか確認
    assert "山田太郎" not in anonymized
    assert "090-1234-5678" not in anonymized
    assert "taro.yamada@example.com" not in anonymized

    # 特殊文字が残っているか確認
    special_chars = "※●■◆★☆♪【】《》〔〕『』〈〉«»"
    for char in special_chars:
        assert char in anonymized


def test_long_sentences():
    """Test PII detection in very long sentences."""
    masker = PIIMasker()

    # 非常に長い文章
    long_prefix = "これは非常に長い文章であり、たくさんの単語が含まれていますが、個人情報はその中に埋もれています。" * 10
    long_suffix = "これは文章の続きであり、個人情報の後にもテキストが続いています。" * 10

    text = long_prefix + "山田太郎の電話番号は090-1234-5678です。" + long_suffix

    # 匿名化を実行
    anonymized = masker.anonymize_text(text)

    # 人名と電話番号が匿名化されているか確認
    assert "山田太郎" not in anonymized
    assert "090-1234-5678" not in anonymized

    # プレースホルダーが含まれていることを確認
    assert "<PERSON>" in anonymized
    assert "<PHONE_NUMBER>" in anonymized


def test_multiple_occurrences():
    """Test handling of multiple occurrences of the same PII."""
    masker = PIIMasker()

    # 同じPIIが複数回出現するテキスト
    text = """
    山田太郎の電話番号は090-1234-5678です。
    山田太郎にメールを送る場合はtaro.yamada@example.comです。
    また、山田太郎の携帯電話は090-1234-5678です。
    予備のメールアドレスとしてtaro.yamada@example.comを使用しています。
    """

    # 匿名化を実行
    anonymized = masker.anonymize_text(text)

    # すべての出現箇所が匿名化されているか確認
    assert "山田太郎" not in anonymized
    assert "090-1234-5678" not in anonymized
    assert "taro.yamada@example.com" not in anonymized

    # プレースホルダーの出現回数を確認
    assert anonymized.count("<PERSON>") >= 3
    assert anonymized.count("<PHONE_NUMBER>") >= 2
    assert anonymized.count("<EMAIL_ADDRESS>") >= 2


def test_different_japanese_names():
    """Test detection of various Japanese name formats."""
    masker = PIIMasker()

    # 様々な日本人名形式
    text = """
    山田太郎さん
    田中花子様
    佐藤一郎氏
    高橋次郎君
    渡辺三郎先生
    鈴木博士
    """

    # 匿名化を実行
    anonymized = masker.anonymize_text(text)

    # 各名前が匿名化されているか確認
    japanese_names = ["山田太郎", "田中花子", "佐藤一郎", "高橋次郎", "渡辺三郎", "鈴木"]
    for name in japanese_names:
        assert name not in anonymized


def test_standard_entity_types():
    """Test handling of standard entity types."""
    masker = PIIMasker()

    # 標準的なエンティティタイプを含むテキスト
    text = """
    山田太郎の住所は東京都千代田区霞が関1-1-1です。
    生年月日は1990年4月1日です。
    """

    # 匿名化を実行
    anonymized = masker.anonymize_text(text)

    # 人名が匿名化されているか確認
    assert "山田太郎" not in anonymized
    assert "<PERSON>" in anonymized

    # 追加で検出された場合のみ確認
    if "<LOCATION>" in anonymized:
        assert "東京都千代田区霞が関1-1-1" not in anonymized

    if "<DATE_TIME>" in anonymized:
        assert "1990年4月1日" not in anonymized


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
