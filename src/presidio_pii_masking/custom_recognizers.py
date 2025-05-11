"""Custom recognizers for Japanese PII entities."""

import re
from typing import List, Optional, Tuple

from presidio_analyzer import (EntityRecognizer, Pattern, PatternRecognizer,
                               RecognizerRegistry, RecognizerResult)
from presidio_analyzer.nlp_engine import NlpArtifacts


def register_custom_recognizers(registry: RecognizerRegistry) -> None:
    """Register custom recognizers with the provided registry.

    Args:
        registry: The recognizer registry to register custom recognizers with
    """
    # 日本の電話番号の認識器
    jp_phone_recognizer = JapanesePhoneNumberRecognizer()
    registry.add_recognizer(jp_phone_recognizer)

    # メールアドレスの認識器
    email_recognizer = EmailRecognizer()
    registry.add_recognizer(email_recognizer)

    # 日本人名の認識器
    jp_person_recognizer = JapanesePersonRecognizer()
    registry.add_recognizer(jp_person_recognizer)

    # 日本の住所認識器
    jp_address_recognizer = JapaneseAddressRecognizer()
    registry.add_recognizer(jp_address_recognizer)

    # 生年月日認識器
    birthdate_recognizer = BirthDateRecognizer()
    registry.add_recognizer(birthdate_recognizer)

    # マイナンバー認識器
    my_number_recognizer = JapaneseMyNumberRecognizer()
    registry.add_recognizer(my_number_recognizer)


class JapanesePhoneNumberRecognizer(PatternRecognizer):
    """Japanese phone number recognizer."""

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "ja",
        supported_entity: str = "PHONE_NUMBER",
    ):
        """Initialize the JapanesePhoneNumberRecognizer."""

        if patterns is None:
            # 携帯電話番号: 090-1234-5678 形式
            mobile_pattern = Pattern(
                name="mobile_phone",
                regex="0[789]0[-\\s]?\\d{4}[-\\s]?\\d{4}",
                score=0.8,
            )

            # 固定電話番号: 03-1234-5678 形式
            landline_pattern = Pattern(
                name="landline_phone",
                regex="0\\d{1,4}[-\\s]?\\d{1,4}[-\\s]?\\d{4}",
                score=0.8,
            )

            patterns = [mobile_pattern, landline_pattern]

        # 電話番号の文脈語
        if context is None:
            context = ["電話", "電話番号", "携帯", "携帯電話", "TEL", "Tel", "tel", "連絡先", "通話", "コール"]

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )


class EmailRecognizer(PatternRecognizer):
    """Email address recognizer."""

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "ja",
        supported_entity: str = "EMAIL_ADDRESS",
    ):
        """Initialize the EmailRecognizer."""

        if patterns is None:
            # メールアドレスパターン
            email_pattern = Pattern(
                name="email",
                regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                score=0.9,
            )

            patterns = [email_pattern]

        # メールアドレスの文脈語
        if context is None:
            context = ["メール", "メールアドレス", "メアド", "email", "Email", "E-mail", "mail", "アドレス"]

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )


