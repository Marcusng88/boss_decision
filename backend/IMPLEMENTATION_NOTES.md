# Document Processing Pipeline - Implementation Notes

## Current Issue: 504 Gateway Timeout

### What Happened:
The `ilmu.ai` API (Zhipu GLM provider) is returning **504 Gateway Timeout** errors:
```
ilmu.ai | 504: Gateway time-out
Host: api.ilmu.ai - Error
```

This is an **infrastructure issue** with the ilmu.ai service, NOT a code problem.

---

## Fixes Applied:

### 1. Extended Timeout Configuration
- **Total timeout**: 120 seconds (for vision model processing)
- **Connect timeout**: 30 seconds
- **Max retries**: 3 automatic retries

### 2. Exponential Backoff Retry Logic
- Attempts: 3 tries with 2s, 4s, 8s delays
- Detects 504/timeout errors specifically
- Logs each retry attempt clearly

### 3. Better Error Handling
- Distinguishes timeout errors from other failures
- Provides clear diagnostic messages
- Explains that 504 is an API infrastructure issue

---

## Options Moving Forward:

### Option A: Wait for ilmu.ai to recover
- The retry logic will handle temporary outages
- If API recovers, everything will work automatically

### Option B: Switch back to Google Gemini (Recommended)
Your original code used Google Gemini and it was working perfectly. We can revert to that:

```python
# In .env, add:
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-flash-lite

# Then use your original document_service.py
```

### Option C: Implement Multi-Provider Fallback with LangChain

---

## LangChain Implementation (Option C)

### Why LangChain?

LangChain provides:
1. **Unified interface** for multiple AI providers (Gemini, OpenAI, Zhipu, etc.)
2. **Automatic fallback** - if one provider fails, try another
3. **Document loaders** - standardized document processing
4. **Retry mechanisms** - built-in exponential backoff
5. **Streaming support** - for large documents
6. **Prompt templates** - reusable prompts
7. **Output parsers** - structured JSON parsing

### Architecture with LangChain:

```
┌─────────────────────────────────────────────────────────┐
│  Step 1: Document Ingestion (LangChain Loaders)         │
├─────────────────────────────────────────────────────────┤
│  - ImageLoader (for images)                              │
│  - PyPDFLoader (for PDFs)                                │
│  - Docx2txtLoader (for DOCX)                             │
│  - TextLoader (for TXT/MD)                               │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  Step 2: AI Extraction (Multi-Provider Chain)           │
├─────────────────────────────────────────────────────────┤
│  Primary: Google Gemini (fast, good vision)              │
│  Fallback 1: Zhipu GLM (if Gemini fails)                 │
│  Fallback 2: OpenAI GPT-4 Vision (if both fail)          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  Step 3: Structured Output Parsing                      │
├─────────────────────────────────────────────────────────┤
│  - PydanticOutputParser (validates JSON structure)       │
│  - Auto-retry if invalid format                          │
│  - Type checking (document_type, entities, etc.)         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  Step 4: Database Query Chain (existing data check)     │
├─────────────────────────────────────────────────────────┤
│  - Query employee table for matching records             │
│  - Query hr_record for period conflicts                  │
│  - Return existing data context                          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  Step 5: SQL Generation Chain (with context)            │
├─────────────────────────────────────────────────────────┤
│  - AI generates UPSERT vs INSERT based on existing data  │
│  - Validates SQL syntax                                  │
│  - Includes ai_justification with details                │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  Step 6: Database Execution                             │
├─────────────────────────────────────────────────────────┤
│  - Execute SQL with transaction support                  │
│  - Rollback on failure                                   │
│  - Return success/failure status                         │
└─────────────────────────────────────────────────────────┘
```

### Example LangChain Code:

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatGoogleGenerativeAI, ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.callbacks import get_openai_callback
from pydantic import BaseModel, Field

# Define structured output
class DocumentExtraction(BaseModel):
    document_type: str = Field(description="Type of document")
    department: str = Field(description="Department")
    entities: list = Field(description="Extracted entities")
    confidence: float = Field(description="Confidence score")

# Multi-provider with fallback
def get_llm_with_fallback():
    primary = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        timeout=60
    )
    
    fallback = ChatOpenAI(
        model="gpt-4-vision-preview",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        timeout=60
    )
    
    # Return primary with fallback
    return primary.with_fallbacks([fallback])

# Create extraction chain
parser = PydanticOutputParser(pydantic_object=DocumentExtraction)
prompt = PromptTemplate(
    template="Extract data from this document...\n{format_instructions}",
    input_variables=[],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

chain = LLMChain(llm=get_llm_with_fallback(), prompt=prompt)

# Execute with automatic retries and fallback
result = chain.run()
parsed = parser.parse(result)
```

### Benefits of LangChain Approach:

1. **Reliability**: Automatic fallback if one provider fails
2. **Maintainability**: Standardized interfaces across providers
3. **Extensibility**: Easy to add new providers or steps
4. **Observability**: Built-in tracing and logging
5. **Cost optimization**: Track token usage across providers
6. **Type safety**: Pydantic models validate structure

---

## Immediate Recommendation:

**Right now, do this:**

1. **Try uploading again** - The retry logic might work if ilmu.ai recovers
2. **If still fails**, switch back to Google Gemini temporarily:
   ```bash
   # In .env
   GOOGLE_API_KEY=your_key
   LLM_MODEL=gemini-2.5-flash-lite
   ```
3. **Implement LangChain properly** in next iteration for production robustness

The current implementation will work once the ilmu.ai API recovers, but for production, a multi-provider LangChain setup is the right architecture.
