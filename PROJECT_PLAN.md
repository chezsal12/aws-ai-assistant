# AWS AI Assistant - Project Plan

**Date Created**: 2026-07-02 (11:45 PM)  
**Status**: Planning Phase  
**Estimated Time**: 4-5 hours implementation

---

## 🎯 Project Vision

Build an intelligent AWS assistant that combines RAG (documentation search) with real-time infrastructure analysis. Users can ask questions in Slack and get answers backed by both AWS documentation and their actual resource state.

---

## 💡 Core Capabilities

### 1. Documentation Q&A (RAG)
- **Input**: "What's the best practice for Lambda concurrency?"
- **Process**: Search AWS docs → Generate answer with citations
- **Output**: Answer + links to relevant AWS documentation

### 2. Infrastructure Analysis
- **Input**: "Why is my Lambda function timing out?"
- **Process**: Analyze YOUR Lambda functions → Check metrics → Compare to best practices
- **Output**: Specific recommendations for YOUR resources

### 3. Cost Intelligence (Integration)
- **Input**: "Show me my biggest cost spikes this week"
- **Process**: Query Cost Anomaly Detective data
- **Output**: Cost analysis with AI explanations

### 4. Optimization Recommendations (Integration)
- **Input**: "What can I optimize right now?"
- **Process**: Query Resource Right-Sizer recommendations
- **Output**: Prioritized list with savings potential

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│                      (Slack Bot)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway + Lambda                       │
│                   (Chat Handler)                            │
└────────────┬───────────────────────────────┬────────────────┘
             │                               │
             ↓                               ↓
   ┌─────────────────────┐        ┌──────────────────────┐
   │   RAG Engine        │        │   AWS Analyzer       │
   │   (OpenSearch +     │        │   (Live Data)        │
   │    Bedrock)         │        │                      │
   │                     │        │   • CloudWatch       │
   │   • AWS Docs        │        │   • Cost Explorer    │
   │   • Embeddings      │        │   • Resource APIs    │
   │   • Vector Search   │        │                      │
   └──────────┬──────────┘        └──────────┬───────────┘
              │                              │
              └──────────────┬───────────────┘
                             ↓
                   ┌─────────────────────┐
                   │  Bedrock (Claude)   │
                   │  • Synthesize       │
                   │  • Generate answer  │
                   │  • Format response  │
                   └─────────┬───────────┘
                             │
                             ↓
                   ┌─────────────────────┐
                   │   DynamoDB          │
                   │   • Chat history    │
                   │   • User context    │
                   │   • Session state   │
                   └─────────────────────┘
```

---

## 🔧 Technical Stack

### Infrastructure
- **Chat Interface**: Slack Bot (via Bolt SDK)
- **API Gateway**: REST API for Slack events
- **Compute**: Lambda (Python 3.12)
- **Vector DB**: OpenSearch Serverless (for embeddings)
- **AI Model**: Bedrock (Claude Sonnet 4.6)
- **Storage**: DynamoDB (chat history), S3 (cached docs)
- **Embeddings**: Bedrock (Titan Embeddings)

### Dependencies
```python
boto3>=1.34.0              # AWS SDK
slack-bolt>=1.18.0         # Slack SDK
opensearch-py>=2.3.0       # OpenSearch client
langchain>=0.1.0           # RAG orchestration
pyyaml>=6.0.1             # Config
requests>=2.31.0           # HTTP client
```

---

## 📦 Component Breakdown

### 1. Chat Handler (`lambda_function.py`)
- Receives Slack events
- Routes to appropriate handler (RAG vs Analysis)
- Manages conversation context
- Formats responses for Slack

### 2. RAG Engine (`rag_engine.py`)
- Queries OpenSearch for relevant docs
- Generates embeddings for user questions
- Retrieves top-k similar documents
- Passes context to Claude

### 3. AWS Analyzer (`aws_analyzer.py`)
- Discovers user's resources
- Collects CloudWatch metrics
- Queries Cost Detective / Right-Sizer data
- Provides current state to Claude

### 4. Response Generator (`response_generator.py`)
- Takes RAG results + AWS data
- Prompts Claude for synthesis
- Formats as Slack blocks
- Adds citations and action buttons

### 5. Document Ingestion (`ingest_docs.py`)
- Downloads AWS documentation
- Chunks into semantic segments
- Generates embeddings
- Stores in OpenSearch
- **(One-time setup, can be pre-built)**

---

## 🎨 User Experience Examples

### Example 1: Documentation Question

**User**: `@aws-assistant What's the difference between Lambda provisioned concurrency and reserved concurrency?`

**Assistant**:
```
📚 Based on AWS Documentation:

Provisioned Concurrency vs Reserved Concurrency:

• Provisioned Concurrency: Pre-initializes function instances to 
  eliminate cold starts. You pay for provisioned capacity even when 
  not in use. Best for latency-sensitive workloads.

• Reserved Concurrency: Sets a maximum limit on concurrent executions 
  for a function. Guarantees that many instances can run, but doesn't 
  pre-warm them. Best for preventing runaway scaling.

Key Difference: Provisioned is about performance (warm instances), 
Reserved is about control (scaling limits).

📖 Sources:
• Lambda Concurrency Best Practices
• Managing Lambda Concurrency

💡 Want me to check your Lambda functions' concurrency settings?
```

### Example 2: Infrastructure Analysis

**User**: `@aws-assistant Why is my data-processor Lambda function slow?`