class JapanesePersonRecognizer(EntityRecognizer):
    """Japanese person name recognizer using spaCy NER."""

    def __init__(
        self,
        supported_language: str = "ja",
        supported_entity: str = "PERSON",
    ):
        """Initialize the JapanesePersonRecognizer."""
        super().__init__(
            supported_entities=[supported_entity],
            supported_language=supported_language,
        )

    def load(self) -> None:
        """Load the recognizer."""
        # This method is called on initialization
        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """Analyze text for Japanese person names using spaCy NER.

        Args:
            text: The text to analyze
            entities: The entities to look for
            nlp_artifacts: The NLP artifacts from the NLP engine

        Returns:
            List of RecognizerResult
        """
        results = []

        # Check if PERSON is in the entities list we are looking for
        if not self.check_entity_supported(entities, "PERSON"):
            return results

        # Using spaCy's named entity recognition
        for entity in nlp_artifacts.entities:
            if entity.label_ == "PERSON":
                # Create a result for each person entity
                start, end = entity.start_char, entity.end_char
                # スパムと見なされそうな単語をフィルタリング
                text_span = text[start:end]
                if self._is_valid_person_name(text_span):
                    result = RecognizerResult(
                        entity_type="PERSON",
                        start=start,
                        end=end,
                        score=0.85,  # Confidence score
                        analysis_explanation=None,
                        recognition_metadata={
                            "source": "spacy_model",
                            "entity_value": text_span,
                        },
                    )
                    results.append(result)

        # 一般的な日本人名のパターン（改善版）
        # 一般的な姓名の形式に合致する2-4文字+1-3文字のパターン
        common_name_pattern = r"(?<![ぁ-んァ-ン一-龯々])[一-龯々]{2,4}\s*[一-龯々]{1,3}(?![ぁ-んァ-ン一-龯々])"
        matches = re.finditer(common_name_pattern, text)
        for match in matches:
            start, end = match.span()
            text_span = text[start:end]
            if (
                self._is_valid_person_name(text_span)
                and len(text_span) >= 3
                and len(text_span) <= 8
            ):
                # 文脈語が名前の直後にある場合、スコアを上げる
                score = 0.75
                context_words = ["さん", "氏", "君", "様", "殿", "先生", "教授", "博士"]
                for context in context_words:
                    if (
                        end + len(context) <= len(text)
                        and text[end : end + len(context)] == context
                    ):
                        score = 0.85
                        break

                result = RecognizerResult(
                    entity_type="PERSON",
                    start=start,
                    end=end,
                    score=score,
                    analysis_explanation=None,
                    recognition_metadata={
                        "source": "pattern_matching",
                        "entity_value": text_span,
                    },
                )
                results.append(result)

        return results

    def check_entity_supported(self, entities: List[str], entity_type: str) -> bool:
        """Check if the entity type is supported and requested.

        Args:
            entities: List of entities to look for
            entity_type: The entity type to check

        Returns:
            True if the entity is supported and requested, False otherwise
        """
        # If entities is None or empty, all entities are supported
        if not entities:
            return True

        return entity_type in entities

    def _is_valid_person_name(self, text: str) -> bool:
        """Check if the text is a valid person name.

        Args:
            text: The text to check

        Returns:
            True if the text is a valid person name, False otherwise
        """
        # 除外する単語リスト（明らかに人名ではない単語を含む）
        exclusions = [
            "電話",
            "電話番号",
            "携帯",
            "メール",
            "メールアドレス",
            "住所",
            "郵便番号",
            "会社",
            "学校",
            "大学",
            "病院",
            "銀行",
            "支店",
            "本店",
            "本社",
            "です",
            "ます",
            "ました",
            "ください",
            "なし",
            "あり",
        ]

        for word in exclusions:
            if word in text:
                return False

        # 単語が短すぎる場合も除外
        if len(text.strip()) < 3:
            return False

        return True


