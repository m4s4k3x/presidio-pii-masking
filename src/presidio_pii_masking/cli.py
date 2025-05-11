"""Command-line interface for PII masking."""

import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from presidio_pii_masking.config import MaskingConfig
from presidio_pii_masking.masking import PIIMasker

app = typer.Typer(help="PII detection and anonymization tool")
console = Console()


def parse_entities(entities_str: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated entity types into a list.

    Args:
        entities_str: Comma-separated entity types

    Returns:
        List of entity types or None if empty
    """
    if not entities_str:
        return None
    return [e.strip() for e in entities_str.split(",") if e.strip()]


@app.command()
def mask(
    input_file: Optional[Path] = typer.Argument(
        None, help="Input file to process (uses stdin if not provided)"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file (uses stdout if not provided)"
    ),
    config_file: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Configuration file in YAML format"
    ),
    entities: Optional[str] = typer.Option(
        None, "--entities", "-e", help="Entity types to anonymize (comma-separated)"
    ),
    language: str = typer.Option("ja", "--language", "-l", help="Language code"),
    model: str = typer.Option("ja_core_news_trf", "--model", "-m", help="spaCy model name"),
    threshold: float = typer.Option(0.5, "--threshold", "-t", help="Confidence score threshold"),
) -> None:
    """Detect and anonymize PII in text."""
    # Load configuration
    config = None
    if config_file:
        try:
            config = MaskingConfig.from_file(config_file)
        except Exception as e:
            console.print(f"[bold red]Error loading configuration file:[/] {e}")
            raise typer.Exit(1)
    else:
        config = MaskingConfig()
        config.language = language
        config.model_name = model
        config.score_threshold = threshold
        if entities:
            config.entity_types = parse_entities(entities)

    # Initialize masker
    try:
        masker = PIIMasker(
            language=config.language,
            model_name=config.model_name,
            score_threshold=config.score_threshold,
        )
    except Exception as e:
        console.print(f"[bold red]Error initializing PII masker:[/] {e}")
        raise typer.Exit(1)

    # Read input
    if input_file:
        try:
            text = input_file.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[bold red]Error reading input file:[/] {e}")
            raise typer.Exit(1)
    else:
        text = sys.stdin.read()

    # Process text
    try:
        anonymized_text = masker.anonymize_text(
            text=text,
            entity_types=config.entity_types,
            operators={
                entity_type: {"operator": op_config.operator, "params": op_config.params}
                for entity_type, op_config in config.operators.items()
            }
            if config.operators
            else None,
        )
    except Exception as e:
        console.print(f"[bold red]Error anonymizing text:[/] {e}")
        raise typer.Exit(1)

    # Write output
    if output_file:
        try:
            output_file.write_text(anonymized_text, encoding="utf-8")
        except Exception as e:
            console.print(f"[bold red]Error writing output file:[/] {e}")
            raise typer.Exit(1)
    else:
        print(anonymized_text)


@app.command()
def detect(
    input_file: Optional[Path] = typer.Argument(
        None, help="Input file to process (uses stdin if not provided)"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file (uses stdout if not provided)"
    ),
    entities: Optional[str] = typer.Option(
        None, "--entities", "-e", help="Entity types to detect (comma-separated)"
    ),
    language: str = typer.Option("ja", "--language", "-l", help="Language code"),
    model: str = typer.Option("ja_core_news_trf", "--model", "-m", help="spaCy model name"),
    threshold: float = typer.Option(0.5, "--threshold", "-t", help="Confidence score threshold"),
) -> None:
    """Detect PII in text without anonymizing."""
    # Initialize masker
    try:
        masker = PIIMasker(
            language=language,
            model_name=model,
            score_threshold=threshold,
        )
    except Exception as e:
        console.print(f"[bold red]Error initializing PII masker:[/] {e}")
        raise typer.Exit(1)

    # Read input
    if input_file:
        try:
            text = input_file.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[bold red]Error reading input file:[/] {e}")
            raise typer.Exit(1)
    else:
        text = sys.stdin.read()

    # Process text
    try:
        entity_list = parse_entities(entities) if entities else None
        results = masker.detect_pii(text=text, entity_types=entity_list)
    except Exception as e:
        console.print(f"[bold red]Error detecting PII:[/] {e}")
        raise typer.Exit(1)

    # Format and output results
    if results:
        output = "\n".join(
            f"Type: {r['entity_type']}, Text: '{text[r['start']:r['end']]}', "
            f"Score: {r['score']:.2f}, Position: {r['start']}-{r['end']}"
            for r in results
        )
    else:
        output = "No PII detected."

    # Write output
    if output_file:
        try:
            output_file.write_text(output, encoding="utf-8")
        except Exception as e:
            console.print(f"[bold red]Error writing output file:[/] {e}")
            raise typer.Exit(1)
    else:
        console.print(Panel(output, title="PII Detection Results"))


@app.command()
def list_entities() -> None:
    """List supported entity types."""
    entities = [
        ("PERSON", "人名"),
        ("PHONE_NUMBER", "電話番号"),
        ("EMAIL_ADDRESS", "メールアドレス"),
        ("ADDRESS", "住所"),
        ("BIRTHDATE", "生年月日"),
        ("CREDIT_CARD", "クレジットカード番号"),
        ("URL", "URL"),
        ("LOCATION", "場所"),
        ("DATE_TIME", "日付・時間"),
        ("NRP", "パスポート番号"),
        ("IP_ADDRESS", "IPアドレス"),
        # 日本固有のエンティティタイプ
        ("JP_MY_NUMBER", "マイナンバー（個人番号）"),
        ("JP_DRIVER_LICENSE", "日本の運転免許証番号"),
        ("JP_BANK_ACCOUNT", "日本の銀行口座番号"),
        ("JP_POSTAL_CODE", "日本の郵便番号"),
        # その他の国固有のエンティティタイプ
        ("US_SSN", "米国社会保障番号"),
        ("US_ITIN", "米国個人納税者番号"),
        ("US_DRIVER_LICENSE", "米国運転免許証番号"),
    ]

    # テーブルを作成
    table = Table(title="サポートされているエンティティタイプ")
    table.add_column("エンティティタイプ", style="bold")
    table.add_column("説明")

    for entity_type, description in entities:
        table.add_row(entity_type, description)

    console.print(table)


if __name__ == "__main__":
    app()
