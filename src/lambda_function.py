"""
AWS AI Assistant - Main Lambda Handler

Slack bot that answers AWS questions using Bedrock + RAG + real-time analysis.
"""

import json
import logging
import os
from typing import Dict, Any

import boto3
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from bedrock_client import BedrockClient
from utils import setup_logging, load_config

logger = setup_logging(__name__)

# Initialize Slack app
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    process_before_response=True
)

# Initialize Bedrock client
config = load_config()
bedrock_client = BedrockClient(config)


@slack_app.event("app_mention")
def handle_mention(event, say, client):
    """
    Handle @mentions of the bot.

    Args:
        event: Slack event data
        say: Function to send message
        client: Slack client
    """
    try:
        user_message = event.get("text", "")
        channel = event.get("channel")
        thread_ts = event.get("ts")
        user_id = event.get("user")

        # Remove bot mention from message
        bot_user_id = client.auth_test()["user_id"]
        user_message = user_message.replace(f"<@{bot_user_id}>", "").strip()

        if not user_message:
            say(
                text="Hi! Ask me anything about AWS. Example: 'What is Lambda provisioned concurrency?'",
                thread_ts=thread_ts
            )
            return

        logger.info(f"Received question from user {user_id}: {user_message}")

        # Send "thinking" indicator
        say(
            text="🤔 Let me think about that...",
            thread_ts=thread_ts
        )

        # Get response from AI
        response = process_question(user_message, user_id)

        # Send response
        say(
            text=response["text"],
            blocks=response.get("blocks"),
            thread_ts=thread_ts
        )

    except Exception as e:
        logger.error(f"Error handling mention: {e}", exc_info=True)
        say(
            text=f"Sorry, I encountered an error: {str(e)}",
            thread_ts=thread_ts
        )


@slack_app.message("hello")
def handle_hello(message, say):
    """Handle hello messages."""
    say(f"Hi there, <@{message['user']}>! I'm your AWS AI Assistant. Mention me with @aws-assistant to ask questions!")


@slack_app.command("/aws-help")
def handle_help_command(ack, say):
    """Handle /aws-help command."""
    ack()

    help_text = """
*AWS AI Assistant - Help Guide* 🤖

*How to Use:*
• Mention me: `@aws-assistant your question here`
• I can answer AWS questions, analyze your resources, and provide recommendations

*Example Questions:*

📚 *Documentation:*
• "What's the difference between Lambda provisioned and reserved concurrency?"
• "How do I enable X-Ray tracing for Lambda?"
• "Best practices for RDS backups?"

🔍 *Infrastructure Analysis:*
• "Why is my Lambda function slow?"
• "Show me my biggest cost spikes this week"
• "What can I optimize right now?"

💰 *Cost Intelligence:*
• "What caused my cost spike yesterday?"
• "How much am I spending on Lambda?"

⚙️ *Resource Analysis:*
• "Check my RDS instances for optimization"
• "Are any of my EC2 instances oversized?"

*Commands:*
• `/aws-help` - Show this help message
• `/aws-status` - Check assistant status

*Tips:*
• Be specific in your questions
• Mention resource names/IDs for detailed analysis
• I remember context within a thread
"""

    say(help_text)


def process_question(question: str, user_id: str) -> Dict[str, Any]:
    """
    Process user question and generate response.

    Args:
        question: User's question
        user_id: Slack user ID

    Returns:
        Response dict with text and optional blocks
    """
    try:
        # For Phase 1: Simple Bedrock call without RAG
        # Phase 2: Add AWS resource analysis
        # Phase 3: Add RAG for documentation

        logger.info(f"Processing question: {question}")

        # Build prompt for Claude
        prompt = f"""You are an AWS expert assistant helping users with AWS questions.

User Question: {question}

Provide a helpful, accurate answer. If you're not certain about something, say so.
Keep answers concise but complete. Use bullet points for clarity.

If the question is about specific AWS resources or performance issues, note that you'll need
resource details to give specific recommendations (we'll add this capability soon).
"""

        # Get response from Bedrock
        answer = bedrock_client.get_completion(prompt)

        # Format response for Slack
        response = {
            "text": answer,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": answer
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "🤖 Powered by Amazon Bedrock (Claude 3.5 Sonnet)"
                        }
                    ]
                }
            ]
        }

        return response

    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        return {
            "text": f"Sorry, I encountered an error processing your question: {str(e)}"
        }


# Lambda handler
handler = SlackRequestHandler(slack_app)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Slack events.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Response dict
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Handle Slack URL verification challenge
        if "challenge" in event.get("body", ""):
            body = json.loads(event["body"])
            return {
                "statusCode": 200,
                "body": json.dumps({"challenge": body["challenge"]})
            }

        # Handle Slack events via Bolt
        return handler.handle(event, context)

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


# Local testing
if __name__ == "__main__":
    # Test prompt processing
    test_question = "What is AWS Lambda?"
    response = process_question(test_question, "test_user")
    print(json.dumps(response, indent=2))
