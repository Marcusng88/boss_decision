# ZhipuAI GLM Usage Guide (智谱AI)

Complete guide for using ZhipuAI GLM models in the AI Boss Decision Engine.

---

## What is GLM?

**GLM (General Language Model)** by ZhipuAI (智谱AI) is a powerful Chinese language model series comparable to GPT-4. We use it for:
- Multi-agent reasoning
- Performance analysis
- Decision synthesis
- OCR text extraction (GLM-4V)

---

## Setup

### 1. Install Dependencies

Already included in `requirements.txt`:
```bash
pip install zhipuai==2.1.5.20241022
```

### 2. Get API Key

1. Go to [https://open.bigmodel.cn/](https://open.bigmodel.cn/)
2. Sign up / log in
3. Navigate to **API Keys**
4. Create new API key
5. Copy the key

### 3. Add to `.env`

```bash
ZHIPUAI_API_KEY=your_api_key_here.xxxxxxxxxxxxx
GLM_MODEL=glm-4-plus
GLM_TEMPERATURE=0.7
```

---

## Available Models

| Model | Purpose | Speed | Cost | When to Use |
|-------|---------|-------|------|-------------|
| **glm-4-plus** | Complex reasoning | Slower | Higher | Multi-agent synthesis, strategic decisions |
| **glm-4** | General tasks | Medium | Medium | Most agent analysis tasks |
| **glm-4-flash** | Simple queries | Fast | Lower | Quick lookups, simple classification |
| **glm-4v-plus** | Vision (OCR) | Medium | Higher | PDF/image text extraction (Kai Haung) |

**Recommendation**: Use `glm-4-plus` for all agents. It's the most capable.

---

## Usage Patterns

### Pattern 1: Simple Chat (Direct API)

```python
from llm_client import GLMClient

# Initialize client
glm = GLMClient(model="glm-4-plus")

# Simple chat
messages = [
    {"role": "system", "content": "You are an HR specialist."},
    {"role": "user", "content": "Analyze this performance: score 2.1/5, 2 warnings"}
]

response = glm.chat(messages)
print(response)
```

---

### Pattern 2: Structured Chat (Recommended for Agents)

```python
from llm_client import GLMClient

glm = GLMClient(model="glm-4-plus")

# Structured prompt + context
response = glm.structured_chat(
    system_prompt="""You are an HR analyst.
    
Output format:
**Findings:**
- [finding 1]
- [finding 2]

**Recommendation:**
[action to take]
""",
    user_input="Analyze employee performance: score declining from 2.8 to 2.0",
    context={
        "hr_records": [...],  # Optional: inject data
        "policies": [...]
    }
)

print(response)
```

**Why use this?**
- Cleaner code
- Easier to inject context
- Automatic message formatting

---

### Pattern 3: Streaming (For Long Responses)

```python
from llm_client import GLMClient

glm = GLMClient(model="glm-4-plus")

messages = [
    {"role": "user", "content": "Write a detailed analysis of..."}
]

# Stream response
for chunk in glm.chat_stream(messages):
    print(chunk, end='', flush=True)
```

---

## Agent Integration Examples

### HR Agent (Yihao)

```python
from llm_client import GLMClient
from .base_agent import BaseAgent, AgentInsight

class HRAgent(BaseAgent):
    
    async def analyze_with_glm(self, evidence, query):
        glm = GLMClient(model="glm-4-plus")
        
        # Format HR records
        hr_data = self._format_hr_records(evidence)
        
        # System prompt
        system_prompt = """You are an HR performance analyst.

Analyze employee performance data and identify:
1. Performance trends (improving/declining)
2. Legal risks (PIP requirements, termination policies)
3. Actionable recommendations

Output format:
**Findings:**
- [Key finding with numbers]
- [Trend analysis]

**Risks:**
- [Legal/compliance risk]
- [HR risk]

**Recommendation:**
[One clear action]
"""
        
        # Get analysis
        response = glm.structured_chat(
            system_prompt=system_prompt,
            user_input=f"Performance Data:\n{hr_data}\n\nQuestion: {query}"
        )
        
        # Parse response
        findings, risks, recommendation = self._parse_glm_response(response)
        
        return AgentInsight(
            agent_name="HR",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.90,
            evidence_used=evidence
        )
```

---

### Sales Agent (Jialih)

```python
from llm_client import GLMClient

class SalesAgent(BaseAgent):
    
    async def analyze_with_glm(self, evidence, query):
        glm = GLMClient(model="glm-4-plus")
        
        # Format sales data
        sales_data = self._format_sales_records(evidence)
        
        system_prompt = """You are a sales performance analyst.

Analyze revenue data and assess:
1. Total revenue contribution
2. Performance vs team benchmarks (good: RM 200k+/quarter)
3. Pipeline health

Output format:
**Findings:**
- Total revenue: RM X
- Trend: [improving/declining/stable]
- Pipeline: [X active deals]

**Risks:**
- [Revenue risk]
- [Pipeline risk]

**Recommendation:**
[Performance assessment]
"""
        
        response = glm.structured_chat(
            system_prompt=system_prompt,
            user_input=f"Sales Data:\n{sales_data}\n\nQuestion: {query}"
        )
        
        return self._parse_response(response)
```

---

### Manager Agent (Marcus)

```python
from llm_client import GLMClient

class ManagerAgent:
    
    def synthesize_with_glm(self, agent_insights, query, persona='balanced'):
        glm = GLMClient(model="glm-4-plus")
        
        # Combine all agent insights
        agent_summaries = []
        for insight in agent_insights:
            agent_summaries.append(f"""
**{insight.agent_name} Agent:**
- Findings: {', '.join(insight.findings)}
- Recommendation: {insight.recommendation}
""")
        
        # Persona instructions
        persona_prompt = {
            'conservative': "Prioritize risk mitigation, legal compliance, and cautious approach.",
            'aggressive': "Prioritize speed, decisiveness, and bold action.",
            'balanced': "Balance all perspectives, consider long-term impacts."
        }
        
        system_prompt = f"""You are a Manager Decision Agent.

Your task:
1. Review all specialist agent recommendations
2. Apply {persona.upper()} decision-making style
3. Synthesize into ONE clear decision

{persona_prompt[persona]}

Output format:
**Final Recommendation:**
[Clear decision statement]

**Risk Level:**
[Low/Medium/High]

**Rationale:**
[Explain how you synthesized agent views]
"""
        
        response = glm.structured_chat(
            system_prompt=system_prompt,
            user_input=f"Query: {query}\n\n{chr(10).join(agent_summaries)}"
        )
        
        return self._parse_decision(response)
```

---

## OCR Usage (Kai Haung - Vision Model)

### GLM-4V for PDF/Image Text Extraction

```python
from llm_client import GLMClient
import base64

# Initialize vision model
glm = GLMClient(model="glm-4v-plus")

# Read image file
with open("performance_review.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Extract structured data
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": """Extract text from this performance review image.

Output format:
- Employee Name: [name]
- Period: [quarter/year]
- Performance Score: [X/5]
- Summary: [text]
"""
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}"
                }
            }
        ]
    }
]

response = glm.chat(messages)
print(response)
```

### OCR Best Practices

1. **Use glm-4v-plus** for vision tasks
2. **Provide clear instructions** in text prompt
3. **Specify output format** (JSON, markdown, etc.)
4. **Handle OCR errors** with try-except

---

## Prompt Engineering Tips

### ✅ Good Prompts

```python
# GOOD: Specific, structured, clear output format
"""You are an HR analyst reviewing performance data.

Task: Identify performance trends and risks.

Data:
{data}

Output format:
**Findings:**
- [finding 1 with numbers]
- [finding 2 with trend]

**Risks:**
- [risk 1]

**Recommendation:**
[action]
"""
```

### ❌ Bad Prompts

```python
# BAD: Vague, no structure, unclear output
"""Analyze this employee's performance and tell me what to do."""
```

### Key Principles

1. **Be specific**: "Analyze performance trends over 3 quarters" > "Analyze performance"
2. **Provide examples**: Show the format you want
3. **Use structure**: Bullet points, sections, headers
4. **Include context**: Numbers, benchmarks, policies
5. **Request reasoning**: "Explain why..." gets better answers

---

## Error Handling

### Pattern: Graceful Fallback

```python
async def analyze_with_glm(self, evidence, query):
    try:
        glm = GLMClient(model="glm-4-plus")
        response = glm.structured_chat(...)
        return self._parse_response(response)
        
    except Exception as e:
        print(f"GLM failed: {e}. Using rule-based fallback.")
        return self.analyze_rule_based(evidence, query)
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ValueError: ZHIPUAI_API_KEY not set` | Missing API key | Add to `.env` |
| `APIError: 401` | Invalid API key | Check key format |
| `APIError: 429` | Rate limit | Add retry logic |
| `APIError: 400` | Bad request | Check message format |

---

## Cost Optimization

### Tips to Reduce API Costs

1. **Use glm-4-flash for simple tasks**
   ```python
   # Simple classification -> use flash
   glm = GLMClient(model="glm-4-flash")
   ```

2. **Cache common queries** (don't re-analyze same data)
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def analyze_employee(employee_id):
       # Result cached for repeated calls
       return glm.chat(...)
   ```

3. **Limit max_tokens** for short responses
   ```python
   response = glm.chat(messages, max_tokens=500)  # vs default 2000
   ```

4. **Use rule-based for obvious cases**
   ```python
   if performance_score > 4.5:
       return "High performer - no GLM needed"
   else:
       return glm.analyze(...)
   ```

---

## Testing Your Agent

### Quick Test Script

```python
# test_hr_agent.py
from agents.hr_agent import HRAgent
from db import DatabaseService

async def test_hr_agent():
    db = DatabaseService()
    agent = HRAgent(db)
    
    # Get real data
    evidence = await agent.retrieve_evidence(
        query="Should we fire employee 1023?",
        context={"target_type": "employee", "target_id": 1023}
    )
    
    # Analyze with GLM
    result = await agent.analyze_with_glm(evidence, "Should we fire employee 1023?")
    
    print("Agent:", result.agent_name)
    print("Findings:", result.findings)
    print("Risks:", result.risks)
    print("Recommendation:", result.recommendation)
    print("Confidence:", result.confidence)

# Run test
import asyncio
asyncio.run(test_hr_agent())
```

---

## Debugging

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("zhipuai")
logger.setLevel(logging.DEBUG)

# Now GLM calls will print request/response
```

### Print GLM Responses

```python
response = glm.chat(messages)
print(f"GLM Response:\n{response}")  # See what GLM returns
```

### Check Token Usage

```python
response = client.client.chat.completions.create(
    model="glm-4-plus",
    messages=messages
)

print(f"Tokens used: {response.usage.total_tokens}")
print(f"Cost estimate: ~${response.usage.total_tokens * 0.0001}")  # Rough estimate
```

---

## Next Steps for Team

### Yihao (HR + Legal Agents)
1. Get ZhipuAI API key from [https://open.bigmodel.cn/](https://open.bigmodel.cn/)
2. Add to `.env`: `ZHIPUAI_API_KEY=xxx`
3. In `hr_agent.py`: rename `analyze_with_glm` to `analyze`
4. Test with: `python -c "from agents.hr_agent import HRAgent; ..."`

### Jialih (Sales + Marketing + Supply Chain Agents)
1. Same API key setup as Yihao
2. Copy GLM pattern from `sales_agent.py` (already has `analyze_with_glm`)
3. Create `marketing_agent.py` and `supply_chain_agent.py` using same pattern
4. Test each agent individually

### Marcus (Manager Agent)
1. Same API key setup
2. Use `_synthesize_with_glm` method in `manager_agent.py`
3. Test with different personas: conservative, balanced, aggressive
4. Compare GLM vs rule-based synthesis

### Kai Haung (OCR Pipeline)
1. Use `glm-4v-plus` model (vision)
2. Create file upload endpoint in FastAPI
3. Process images/PDFs → extract text → insert into database
4. Link to `source_document` table

---

## Resources

- **ZhipuAI Docs**: [https://open.bigmodel.cn/dev/api](https://open.bigmodel.cn/dev/api)
- **Python SDK**: [https://github.com/zhipuai/zhipuai-sdk-python](https://github.com/zhipuai/zhipuai-sdk-python)
- **Model Pricing**: [https://open.bigmodel.cn/pricing](https://open.bigmodel.cn/pricing)
- **API Playground**: [https://open.bigmodel.cn/playground](https://open.bigmodel.cn/playground)

---

## FAQ

### Q: Can I use English prompts with GLM?
**A:** Yes! GLM supports both English and Chinese. Use English for consistency with your code.

### Q: Which model should I use?
**A:** Use `glm-4-plus` for all agents. It's the most capable and worth the extra cost for accuracy.

### Q: What if GLM is slow?
**A:** GLM-4-plus takes 2-5 seconds. If too slow, use `glm-4-flash` for simple tasks or implement caching.

### Q: How do I handle rate limits?
**A:** Add retry logic with exponential backoff. Or upgrade your API tier on ZhipuAI platform.

### Q: Can I use multiple models at once?
**A:** Yes! Create different GLMClient instances with different models for different agents.

---

**Happy coding with GLM! 🚀**
