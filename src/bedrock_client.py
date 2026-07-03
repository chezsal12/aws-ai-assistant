"""
Bedrock Client

Handles interactions with Amazon Bedrock (Claude 3.5 Sonnet).
"""

import json
import logging
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockClient:
    """Client for Amazon Bedrock AI interactions."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Bedrock client.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=config.get('bedrock_region', 'us-east-1')
        )
        self.model_id = config.get(
            'bedrock_model_id',
            'anthropic.claude-3-5-sonnet-20241022-v2:0'
        )

    def get_completion(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Get completion from Bedrock.

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens in response
            temperature: Temperature (0-1)
            system_prompt: Optional system prompt

        Returns:
            Response text
        """
        try:
            max_tokens = max_tokens or self.config.get('max_tokens', 2000)
            temperature = temperature or self.config.get('temperature', 0.7)

            # Build request
            messages = [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]

            request_body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': messages
            }

            # Add system prompt if provided
            if system_prompt:
                request_body['system'] = system_prompt

            logger.info(f"Calling Bedrock with model: {self.model_id}")

            # Call Bedrock
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            answer = response_body['content'][0]['text']

            logger.info(f"Bedrock response received ({len(answer)} chars)")

            return answer

        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting completion: {e}")
            raise

    def get_completion_with_rag(
        self,
        prompt: str,
        context_documents: list,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Get completion with RAG context.

        Args:
            prompt: User question
            context_documents: Retrieved relevant documents
            max_tokens: Maximum tokens in response

        Returns:
            Response text with citations
        """
        try:
            # Build RAG-enhanced prompt
            context = "\n\n".join([
                f"Document {i+1}:\n{doc['content']}\nSource: {doc['source']}"
                for i, doc in enumerate(context_documents[:5])  # Top 5 docs
            ])

            enhanced_prompt = f"""Answer the following question using the provided documentation context.
If the context doesn't contain enough information, say so and provide your best answer based on your knowledge.

Context from AWS Documentation:
{context}

User Question: {prompt}

Provide a clear, accurate answer. Include citations to the source documents when applicable.
"""

            return self.get_completion(
                enhanced_prompt,
                max_tokens=max_tokens or 3000,
                temperature=0.3  # Lower temp for factual accuracy
            )

        except Exception as e:
            logger.error(f"Error in RAG completion: {e}")
            # Fallback to regular completion
            return self.get_completion(prompt)

    def analyze_with_context(
        self,
        question: str,
        aws_resources: Dict[str, Any],
        metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze question with AWS resource context.

        Args:
            question: User question
            aws_resources: Resource metadata
            metrics: Optional CloudWatch metrics

        Returns:
            Analysis with recommendations
        """
        try:
            # Build context-aware prompt
            prompt = f"""You are an AWS expert analyzing a user's actual infrastructure.

User Question: {question}

AWS Resources:
{json.dumps(aws_resources, indent=2)}
"""

            if metrics:
                prompt += f"""
CloudWatch Metrics:
{json.dumps(metrics, indent=2)}
"""

            prompt += """
Provide specific, actionable recommendations based on the user's actual resources.
Include cost estimates and implementation steps where applicable.

Format your response as:
1. Summary (1-2 sentences)
2. Findings (bullet points)
3. Recommendations (specific actions)
4. Estimated Impact (cost, performance)
"""

            response_text = self.get_completion(
                prompt,
                max_tokens=2000,
                temperature=0.2  # Deterministic for analysis
            )

            return {
                'analysis': response_text,
                'resources_analyzed': list(aws_resources.keys()),
                'has_metrics': metrics is not None
            }

        except Exception as e:
            logger.error(f"Error in contextual analysis: {e}")
            raise
