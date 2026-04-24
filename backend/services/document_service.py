import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import os
import mimetypes
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    from config import get_settings
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from config import get_settings


@dataclass
class DocumentServiceSettings:
    zhipu_api_key: Optional[str]
    zhipu_base_url: str = "https://api.ilmu.ai/v1"
    zhipu_model: str = "ilmu-glm-5.1"
    llm_temperature: float = 0.7


def load_document_settings() -> DocumentServiceSettings:
    try:
        app_settings = get_settings()
        return DocumentServiceSettings(
            zhipu_api_key=app_settings.zhipu_api_key,
            zhipu_base_url=app_settings.zhipu_base_url,
            zhipu_model=app_settings.zhipu_model,
            llm_temperature=app_settings.llm_temperature,
        )
    except Exception:
        backend_root = Path(__file__).resolve().parents[1]
        load_dotenv(dotenv_path=backend_root / ".env")
        temp_raw = os.getenv("LLM_TEMPERATURE", "0.7")
        try:
            temp = float(temp_raw)
        except ValueError:
            temp = 0.7
        return DocumentServiceSettings(
            zhipu_api_key=os.getenv("ZHIPU_API_KEY"),
            zhipu_base_url=os.getenv("ZHIPU_BASE_URL", "https://api.ilmu.ai/v1"),
            zhipu_model=os.getenv("ZHIPU_MODEL", "ilmu-glm-5.1"),
            llm_temperature=temp,
        )


ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".txt", ".md", ".rtf",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"
}

MIME_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".rtf": "application/rtf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}


def _extract_text_from_file(file_path: str) -> str:
    """Extract plain text from a supported file type."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages).strip()
        except Exception as e:
            raise Exception(f"PDF extraction failed: {e}")

    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs).strip()
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {e}")

    if ext in {".txt", ".md", ".rtf", ".doc"}:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Text file reading failed: {e}")

    if ext in IMAGE_EXTENSIONS:
        return f"[Image file: {path.name}. Visual content — text extraction not available for images.]"

    raise ValueError(f"Unsupported file extension for text extraction: {ext}")


class DocumentIngestor:
    EXTRACTION_PROMPT = """You are an enterprise document classification and information extraction system.

Your job:
1. Classify document with BOTH document_type AND department
2. Extract ALL structured business data you can see
3. Identify relationships between entities

=== CRITICAL: DOCUMENT_TYPE vs DEPARTMENT ===

DOCUMENT_TYPE = What the document IS (the format/template)
DEPARTMENT = Where it belongs organizationally

These are DIFFERENT! A payslip is document_type "Employee" but department "HR".

=== DOCUMENT TYPE (Use ONLY these exact values) ===

STRICTLY classify into ONE of these 9 types:

1. "HR Report" - Performance reviews, hiring reports, team evaluations
2. "Sales Log" - Sales deals, revenue tracking, customer deals
3. "Finance Report" - Financial statements, budgets, expense reports, invoices
4. "Marketing Report" - Campaign performance, ROI reports, ad metrics
5. "Supply Chain Log" - Inventory reports, procurement, vendor data
6. "Legal Policy" - Company policies, rules, regulations
7. "Legal Contract" - Employment contracts, vendor contracts, agreements
8. "Legal Case" - Employee legal issues, misconduct cases
9. "Employee" - INDIVIDUAL employee documents: payslips, offer letters, salary slips

=== CLASSIFICATION RULES (STRICT) ===

PAYSLIP / SALARY SLIP -> document_type: "Employee", department: "HR"
PERFORMANCE REVIEW -> document_type: "HR Report", department: "HR"
SALES DEAL/REVENUE -> document_type: "Sales Log", department: "Sales"
BUDGET/INVOICE -> document_type: "Finance Report", department: "Finance"
CAMPAIGN METRICS -> document_type: "Marketing Report", department: "Marketing"
INVENTORY -> document_type: "Supply Chain Log", department: "Operations"

=== OUTPUT FORMAT (STRICT JSON) ===

{
  "document_type": "MUST be ONE of: HR Report | Sales Log | Finance Report | Marketing Report | Supply Chain Log | Legal Policy | Legal Contract | Legal Case | Employee",
  "department": "MUST be ONE of: HR | Sales | Finance | Marketing | Operations | Legal",
  "confidence": 0.95,
  "summary": "clear business summary",
  "entities": [
    {
      "type": "Employee | Campaign | Metric | Organization | Date | Amount",
      "name": "field name (e.g. employee_name, salary, period)",
      "value": "the actual extracted value",
      "role": "optional context"
    }
  ],
  "tags": ["relevant", "keywords"],
  "relationships": [
    {
      "source": "entity_name",
      "target": "entity_name",
      "type": "relationship_type",
      "confidence": 0.9
    }
  ]
}

=== EXTRACTION RULES ===

- Extract ALL visible data: employee names, dates, amounts, metrics
- For payslips: extract employee name, salary, period, attendance, deductions, bonuses
- Normalize numbers (no commas, use plain numbers: 10500 not 10,500)
- Keep entity names consistent
- Always provide at least 1 entity if you can read ANY data

