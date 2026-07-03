"""
AWS AI Assistant - Simplified Lambda Handler (without slack-bolt)

Direct Slack API integration for Lambda Function URLs.
"""

import json
import logging
import os
import hmac
import hashlib
from typing import Dict, Any
from urllib.request import Request, urlopen

import boto3

from bedrock_client import BedrockClient
from utils import setup_logging, load_config

logger = setup_logging(__name__)

# Initialize Bedrock client
config = load_config()
bedrock_client = BedrockClient(config)


def verify_slack_signature(event: Dict[str, Any]) -> bool:
    """
    Verify request is from Slack.

    Args:
        event: Lambda event

    Returns:
        True if signature is valid
    """
    try:
        slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "")

        # Get signature from headers
        headers = event.get("headers", {})
        slack_signature = headers.get("x-slack-signature", "")
        slack_request_timestamp = headers.get("x-slack-request-timestamp", "")

        if not slack_signature or not slack_request_timestamp:
            return False

        # Get body
        body = event.get("body", "")

        # Create signature
        sig_basestring = f"v0:{slack_request_timestamp}:{body}"
        my_signature = "v0=" + hmac.new(
            slack_signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(my_signature, slack_signature)

    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False


def send_slack_message(channel: str, text: str, thread_ts: str = None):
    """
    Send message to Slack using Web API.

    Args:
        channel: Channel ID
        text: Message text
        thread_ts: Thread timestamp (for replies)
    """
    try:
        bot_token = os.environ.get("SLACK_BOT_TOKEN")

        payload = {
            "channel": channel,
            "text": text
        }

        if thread_ts:
            payload["thread_ts"] = thread_ts

        request = Request(
            "https://slack.com/api/chat.postMessage",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json"
            }
        )

        response = urlopen(request, timeout=10)
        result = json.loads(response.read().decode())

        if not result.get("ok"):
            logger.error(f"Slack API error: {result}")

    except Exception as e:
        logger.error(f"Error sending Slack message: {e}")


def process_question(question: str) -> str:
    """
    Process user question with Bedrock.

    Args:
        question: User's question

    Returns:
        AI response text
    """
    try:
        prompt = f"""You are an AWS expert assistant helping users with AWS questions.

User Question: {question}

Provide a helpful, accurate answer. Keep answers concise but complete. Use bullet points for clarity.
"""

        answer = bedrock_client.get_completion(prompt)
        return answer

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return f"Sorry, I encountered an error: {str(e)}"


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

        # Parse body
        body_str = event.get("body", "{}")
        if isinstance(body_str, str):
            body = json.loads(body_str)
        else:
            body = body_str

        # Handle Slack URL verification challenge
        if "challenge" in body:
            logger.info(f"Handling challenge: {body['challenge']}")
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"challenge": body["challenge"]})
            }

        # Handle Slack event
        event_data = body.get("event", {})
        event_type = event_data.get("type")

        logger.info(f"Event type: {event_type}")

        # Handle app_mention
        if event_type == "app_mention":
            text = event_data.get("text", "")
            channel = event_data.get("channel")
            thread_ts = event_data.get("ts")
            user = event_data.get("user")

            # Remove bot mention
            bot_id = body.get("authorizations", [{}])[0].get("user_id", "")
            if bot_id:
                text = text.replace(f"<@{bot_id}>", "").strip()

            logger.info(f"Question from {user}: {text}")

            # Send thinking message
            send_slack_message(channel, "🤔 Let me think about that...", thread_ts)

            # Get AI response
            answer = process_question(text)

            # Send answer
            send_slack_message(channel, answer, thread_ts)

        # Return success
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True})
        }

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}", exc_info=True)
        return {
            "statusCode": 200,  # Return 200 to avoid retries
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": False, "error": str(e)})
        }


# Local testing
if __name__ == "__main__":
    # Test challenge
    test_event = {
        "body": json.dumps({"challenge": "test123"}),
        "headers": {}
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
