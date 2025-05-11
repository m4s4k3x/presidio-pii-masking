# Presidio PII Masking

Microsoft Presidio を活用した個人情報（PII）検出・匿名化ツール

## 概要

このツールは、テキストデータから個人を特定できる情報（PII: Personally Identifiable Information）を検出し、匿名化するための機能を提供します。Microsoft Presidio をベースに、日本語対応や日本固有の個人情報タイプの検出など、拡張機能を追加しています。

## 特徴

- テキスト内の個人情報を高精度で検出
- 検出された個人情報の匿名化（マスキング、置換、削除など）
- 日本語固有の個人情報タイプの検出（マイナンバー、運転免許証番号など）
- カスタム匿名化ルールの定義
- コマンドラインインターフェース提供

## インストール

### 必要条件

- Python 3.10 以上
- Poetry（パッケージ管理ツール）

### インストール手順

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/presidio-pii-masking.git
cd presidio-pii-masking

# Poetryを使った依存関係のインストール
poetry install

# 日本語モデルのダウンロード
poetry run python -m spacy download ja_core_news_trf
```

## 使い方

### Python コード内での使用

```python
from presidio_pii_masking import PIIMasker

# マスカーの初期化
masker = PIIMasker()

# テキストの匿名化
text = "山田太郎の電話番号は090-1234-5678です。メールはtaro.yamada@example.comです。"
anonymized_text = masker.anonymize_text(text)
print(anonymized_text)
# 出力例: "<PERSON>の電話番号は<PHONE_NUMBER>です。メールは<EMAIL_ADDRESS>です。"

# 特定のエンティティタイプのみを匿名化
anonymized_text = masker.anonymize_text(text, entity_types=["PHONE_NUMBER"])
print(anonymized_text)
# 出力例: "山田太郎の電話番号は<PHONE_NUMBER>です。メールはtaro.yamada@example.comです。"

# カスタム匿名化ルールを使用
anonymized_text = masker.anonymize_text(
    text,
    operators={
        "PERSON": {"operator": "replace", "params": {"new_value": "名無しさん"}},
        "PHONE_NUMBER": {"operator": "mask", "params": {"masking_char": "*", "chars_to_mask": 8}},
    }
)
print(anonymized_text)
# 出力例: "名無しさんの電話番号は********5678です。メールは<EMAIL_ADDRESS>です。"
```

### コマンドラインでの使用

```bash
# 基本的な使用方法
pii-mask input.txt -o output.txt

# 特定のエンティティタイプのみ処理
pii-mask input.txt -o output.txt --entities PERSON,PHONE_NUMBER

# 標準入力からの処理
cat input.txt | pii-mask > output.txt

# PIIの検出のみを行う（匿名化なし）
pii-mask detect input.txt

# サポートされているエンティティタイプの一覧表示
pii-mask list-entities
```

## サポートしているエンティティタイプ

- 一般的な PII:

  - PERSON: 人名
  - PHONE_NUMBER: 電話番号
  - EMAIL_ADDRESS: メールアドレス
  - CREDIT_CARD: クレジットカード番号
  - URL: URL
  - LOCATION: 場所
  - DATE_TIME: 日付・時間
  - IP_ADDRESS: IP アドレス

- 日本固有の PII:

  - JP_MY_NUMBER: マイナンバー（個人番号）
  - JP_DRIVER_LICENSE: 日本の運転免許証番号
  - JP_BANK_ACCOUNT: 日本の銀行口座番号
  - JP_POSTAL_CODE: 日本の郵便番号

- その他の国固有の PII:
  - US_SSN: 米国社会保障番号
  - US_ITIN: 米国個人納税者番号
  - US_DRIVER_LICENSE: 米国運転免許証番号

## 将来の展望

- AWS Lambda での実行
- Terraform を使った自動デプロイ
- 構造化データ（CSV、JSON）のサポート
- より多くの日本固有の個人情報タイプの追加

## ライセンス

MIT

## 謝辞

このプロジェクトは[Microsoft Presidio](https://github.com/microsoft/presidio/)をベースにしています。
