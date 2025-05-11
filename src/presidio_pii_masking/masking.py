"""PII detection and anonymization core functions."""

from typing import Any, Dict, List, Optional, Union

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# カスタム認識器を再度有効化
from presidio_pii_masking.custom_recognizers import register_custom_recognizers


class PIIMasker:
    """PII detection and anonymization class.

    This class provides methods to detect and anonymize PII in text data.
    """

    def __init__(
        self,
        language: str = "ja",
        model_name: str = "ja_core_news_trf",
        score_threshold: float = 0.5,
    ) -> None:
        """Initialize PIIMasker.

        Args:
            language: Language code for the NLP model
            model_name: Name of the spaCy model to use
            score_threshold: Confidence score threshold for PII detection
        """
        self.language = language
        self.model_name = model_name
        self.score_threshold = score_threshold

        # Initialize NLP engine with spaCy
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": language, "model_name": model_name}],
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        nlp_engine = provider.create_engine()

        # Initialize analyzer and anonymizer
        registry = RecognizerRegistry()

        # カスタム認識器を再度有効化
        register_custom_recognizers(registry)

        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry,
        )
        self.anonymizer = AnonymizerEngine()

    def detect_pii(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Detect PII in text.

        Args:
            text: Input text to analyze
            entity_types: List of entity types to detect (None for all supported types)

        Returns:
            List of detected PII entities with their details
        """
        results = self.analyzer.analyze(
            text=text,
            language=self.language,
            entities=entity_types,
            score_threshold=self.score_threshold,
        )

        return [result.to_dict() for result in results]

    def anonymize_text(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        operators: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None,
    ) -> str:
        """Anonymize PII in text.

        Args:
            text: Input text to anonymize
            entity_types: List of entity types to anonymize (None for all supported types)
            operators: Dictionary mapping entity types to anonymization operators
                       Example: {"PERSON": {"operator": "replace", "params": {"new_value": "名無しさん"}}}

        Returns:
            Anonymized text
        """
        # Detect PII entities
        analysis_results = self.analyzer.analyze(
            text=text,
            language=self.language,
            entities=entity_types,
            score_threshold=self.score_threshold,
        )

        if not analysis_results:
            return text

        # Prepare operator configs
        operator_configs: Dict[str, OperatorConfig] = {}
        if operators:
            for entity_type, operator_info in operators.items():
                if isinstance(operator_info, dict):
                    operator_name = operator_info.get("operator", "replace")
                    params = operator_info.get("params", {})
                    operator_configs[entity_type] = OperatorConfig(
                        operator_name=operator_name,
                        params=params,
                    )
                else:
                    operator_configs[entity_type] = OperatorConfig(
                        operator_name=str(operator_info),
                    )

        # Anonymize the text
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analysis_results,
            operators=operator_configs,
        )

        return anonymized_result.text