Now analyze the provided document text and return ONLY valid JSON."""

    def __init__(self):
        self.settings = load_document_settings()
        if not self.settings.zhipu_api_key:
            raise ValueError(
                "ZHIPU_API_KEY is missing. Add a valid key to backend/.env, then rerun."
            )

    def _call_zhipu(self, document_text: str) -> str:
        import httpx
        import time as _time
        import random

        url = self.settings.zhipu_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.zhipu_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.zhipu_model,
            "messages": [
                {"role": "system", "content": self.EXTRACTION_PROMPT},
                {"role": "user", "content": f"Document text:\n\n{document_text[:8000]}"},
            ],
            "temperature": self.settings.llm_temperature,
            "max_tokens": 3000,
        }
        retryable = {502, 503, 504}
        max_attempts = 4
        with httpx.Client(timeout=120.0) as client:
            for attempt in range(max_attempts):
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code in retryable:
                    wait = min(30.0, 3.0 * (2 ** attempt) + random.uniform(0, 1))
                    print(f"    [DOCUMENT_SERVICE] HTTP {resp.status_code}, retrying in {wait:.1f}s (attempt {attempt + 1}/{max_attempts})")
                    _time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        raise Exception(f"Zhipu request failed after {max_attempts} attempts (last status: {resp.status_code})")

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]
        return json.loads(text)

    def process(self, file_path: str) -> Dict[str, Any]:
        print(f"    [DOCUMENT_SERVICE] Starting document processing...")
        print(f"    [DOCUMENT_SERVICE] File path: {file_path}")

        file_ext = Path(file_path).suffix.lower()
        print(f"    [DOCUMENT_SERVICE] File extension: {file_ext}")

        file_type = (
            "IMAGE" if file_ext in IMAGE_EXTENSIONS else
            "PDF" if file_ext == ".pdf" else
            "DOCX" if file_ext == ".docx" else
            "TEXT"
        )
        print(f"    [DOCUMENT_SERVICE] Processing as {file_type} using Zhipu GLM...")

        try:
            print(f"    [DOCUMENT_SERVICE] Extracting text from file...")
            document_text = _extract_text_from_file(file_path)
            preview = document_text[:200].replace("\n", " ")
            print(f"    [DOCUMENT_SERVICE] Extracted {len(document_text)} chars. Preview: {preview}")
        except Exception as e:
            print(f"    [DOCUMENT_SERVICE] Text extraction failed: {e}")
            raise

        print(f"    [DOCUMENT_SERVICE] Calling Zhipu GLM for extraction and classification...")
        try:
            raw_text = self._call_zhipu(document_text)
        except Exception as e:
            print(f"    [DOCUMENT_SERVICE] Zhipu GLM call failed: {e}")
            raise Exception(f"Zhipu GLM extraction failed: {e}")

        print(f"    [DOCUMENT_SERVICE] Zhipu GLM response received")
        print(f"    [DOCUMENT_SERVICE] Raw AI response (first 500 chars):")
        print(f"    [DOCUMENT_SERVICE] {raw_text[:500]}")
        print()

        result = self._parse_json_response(raw_text)

        print(f"    [DOCUMENT_SERVICE] SUCCESS - Extraction completed")
        print(f"    [DOCUMENT_SERVICE] Document type: {result.get('document_type', 'Unknown')}")
        print(f"    [DOCUMENT_SERVICE] Department: {result.get('department', 'Unknown')}")
        print(f"    [DOCUMENT_SERVICE] Entities extracted: {len(result.get('entities', []))}")

        if not result.get("entities"):
            print(f"    [DOCUMENT_SERVICE] WARNING: No entities extracted from document!")
        else:
            for i, entity in enumerate(result.get("entities", [])[:5], 1):
                print(f"    [DOCUMENT_SERVICE]   {i}. {entity.get('type', 'N/A')}: {entity.get('name', 'N/A')} = {entity.get('value', 'N/A')}")
            if len(result.get("entities", [])) > 5:
                print(f"    [DOCUMENT_SERVICE]   ... and {len(result.get('entities', [])) - 5} more")
        print()

        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a document and run AI extraction.")
    parser.add_argument("file", help="Path to file (pdf/doc/docx/txt/md/rtf/png/jpg/jpeg/webp/gif/bmp/tiff)")
    args = parser.parse_args()

    raw_path = Path(args.file).expanduser()
    backend_root = Path(__file__).resolve().parents[1]
    repo_root = backend_root.parent

    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.append(Path.cwd() / raw_path)
        candidates.append(backend_root / raw_path)
        candidates.append(repo_root / raw_path)

    file_path = next((p.resolve() for p in candidates if p.exists() and p.is_file()), None)
    if file_path is None:
        raise FileNotFoundError(f"File not found: {raw_path}")
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"Unsupported file type '{file_path.suffix}'. Allowed: {allowed}")

    agent = DocumentIngestor()
    data = agent.process(str(file_path))
    print("\nParsed output:")
    print(json.dumps(data, indent=2))