class JapaneseAddressRecognizer(EntityRecognizer):
    """Japanese address recognizer with improved accuracy."""

    def __init__(
        self,
        supported_language: str = "ja",
        supported_entity: str = "ADDRESS",
    ):
        """Initialize the JapaneseAddressRecognizer."""
        super().__init__(
            supported_entities=[supported_entity],
            supported_language=supported_language,
        )

        # 都道府県リスト
        self.prefectures = [
            "北海道",
            "青森県",
            "岩手県",
            "宮城県",
            "秋田県",
            "山形県",
            "福島県",
            "茨城県",
            "栃木県",
            "群馬県",
            "埼玉県",
            "千葉県",
            "東京都",
            "神奈川県",
            "新潟県",
            "富山県",
            "石川県",
            "福井県",
            "山梨県",
            "長野県",
            "岐阜県",
            "静岡県",
            "愛知県",
            "三重県",
            "滋賀県",
            "京都府",
            "大阪府",
            "兵庫県",
            "奈良県",
            "和歌山県",
            "鳥取県",
            "島根県",
            "岡山県",
            "広島県",
            "山口県",
            "徳島県",
            "香川県",
            "愛媛県",
            "高知県",
            "福岡県",
            "佐賀県",
            "長崎県",
            "熊本県",
            "大分県",
            "宮崎県",
            "鹿児島県",
            "沖縄県",
        ]

        # 正規表現パターン
        self.address_patterns = [
            # 都道府県から始まる住所
            r"(?:"
            + "|".join(self.prefectures)
            + r")(?:[一-龯々ぁ-んァ-ン0-9０-９a-zA-Z\-－・\s]{2,30}[市区町村郡])",
            # 郵便番号
            r"〒\d{3}[-−]?\d{4}",
            # 丁目・番地を含む住所表現
            r"[一-龯々ぁ-んァ-ン0-9０-９]+(?:丁目|番町|条|番地|番|通|町目|条通|の町|横町)([-−0-9０-９一二三四五六七八九十百千]+)?",
        ]

        # 住所の一部として使われる単語リスト
        self.address_keywords = [
            "市",
            "区",
            "町",
            "村",
            "郡",
            "丁目",
            "番地",
            "号",
            "マンション",
            "アパート",
            "団地",
            "住宅",
            "荘",
            "ハイツ",
            "コーポ",
            "ビル",
            "タワー",
            "コート",
            "号室",
            "室",
            "階",
        ]

    def load(self) -> None:
        """Load the recognizer."""
        # This method is called on initialization
        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """Analyze text for Japanese addresses.

        Args:
            text: The text to analyze
            entities: The entities to look for
            nlp_artifacts: The NLP artifacts from the NLP engine

        Returns:
            List of RecognizerResult
        """
        results = []

        # Check if ADDRESS is in the entities list we are looking for
        if not self.check_entity_supported(entities, "ADDRESS"):
            return results

        # 住所の文脈語
        context_words = ["住所", "自宅", "所在地", "住所は", "住所：", "自宅は", "自宅：", "所在地は", "所在地："]
        context_positions = []

        # 文脈語の位置を探す
        for context in context_words:
            for match in re.finditer(context, text):
                context_positions.append((match.start(), match.end()))

        # まず文脈語による住所検索
        for ctx_start, ctx_end in context_positions:
            # 文脈語の直後からの文字列を取得（改行または次の文脈語まで）
            remaining_text = text[ctx_end:]
            end_match = re.search(r"[\n\r]|(" + "|".join(context_words) + ")", remaining_text)
            if end_match:
                address_candidate = remaining_text[: end_match.start()].strip()
            else:
                address_candidate = remaining_text.strip()

            # 住所らしい文字列が含まれていれば検出
            if len(address_candidate) > 4 and self._has_address_features(address_candidate):
                result = RecognizerResult(
                    entity_type="ADDRESS",
                    start=ctx_end,
                    end=ctx_end + len(address_candidate),
                    score=0.9,  # 文脈語の直後なので高スコア
                    analysis_explanation=None,
                    recognition_metadata={
                        "source": "context_pattern",
                        "entity_value": address_candidate,
                    },
                )
                results.append(result)

        # パターンマッチング
        for pattern in self.address_patterns:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                text_span = text[start:end]

                # 電話番号やマイナンバーなどの数字パターンをフィルタリング
                if self._is_valid_address(text_span):
                    # 文脈語の近くにあるかチェック
                    score = 0.8
                    for ctx_start, ctx_end in context_positions:
                        # 文脈語の直後に住所がある場合、スコアを上げる
                        if abs(ctx_end - start) < 20:  # 20文字以内に住所がある
                            score = 0.95
                            break

                    # 住所の範囲を拡大（前後にある住所関連の部分も含める）
                    extended_start, extended_end = self._expand_address_span(text, start, end)
                    text_span = text[extended_start:extended_end]

                    result = RecognizerResult(
                        entity_type="ADDRESS",
                        start=extended_start,
                        end=extended_end,
                        score=score,
                        analysis_explanation=None,
                        recognition_metadata={
                            "source": "pattern_matching",
                            "entity_value": text_span,
                        },
                    )
                    results.append(result)

        # spaCyのLOC認識結果も活用
        for entity in nlp_artifacts.entities:
            if entity.label_ == "LOC":
                # 地名エンティティを住所候補として扱う
                start, end = entity.start_char, entity.end_char
                text_span = text[start:end]

                # 住所の特徴語句を含む場合のみ採用（誤検出を減らすため）
                if self._has_address_features(text_span):
                    # 住所の範囲を拡大（前後にある住所関連の部分も含める）
                    extended_start, extended_end = self._expand_address_span(text, start, end)
                    text_span = text[extended_start:extended_end]

                    result = RecognizerResult(
                        entity_type="ADDRESS",
                        start=extended_start,
                        end=extended_end,
                        score=0.75,
                        analysis_explanation=None,
                        recognition_metadata={
                            "source": "spacy_model",
                            "entity_value": text_span,
                        },
                    )
                    results.append(result)

        # 重複や被包含エンティティを除去
        results = self._remove_overlapping_results(results)

        return results

    def check_entity_supported(self, entities: List[str], entity_type: str) -> bool:
        """Check if the entity type is supported and requested."""
        if not entities:
            return True
        return entity_type in entities

    def _is_valid_address(self, text: str) -> bool:
        """Check if the text is likely to be a valid address."""
        # 明らかに住所ではない数字パターンを除外
        if re.match(r"^\d{3}-\d{4}$", text):  # 郵便番号のみ
            return False
        if re.match(r"^\d{4}年\d{1,2}月\d{1,2}日$", text):  # 日付
            return False
        if re.match(r"^\d{11,12}$", text):  # マイナンバーなど
            return False
        if re.match(r"^\d{2,4}-\d{2,4}-\d{4}$", text):  # 電話番号
            return False

        return self._has_address_features(text)

    def _has_address_features(self, text: str) -> bool:
        """住所の特徴（都道府県名、市区町村、住所表現）を含むか確認."""
        # 都道府県名を含む
        if any(pref in text for pref in self.prefectures):
            return True

        # 住所キーワードを含む
        if any(keyword in text for keyword in self.address_keywords):
            return True

        # 丁目、番地、号などの表記を含む
        if re.search(r"([0-9０-９一二三四五六七八九十]+)(丁目|番地|号|番|条|町目|区|市)", text):
            return True

        # 「X-Y-Z」形式の住所表記
        if re.search(r"[0-9０-９]{1,3}[-－][0-9０-９]{1,3}[-－][0-9０-９]{1,3}", text):
            return True

        return False

    def _expand_address_span(self, text: str, start: int, end: int) -> Tuple[int, int]:
        """住所の範囲を前後に拡大する."""
        # 前方に都道府県名や市区町村名があれば含める
        pre_text = text[:start]
        for pref in self.prefectures:
            pref_pos = pre_text.rfind(pref)
            if pref_pos != -1 and start - pref_pos < 30:  # 30文字以内に都道府県名がある
                start = pref_pos
                break

        # 後方に番地や部屋番号などがあれば含める
        post_text = text[end : min(len(text), end + 30)]  # 後方30文字まで検索

        # 数字-数字-数字の形式
        num_pattern = re.search(r"[-−0-9０-９一二三四五六七八九十]+", post_text)
        if num_pattern:
            # 次の明らかな区切り（句読点や改行）まで含める
            extended_end = end + num_pattern.end()
            delimiter_match = re.search(r"[。、.，,；;:\n\r]", post_text[num_pattern.end() :])
            if delimiter_match:
                extended_end = end + num_pattern.end() + delimiter_match.start()
            end = min(len(text), extended_end)

        return start, end

    def _remove_overlapping_results(
        self, results: List[RecognizerResult]
    ) -> List[RecognizerResult]:
        """重複や包含関係にあるエンティティを除去."""
        if not results:
            return results

        # スコアの高い順にソート
        sorted_results = sorted(results, key=lambda x: (-x.score, x.start))

        # 重複を除去
        filtered_results = []
        for result in sorted_results:
            # すでに追加済みの結果と重複/包含関係をチェック
            is_contained = False
            for existing in filtered_results:
                # 完全重複
                if result.start == existing.start and result.end == existing.end:
                    is_contained = True
                    break

                # 包含関係（現在の結果が既存の結果に完全に含まれる）
                if result.start >= existing.start and result.end <= existing.end:
                    is_contained = True
                    break

                # 大幅な重複（80%以上重複している場合）
                overlap_start = max(result.start, existing.start)
                overlap_end = min(result.end, existing.end)
                overlap_length = overlap_end - overlap_start
                result_length = result.end - result.start

                if overlap_length > 0 and overlap_length / result_length > 0.8:
                    is_contained = True
                    break

            if not is_contained:
                filtered_results.append(result)

        return filtered_results


