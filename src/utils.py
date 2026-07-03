"""
Utility Functions

Helper functions for logging, configuration, and common operations.
"""

import os
import logging
from typing import Dict, Any


def setup_logging(name: str) -> logging.Logger:
    """
    Setup standardized logging.

    Args:
        name: Logger name

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)

    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.

    Returns:
        Configuration dictionary
    """
    config = {
        # Slack settings
        'slack_bot_token': os.environ.get('SLACK_BOT_TOKEN'),
        'slack_signing_secret': os.environ.get('SLACK_SIGNING_SECRET'),

        # Bedrock settings
        'bedrock_region': os.environ.get('BEDROCK_REGION', 'us-east-1'),
        'bedrock_model_id': os.environ.get(
            'BEDROCK_MODEL_ID',
            'anthropic.claude-3-5-sonnet-20241022-v2:0'
        ),
        'max_tokens': int(os.environ.get('MAX_TOKENS', '2000')),
        'temperature': float(os.environ.get('TEMPERATURE', '0.7')),

        # OpenSearch settings (for RAG)
        'opensearch_endpoint': os.environ.get('OPENSEARCH_ENDPOINT'),
        'opensearch_index': os.environ.get('OPENSEARCH_INDEX', 'aws-docs'),

        # DynamoDB settings
        'dynamodb_table': os.environ.get('DYNAMODB_TABLE', 'aws-assistant-chats'),

        # Integration settings
        'cost_detective_table': os.environ.get('COST_DETECTIVE_TABLE', 'cost-anomalies'),
        'optimizer_table': os.environ.get('OPTIMIZER_TABLE', 'optimizer-recommendations'),

        # AWS settings
        'aws_region': os.environ.get('AWS_REGION', 'us-east-1')
    }

    return config


def truncate_text(text: str, max_length: int = 3000) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_slack_code_block(code: str, language: str = "") -> str:
    """
    Format code for Slack code block.

    Args:
        code: Code to format
        language: Language identifier

    Returns:
        Formatted code block
    """
    return f"```{language}\n{code}\n```"


def extract_resource_id_from_text(text: str) -> Dict[str, list]:
    """
    Extract AWS resource IDs from text.

    Args:
        text: Text to parse

    Returns:
        Dict of resource types to IDs
    """
    import re

    resource_patterns = {
        'instance': r'i-[a-f0-9]{8,17}',
        'lambda': r'arn:aws:lambda:[a-z0-9-]+:\d+:function:[a-zA-Z0-9-_]+',
        'rds': r'[a-z0-9-]+-[a-z0-9-]+-[0-9]+\.([a-z0-9-]+)\.rds\.amazonaws\.com',
        'bucket': r's3://[a-z0-9.-]+'
    }

    results = {}

    for resource_type, pattern in resource_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            results[resource_type] = list(set(matches))

    return results
