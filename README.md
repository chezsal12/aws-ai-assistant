# AWS AI Assistant 🤖

**Intelligent Slack bot powered by Amazon Bedrock + RAG**

Ask AWS questions in Slack and get answers backed by official documentation AND your actual infrastructure state. Combines retrieval-augmented generation (RAG) with real-time CloudWatch metrics, cost analysis, and optimization recommendations.

[![License: MIT-0](https://img.shields.io/badge/License-MIT--0-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20OpenSearch%20%7C%20Lambda-orange.svg)](https://aws.amazon.com/)

> **Note**: This is a sample project for demonstration purposes. Review and test thoroughly before using in production.

---

## 🌟 What Makes This Special?

**Traditional Documentation Search:**
- ❌ Google AWS docs, read 10 articles
- ❌ Generic answers, not specific to YOUR infrastructure
- ❌ No context about your resources
- ❌ Can't answer "why is MY Lambda slow?"

**AWS AI Assistant:**
- ✅ Ask in Slack: "Why is my Lambda slow?"
- ✅ AI analyzes YOUR actual Lambda functions + CloudWatch metrics
- ✅ Combines official AWS best practices with your specific situation
- ✅ Actionable recommendations: "Increase memory from 512MB to 1024MB - will cost $5/month, improve latency 40%"
- ✅ Citations to official AWS documentation

---

## 💬 Example Conversations

### Documentation Q&A
```
You: @aws-assistant What's the difference between Lambda provisioned 
     concurrency and reserved concurrency?

Bot: 📚 Based on AWS Documentation:

     **Provisioned Concurrency** pre-initializes function instances 
     to eliminate cold starts. You pay for provisioned capacity even 
     when not in use.

     **Reserved Concurrency** sets a maximum limit on concurrent 
     executions. Guarantees capacity but doesn't pre-warm instances.

     Key Difference: Provisioned = performance (warm instances), 
     Reserved = control (scaling limits)

     📖 Sources: Lambda Concurrency Best Practices

     💡 Want me to check your Lambda functions' concurrency settings?
```

### Infrastructure Analysis
```
You: @aws-assistant Why is my data-processor Lambda function slow?

Bot: 🔍 Analyzing function: data-processor

     Found Issues:
     1. 🔴 Memory under-provisioned
        • Allocated: 512 MB
        • P95 usage: 480 MB (94%)
        • Recommendation: Increase to 1024 MB
        • Impact: 40% faster, +$5/month

     2. 🟡 Cold start issues
        • Avg duration: 850ms
        • Cold start: 3.2s
        • Recommendation: Enable Provisioned Concurrency (2 instances)
        • Impact: +$35/month

     💰 Total Cost: +$40/month for 70% better P95 latency

     [Apply Memory Fix] [View Metrics]
```

### Cost Intelligence
```
You: @aws-assistant What caused my cost spike yesterday?

Bot: 💰 Cost Spike Analysis - July 2, 2026

     Spike: $450 (+180%)

     Root Cause:
     🚨 RDS prod-database-1
        • Changed from db.t3.large → db.r5.2xlarge
        • Time: 2:15 PM by john.doe@company.com
        • Reason: "Performance testing"

     💡 Recommendation: Revert or switch to Aurora Serverless

     [View Full Report] [Create Ticket]
```

---

## 🏗️ Architecture

```
Slack → API Gateway → Lambda (Chat Handler)
                         ↓
                    Bedrock (Claude 3.5)
                         ↓
              ┌──────────┴──────────┐
              │                     │
         RAG Engine            AWS Analyzer
         (OpenSearch)          (Live Data)
         • AWS docs            • CloudWatch
         • Embeddings          • Cost Explorer
         • Vector search       • Resources
              │                     │
              └──────────┬──────────┘
                         ↓
                   DynamoDB
                   (Chat history)
```

---

## 🚀 Quick Start

### Prerequisites

- AWS Account with Bedrock enabled
- Slack workspace with admin access
- AWS CLI configured
- Python 3.12+

### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "AWS Assistant"
4. Select your workspace
5. Navigate to **OAuth & Permissions**:
   - Add Bot Token Scopes:
     - `app_mentions:read`
     - `chat:write`
     - `commands`
   - Install app to workspace
   - Copy "Bot User OAuth Token" (starts with `xoxb-`)
6. Navigate to **Event Subscriptions**:
   - Enable Events
   - Request URL: (will set after Lambda deployment)
   - Subscribe to bot events:
     - `app_mention`
     - `message.channels`
7. Navigate to **App Home**:
   - Enable "Allow users to send Slash commands and messages"

### Step 2: Deploy Lambda Function

```bash
# Clone repository
git clone https://github.com/chezsal12/aws-ai-assistant.git
cd aws-ai-assistant

# Install dependencies
cd src
pip install -r ../requirements.txt -t .

# Package Lambda
zip -r ../function.zip .
cd ..

# Create Lambda function
aws lambda create-function \
  --function-name aws-assistant \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/AWSAssistantRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{
    SLACK_BOT_TOKEN=xoxb-your-token-here,
    SLACK_SIGNING_SECRET=your-signing-secret,
    BEDROCK_REGION=us-east-1,
    LOG_LEVEL=INFO
  }"
```

### Step 3: Create API Gateway

```bash
# Create REST API
aws apigatewayv2 create-api \
  --name aws-assistant-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:aws-assistant

# Get API endpoint
aws apigatewayv2 get-apis --query 'Items[?Name==`aws-assistant-api`].ApiEndpoint' --output text
```

### Step 4: Configure Slack Event URL

1. Copy API Gateway endpoint from Step 3
2. Go back to Slack App → **Event Subscriptions**
3. Set Request URL to: `https://YOUR_API_ENDPOINT/slack/events`
4. Wait for verification ✓

### Step 5: Test It!

In Slack:
```
@aws-assistant What is AWS Lambda?
```

---

## 📋 Features

### Current (Phase 1)
✅ Slack bot integration  
✅ Basic AWS Q&A powered by Bedrock  
✅ Natural language understanding  
✅ Threaded conversations  

### Coming Soon
⏳ RAG with AWS documentation (Phase 3)  
⏳ Real-time resource analysis (Phase 2)  
⏳ Cost Detective integration (Phase 2)  
⏳ Resource Optimizer integration (Phase 2)  
⏳ CloudWatch metrics analysis (Phase 2)  

---

## 🔧 Configuration

Set via Lambda environment variables:

```bash
# Required
SLACK_BOT_TOKEN=xoxb-...          # From Slack App OAuth
SLACK_SIGNING_SECRET=abc123...     # From Slack App Basic Info

# Bedrock
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-6
MAX_TOKENS=2000
TEMPERATURE=0.7

# Optional (for Phase 2/3)
OPENSEARCH_ENDPOINT=https://...
DYNAMODB_TABLE=aws-assistant-chats
COST_DETECTIVE_TABLE=cost-anomalies
OPTIMIZER_TABLE=optimizer-recommendations
```

---

## 💰 Cost Estimate

**Basic Usage** (100 questions/day):
- Lambda invocations: ~$3/month
- Bedrock API calls: ~$30/month
- API Gateway: ~$1/month
- **Total: ~$35/month**

**With RAG** (Phase 3):
- Add OpenSearch Serverless: +$60/month
- Add DynamoDB: +$2/month
- **Total: ~$100/month**

---

## 🛡️ Security Best Practices

- Store Slack tokens in AWS Secrets Manager (not Lambda env vars)
- Use IAM roles with least privilege
- Enable CloudWatch Logs encryption
- Validate Slack signatures on all requests
- Don't log sensitive user data

---

## 📚 Commands

- `@aws-assistant <question>` - Ask anything
- `/aws-help` - Show help guide
- `/aws-status` - Check assistant status

---

## 🤝 Integration with Other Tools

This assistant integrates with:
- **[Cost Anomaly Detective](https://github.com/chezsal12/aws-cost-anomaly-detective)** - Query cost spike data
- **[Resource Optimizer](https://github.com/chezsal12/aws-resource-optimizer)** - Get optimization recommendations

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 License

MIT-0 - See [LICENSE](LICENSE)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/chezsal12/aws-ai-assistant/issues)

---

**Built with ❤️ using Amazon Bedrock (Claude Sonnet 4.6)**