class BirthDateRecognizer(PatternRecognizer):
    """Birth date recognizer for Japanese format dates."""

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "ja",
        supported_entity: str = "BIRTHDATE",
    ):
        """Initialize the BirthDateRecognizer."""

        if patterns is None:
            # 西暦の生年月日: 1990年4月1日 形式
            date_pattern1 = Pattern(
                name="western_date",
                regex=r"\d{4}年\d{1,2}月\d{1,2}日",
                score=0.7,
            )

            # 西暦の生年月日: 1990/4/1 形式
            date_pattern2 = Pattern(
                name="western_date_slash",
                regex=r"\d{4}[/／]\d{1,2}[/／]\d{1,2}",
                score=0.7,
            )

            # 年のみ: 1990年生まれ
            year_pattern = Pattern(
                name="year_only",
                regex=r"\d{4}年(?:生|生まれ)",
                score=0.6,
            )

            # 元号の生年月日: 平成2年4月1日 形式
            era_date_pattern = Pattern(
                name="japanese_era_date",
                regex=r"(?:昭和|平成|大正|明治|令和)\d{1,2}年\d{1,2}月\d{1,2}日",
                score=0.7,
            )

            patterns = [date_pattern1, date_pattern2, year_pattern, era_date_pattern]

        # 生年月日の文脈語
        if context is None:
            context = ["生年月日", "誕生日", "生まれ", "出生", "年齢", "生誕", "生年月日:", "誕生日:"]

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )


class JapaneseMyNumberRecognizer(PatternRecognizer):
    """Japanese My Number (Individual Number) recognizer."""

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "ja",
        supported_entity: str = "JP_MY_NUMBER",
    ):
        """Initialize the JapaneseMyNumberRecognizer."""

        if patterns is None:
            # マイナンバー: 12桁の数字
            my_number_pattern = Pattern(
                name="my_number",
                regex=r"\d{4}[\s-]?\d{4}[\s-]?\d{4}|\d{12}",
                score=0.6,
            )

            patterns = [my_number_pattern]

        # マイナンバーの文脈語
        if context is None:
            context = ["マイナンバー", "個人番号", "個人番号カード", "通知カード", "番号", "マイナンバー:", "個人番号:"]

        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