**Assistant**:
```
🔍 Analyzing your Lambda function: data-processor

Found Issues:
1. 🔴 Memory under-provisioned
   • Allocated: 512 MB
   • P95 usage: 480 MB (94% utilized)
   • Recommendation: Increase to 1024 MB
   • Expected improvement: 40% faster, minimal cost increase

2. 🟡 Cold start issues
   • Average duration: 850ms
   • Cold start duration: 3.2s
   • Invocation pattern: Bursty (10 invocations/minute)
   • Recommendation: Enable Provisioned Concurrency (2 instances)

3. 🟢 Timeout is appropriate
   • Current: 30s
   • P99 duration: 4.2s
   • Status: No change needed

💰 Cost Impact:
• Memory increase: +$5/month
• Provisioned Concurrency: +$35/month
• Performance gain: 70% faster P95 latency

📖 Related Documentation:
• Lambda Performance Optimization
• Right-sizing Lambda Memory

[Apply Memory Fix] [View Detailed Metrics]
```

### Example 3: Cost Intelligence

**User**: `@aws-assistant What caused my cost spike yesterday?`

**Assistant**:
```
💰 Cost Spike Analysis - July 1, 2026

Total Spike: $450 (+180%)

Top Anomaly:
🚨 Amazon RDS - prod-database-1
• Cost increased from $120 to $380 (+217%)
• Root Cause: Database instance changed from db.t3.large 
  to db.r5.2xlarge at 2:15 PM by user john.doe@company.com
• Reason (from CloudTrail): "Performance testing"
• Recommendation: Revert to db.t3.large or use Aurora Serverless

[View Full Report] [Create Jira Ticket]

💡 Want me to check if this change is still needed?
```

---

## 📋 Implementation Phases

### Phase 1: Basic Chat (2 hours)
- ✅ Slack bot setup
- ✅ Lambda + API Gateway
- ✅ Basic Bedrock integration (no RAG yet)
- ✅ Simple Q&A (Claude answers directly)

**Deliverable**: Working Slack bot that answers AWS questions using Claude's training data

### Phase 2: AWS Analysis Integration (1 hour)
- ✅ Connect to CloudWatch
- ✅ Resource discovery (EC2, Lambda, RDS)
- ✅ Pull data from Cost Detective DynamoDB
- ✅ Pull data from Right-Sizer DynamoDB

**Deliverable**: Bot can analyze YOUR actual AWS resources

### Phase 3: RAG Engine (2 hours)
- ✅ OpenSearch Serverless setup
- ✅ Document ingestion (AWS docs)
- ✅ Embedding generation (Titan)
- ✅ Vector search implementation
- ✅ Citation formatting

**Deliverable**: Bot answers using official AWS documentation with sources

### Phase 4: Polish (30 minutes)
- ✅ Slack formatting (blocks, buttons)
- ✅ Error handling
- ✅ Rate limiting
- ✅ Help commands
- ✅ README + docs

**Deliverable**: Production-ready, publish to GitHub

---

## 🚀 Quick Start (Tomorrow)

### Step 1: Architecture Review (30 min)
Review this plan, make any adjustments

### Step 2: Start with Phase 1 (2 hours)
Build basic Slack bot without RAG - get it working end-to-end

### Step 3: Add Phase 2 (1 hour)
Integrate with existing Cost Detective / Right-Sizer

### Step 4: Add Phase 3 (2 hours)
Implement RAG with OpenSearch

**Total Time**: ~5 hours for full implementation

---

## 🎯 Success Criteria

✅ User can ask AWS questions in Slack and get answers  
✅ Answers include citations to official AWS docs  
✅ Bot can analyze user's actual AWS resources  
✅ Integrates with Cost Detective and Right-Sizer  
✅ Responses formatted beautifully in Slack  
✅ Production-ready code, published to GitHub

---

## 💡 Optional Enhancements (Post-Launch)

- **Multi-account support**: Query across AWS Organization
- **Jira integration**: "Create a ticket for this recommendation"
- **Scheduled summaries**: Daily digest of cost/optimization updates
- **Custom knowledge base**: Ingest your internal runbooks
- **Voice interface**: Alexa skill for AWS queries
- **Teams/Discord support**: Beyond Slack

---

## 📊 Estimated Costs

**Development/Testing** (per month):
- Lambda invocations: ~$2
- Bedrock API calls: ~$20
- OpenSearch Serverless: ~$60 (1 OCU)
- DynamoDB: ~$1
- **Total: ~$85/month**

**Production** (100 queries/day):
- Lambda: ~$5
- Bedrock: ~$50
- OpenSearch: ~$60
- DynamoDB: ~$2
- **Total: ~$120/month**

**Value**: Saves hours of documentation searching, instant AWS insights

---

## 🔗 Related Projects

This integrates with:
1. **Cost Anomaly Detective**: Query cost spike data
2. **Resource Right-Sizer**: Query optimization recommendations

Together they form a complete "AWS AI Operations Suite"

---

## 📝 Notes for Tomorrow

- Start fresh with Phase 1 (basic bot)
- Don't get stuck on RAG complexity - add it last
- Test with real Slack workspace as you build
- OpenSearch Serverless takes 10-15 min to provision (plan for that)
- AWS docs ingestion can be pre-built dataset (save time)

---

**Good night! See you tomorrow for the build! 🚀**

---

## Quick Commands for Tomorrow

```bash
# Navigate to project
cd ~/aws-ai-assistant

# Start git
git init
git config user.email "chezsal@amazon.com"
git config user.name "Chezsal Kamaray"

# Create structure
mkdir -p src docs tests

# Begin implementation
# (Start with lambda_function.py - basic Slack handler)
```
