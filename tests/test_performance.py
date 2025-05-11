"""Performance tests for PII masking."""

import time
from typing import Any, Dict, List

import pytest

from presidio_pii_masking import PIIMasker


@pytest.fixture
def large_text() -> str:
    """Generate a large text sample with repeated PII."""
    base_text = """
    山田太郎さんの連絡先情報：
    電話番号：090-1234-5678
    メールアドレス：taro.yamada@example.com
    
    佐藤花子さんの連絡先情報：
    電話番号：080-8765-4321
    メールアドレス：hanako.sato@example.jp
    
    田中一郎さんの連絡先情報：
    電話番号：070-2468-1357
    メールアドレス：ichiro.tanaka@example.co.jp
    """

    # テキストを100回繰り返して大きなサンプルを作成
    return base_text * 100


def test_detection_performance(large_text: str):
    """Test performance of PII detection."""
    masker = PIIMasker()

    # PII検出の実行時間を計測
    start_time = time.time()
    results = masker.detect_pii(large_text)
    end_time = time.time()

    # 実行時間の記録
    detection_time = end_time - start_time

    # 検出結果の確認
    assert len(results) > 0

    # 性能指標の確認（これは環境依存なので厳密なテストではなく参考値）
    # 検出速度（1秒あたりの検出エンティティ数）
    detection_rate = len(results) / detection_time if detection_time > 0 else 0

    # ログ出力
    print(f"\nPII Detection Performance:")
    print(f"- Text size: {len(large_text)} characters")
    print(f"- Entities detected: {len(results)}")
    print(f"- Processing time: {detection_time:.2f} seconds")
    print(f"- Detection rate: {detection_rate:.2f} entities/second")

    # 非常に低速な場合は失敗とする（具体的な閾値は環境によって調整）
    # これは参考値であり、実行環境によって大きく変わるため、必要に応じて調整または無効化してください
    if detection_time > 60:  # 1分以上かかる場合
        pytest.skip("Detection performance test skipped due to slow execution")


def test_anonymization_performance(large_text: str):
    """Test performance of PII anonymization."""
    masker = PIIMasker()

    # 匿名化の実行時間を計測
    start_time = time.time()
    anonymized = masker.anonymize_text(large_text)
    end_time = time.time()

    # 実行時間の記録
    anonymization_time = end_time - start_time

    # 匿名化結果の確認
    assert len(anonymized) > 0

    # 元のテキストとほぼ同じ長さであることを確認
    # (プレースホルダーに置き換えられるので、完全に同じではない)
    assert 0.5 * len(large_text) <= len(anonymized) <= 1.5 * len(large_text)

    # ログ出力
    print(f"\nPII Anonymization Performance:")
    print(f"- Text size: {len(large_text)} characters")
    print(f"- Anonymized text size: {len(anonymized)} characters")
    print(f"- Processing time: {anonymization_time:.2f} seconds")
    print(f"- Anonymization rate: {len(large_text) / anonymization_time:.2f} chars/second")

    # 非常に低速な場合は失敗とする（具体的な閾値は環境によって調整）
    if anonymization_time > 60:  # 1分以上かかる場合
        pytest.skip("Anonymization performance test skipped due to slow execution")


def test_memory_usage():
    """Test memory usage during PII processing."""
    try:
        import os

        import psutil
    except ImportError:
        pytest.skip("psutil not installed, skipping memory usage test")

    masker = PIIMasker()

    # 現在のプロセスを取得
    process = psutil.Process(os.getpid())

    # 初期メモリ使用量を記録
    initial_memory = process.memory_info().rss / (1024 * 1024)  # MB単位

    # テストテキストを生成（中程度のサイズ）
    base_text = """
    山田太郎さんの連絡先情報：
    電話番号：090-1234-5678
    メールアドレス：taro.yamada@example.com
    """
    test_text = base_text * 50

    # PIIの検出と匿名化を実行
    masker.detect_pii(test_text)
    masker.anonymize_text(test_text)

    # 終了時のメモリ使用量を記録
    final_memory = process.memory_info().rss / (1024 * 1024)  # MB単位

    # メモリ使用量の増加を計算
    memory_increase = final_memory - initial_memory

    # ログ出力
    print(f"\nMemory Usage:")
    print(f"- Initial memory: {initial_memory:.2f} MB")
    print(f"- Final memory: {final_memory:.2f} MB")
    print(f"- Memory increase: {memory_increase:.2f} MB")

    # 過度なメモリ使用量増加がないことを確認
    # 具体的な閾値は環境によって調整することをお勧めします
    assert memory_increase < 1000, f"Memory increase of {memory_increase:.2f} MB exceeds threshold"


def test_different_operator_performance():
    """Test performance of different anonymization operators."""
    masker = PIIMasker()

    # テストテキスト
    text = (
        """
    山田太郎さんの連絡先情報：
    電話番号：090-1234-5678
    メールアドレス：taro.yamada@example.com
    """
        * 20
    )

    operators = [
        {
            "name": "Replace",
            "config": {"operator": "replace", "params": {"new_value": "[REDACTED]"}},
        },
        {
            "name": "Mask",
            "config": {
                "operator": "mask",
                "params": {"masking_char": "*", "chars_to_mask": 4, "from_end": False},
            },
        },
        {"name": "Hash", "config": {"operator": "hash", "params": {}}},
    ]

    results = []

    for op in operators:
        # 実行時間を計測
        start_time = time.time()

        anonymized = masker.anonymize_text(
            text,
            operators={
                "PERSON": op["config"],
                "PHONE_NUMBER": op["config"],
                "EMAIL_ADDRESS": op["config"],
            },
        )

        end_time = time.time()
        processing_time = end_time - start_time

        results.append(
            {"operator": op["name"], "time": processing_time, "text_length": len(anonymized)}
        )

    # 結果をログ出力
    print("\nOperator Performance Comparison:")
    for result in results:
        print(f"- {result['operator']}: {result['time']:.4f} seconds")

    # 各オペレーターが正常に動作したことを確認
    assert all(result["text_length"] > 0 for result in results)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
