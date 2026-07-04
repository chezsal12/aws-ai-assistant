# Quick Deployment Guide - Phase 1

**Goal**: Get the basic Slack bot working in 15 minutes

---

## Step 1: Create Slack App (5 minutes)

### 1.1 Create App
1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. App Name: `AWS Assistant`
4. Pick your workspace
5. Click **Create App**

### 1.2 Configure Bot Token Scopes
1. In left sidebar, click **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Click **"Add an OAuth Scope"** and add:
   - `app_mentions:read`
   - `chat:write`
   - `channels:history`
   - `groups:history`
   - `im:history`
   - `mpim:history`

### 1.3 Install App to Workspace
1. Scroll up on same page
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. **Copy the "Bot User OAuth Token"** (starts with `xoxb-`)
   - Save this - you'll need it for Lambda!

### 1.4 Get Signing Secret
1. In left sidebar, click **"Basic Information"**
2. Scroll to **"App Credentials"**
3. **Copy the "Signing Secret"**
   - Save this too!

---

## Step 2: Create IAM Role (2 minutes)

```bash
# Create trust policy
cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name AWSAssistantRole \
  --assume-role-policy-document file:///tmp/trust-policy.json

# Attach basic Lambda execution policy
aws iam attach-role-policy \
  --role-name AWSAssistantRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Attach Bedrock access policy
cat > /tmp/bedrock-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name AWSAssistantRole \
  --policy-name BedrockAccess \
  --policy-document file:///tmp/bedrock-policy.json

# Wait for role to propagate
sleep 10
```

---

## Step 3: Package and Deploy Lambda (5 minutes)

```bash
cd ~/aws-ai-assistant

# Install dependencies
cd src
pip install -r ../requirements.txt -t . --quiet

# Package Lambda
zip -r ../function.zip . -q
cd ..

# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create Lambda function
aws lambda create-function \
  --function-name aws-assistant \
  --runtime python3.12 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/AWSAssistantRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{
    SLACK_BOT_TOKEN=YOUR_XOXB_TOKEN_HERE,
    SLACK_SIGNING_SECRET=YOUR_SIGNING_SECRET_HERE,
    BEDROCK_REGION=us-east-1,
    LOG_LEVEL=INFO
  }"

# IMPORTANT: Replace YOUR_XOXB_TOKEN_HERE and YOUR_SIGNING_SECRET_HERE
# with the values you saved from Step 1!

# Or update after creation:
aws lambda update-function-configuration \
  --function-name aws-assistant \
  --environment Variables="{
    SLACK_BOT_TOKEN=xoxb-paste-your-token-here,
    SLACK_SIGNING_SECRET=paste-your-secret-here,
    BEDROCK_REGION=us-east-1,
    LOG_LEVEL=INFO
  }"
```

---

## Step 4: Create API Gateway (3 minutes)

```bash
# Create Lambda function URL (simpler than API Gateway)
aws lambda create-function-url-config \
  --function-name aws-assistant \
  --auth-type NONE

# Grant public invoke permission
aws lambda add-permission \
  --function-name aws-assistant \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE

# Get the function URL
FUNCTION_URL=$(aws lambda get-function-url-config \
  --function-name aws-assistant \
  --query 'FunctionUrl' \
  --output text)

echo "Your Function URL is: ${FUNCTION_URL}"
echo "Copy this URL - you'll need it for Slack!"
```

---

## Step 5: Configure Slack Events (2 minutes)

### 5.1 Set Request URL
1. Go back to https://api.slack.com/apps
2. Click your **AWS Assistant** app
3. In left sidebar, click **"Event Subscriptions"**
4. Toggle **"Enable Events"** to ON
5. In **"Request URL"** field, paste your Function URL from Step 4
   - Should look like: `https://abc123.lambda-url.us-east-1.on.aws/`
6. Wait for the checkmark ✓ (it verifies the URL)
7. Scroll down to **"Subscribe to bot events"**
8. Click **"Add Bot User Event"** and add:
   - `app_mention`
   - `message.channels`
9. Click **"Save Changes"**

### 5.2 Reinstall App (if needed)
If Slack prompts you to reinstall:
1. Click the banner at top
2. Click **"reinstall your app"**

---

## Step 6: Test It! 🎉

### 6.1 Invite Bot to Channel
1. In Slack, go to any channel
2. Type: `/invite @AWS Assistant`

### 6.2 Ask a Question
```
@AWS Assistant What is AWS Lambda?
```

You should see:
- "🤔 Let me think about that..."
- Then the AI response!

### 6.3 Troubleshooting

**If bot doesn't respond:**

Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/aws-assistant --follow
```

**Common issues:**
- **"Invalid token"**: Check SLACK_BOT_TOKEN in Lambda env vars
- **"Verification failed"**: Check SLACK_SIGNING_SECRET
- **"Bedrock access denied"**: Verify IAM role has Bedrock permissions
- **Bot not responding**: Make sure you @mentioned the bot

---

## Step 7: Verify Bedrock Access

```bash
# Test Bedrock access
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude-3-5-sonnet`)].[modelId]' \
  --output text
```

If you see model IDs, you're good!

If not, enable Bedrock model access:
1. Go to https://console.aws.amazon.com/bedrock/home#/modelaccess
2. Click **"Manage model access"**
3. Enable **"Claude Sonnet 4.6 v2"**
4. Click **"Save changes"**

---

## 🎉 Success Criteria

✅ Slack bot responds to @mentions  
✅ Bot uses Claude to answer questions  
✅ Responses appear in threads  
✅ CloudWatch logs show successful invocations  

---

## Next Steps

Once working, you can:
1. **Continue to Phase 2** - Add AWS resource analysis
2. **Customize responses** - Edit `src/lambda_function.py`
3. **Add more commands** - See `@slack_app.command()` decorator

---

## Quick Commands Reference

```bash
# View logs
aws logs tail /aws/lambda/aws-assistant --follow

# Update code
cd ~/aws-ai-assistant/src
zip -r ../function.zip . -q
cd ..
aws lambda update-function-code \
  --function-name aws-assistant \
  --zip-file fileb://function.zip

# Update environment variables
aws lambda update-function-configuration \
  --function-name aws-assistant \
  --environment Variables="{SLACK_BOT_TOKEN=...,SLACK_SIGNING_SECRET=...,BEDROCK_REGION=us-east-1,LOG_LEVEL=DEBUG}"

# Delete everything (cleanup)
aws lambda delete-function --function-name aws-assistant
aws iam detach-role-policy --role-name AWSAssistantRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role-policy --role-name AWSAssistantRole --policy-name BedrockAccess
aws iam delete-role --role-name AWSAssistantRole
```

---

**Ready to deploy? Let's do it!** 🚀
