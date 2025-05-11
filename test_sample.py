"""簡単なテストスクリプト"""

from presidio_pii_masking import PIIMasker


def main():
    # より低いスコアしきい値でマスカーを初期化
    masker = PIIMasker(score_threshold=0.3)

    # テスト用のテキスト
    text1 = "山田太郎の電話番号は090-1234-5678です。メールはtaro.yamada@example.comです。"

    # まずデバッグ用に検出のみ試す
    print("テキスト1の検出結果:")
    results1 = masker.detect_pii(text1)
    if results1:
        for result in results1:
            print(
                f"  - タイプ: {result['entity_type']}, テキスト: '{text1[result['start']:result['end']]}', スコア: {result['score']:.2f}"
            )
    else:
        print("  検出結果なし")

    # より明確なPII情報を含むテキスト
    text2 = "私の電話番号は090-1234-5678です。メールアドレスはtest@example.comです。郵便番号は123-4567です。"

    # 検出結果
    print("\nテキスト2の検出結果:")
    results2 = masker.detect_pii(text2)
    if results2:
        for result in results2:
            print(
                f"  - タイプ: {result['entity_type']}, テキスト: '{text2[result['start']:result['end']]}', スコア: {result['score']:.2f}"
            )
    else:
        print("  検出結果なし")

    # 匿名化
    anonymized = masker.anonymize_text(text2)
    print(f"\n匿名化後: {anonymized}")

    # カスタム匿名化
    custom_anonymized = masker.anonymize_text(
        text2,
        operators={
            "PHONE_NUMBER": {
                "operator": "mask",
                "params": {"masking_char": "*", "chars_to_mask": 8, "from_end": False},
            },
            "EMAIL_ADDRESS": {"operator": "replace", "params": {"new_value": "[メールアドレス]"}},
        },
    )
    print(f"\nカスタム匿名化後: {custom_anonymized}")


if __name__ == "__main__":
    main()
