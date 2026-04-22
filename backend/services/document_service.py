import time
import json
import argparse
import base64
from pathlib import Path
from typing import Dict, Any, Optional
import warnings
import os
import mimetypes
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

try:
    from config import get_settings
except ModuleNotFoundError:
    # Allows running this file directly: python services/document_service.py ...
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from config import get_settings


@dataclass
class DocumentServiceSettings:
    zhipu_api_key: Optional[str]
    zhipu_base_url: str = "https://api.ilmu.ai/v1"
    zhipu_model: str = "nemo-super"
    llm_temperature: float = 0.7


def load_document_settings() -> DocumentServiceSettings:
    """Load only settings required for document ingestion."""
    try:
        app_settings = get_settings()
        return DocumentServiceSettings(
            zhipu_api_key=app_settings.zhipu_api_key,
            zhipu_base_url=app_settings.zhipu_base_url,
            zhipu_model=app_settings.zhipu_model,
            llm_temperature=app_settings.llm_temperature,
        )
    except Exception:
        # Fall back to direct env loading for standalone script usage.
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
            zhipu_model=os.getenv("ZHIPU_MODEL", "nemo-super"),
            llm_temperature=temp,
        )


def _validate_zhipu_api_key(api_key: Optional[str]) -> None:
    if not api_key or not api_key.strip():
        raise ValueError(
            "ZHIPU_API_KEY is missing. Add a valid key to backend/.env, then rerun."
        )

    normalized = api_key.strip()
    placeholder_markers = {
        "your_key_here",
        "replace_me",
        "changeme",
        "xxx",
    }
    if (
        normalized.lower() in placeholder_markers
        or "your" in normalized.lower() and "key" in normalized.lower()
    ):
        raise ValueError(
            "ZHIPU_API_KEY appears to be a placeholder. Set your real Zhipu API key in backend/.env."
        )

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".txt", ".md", ".rtf",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".xlsx", ".csv"
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv"}

MIME_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".rtf": "application/rtf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
}

class DocumentIngestor:
    def __init__(self):
        # Fetch settings from config
        self.settings = load_document_settings()
        _validate_zhipu_api_key(self.settings.zhipu_api_key)
        
        # Initialize Zhipu AI client (OpenAI-compatible)
        self.client = OpenAI(
            api_key=self.settings.zhipu_api_key,
            base_url=self.settings.zhipu_base_url
        )

        self.extraction_prompt = """You are an enterprise document classification and information extraction system.

Your job:
1. Classify the document correctly into ONE department
2. Extract structured business data
3. Identify relationships between entities

DOCUMENT TYPE RESTRICTIONS - Use ONLY these exact values:
- "HR Report"
- "Sales Log"
- "Finance Report"
- "Marketing Report"
- "Supply Chain Log"
- "Legal Policy"
- "Employee" (for individual employee documents like payslips)

DEPARTMENT CLASSIFICATION RULES:
- HR: Payslip, employee evaluation, payroll, hiring, resignation, benefits
- Marketing: Campaign report, ROI report, advertisement, customer segmentation
- Sales: Sales report, revenue data, pipeline, deals
- Finance: Invoice, financial statement, budget, expense report
- Legal: Contracts, agreements, compliance
- Operations: Supply chain, logistics, inventory

IMPORTANT:
- "Job title" ≠ department
- A "Marketing Executive payslip" is STILL HR
- Document type must be one of the restricted values above

OUTPUT FORMAT (STRICT JSON ONLY):
{
  "document_type": "HR Report | Sales Log | Finance Report | Marketing Report | Supply Chain Log | Legal Policy | Employee",
  "department": "HR | Marketing | Sales | Finance | Legal | Operations",
  "confidence": 0.95,
  "summary": "clear business summary",
  "entities": [
    {
      "type": "Employee | Campaign | Metric | Organization | Date | Amount",
      "name": "string",
      "value": "optional",
      "role": "optional description"
    }
  ],
  "tags": ["string"],
  "relationships": [
    {
      "source": "entity_name",
      "target": "entity_name",
      "type": "relationship_type",
      "confidence": 0.9
    }
  ]
}

EXTRACTION RULES:
- Always extract monetary values (salary, ROI, cost)
- Normalize numbers (no commas, use plain numbers)
- Keep entity names consistent
- Relationships must connect existing entities
- If unsure, lower confidence score (0.5-0.7)

Now analyze the provided document and return ONLY valid JSON."""

    def _encode_image_base64(self, file_path: str) -> str:
        """Encode image file to base64 string"""
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type from file extension"""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }
        return mime_types.get(ext, "image/jpeg")

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from AI response, handling markdown code blocks"""
        text = (text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        return json.loads(text)

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            return "[PDF text extraction not available - install pypdf]"
        except Exception as e:
            return f"[PDF text extraction failed: {str(e)}]"
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            return "[DOCX text extraction not available - install python-docx]"
        except Exception as e:
            return f"[DOCX text extraction failed: {str(e)}]"

    def process(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document file and extract structured data using Zhipu AI.
        Supports images, PDFs, and text documents.
        """
        file_ext = Path(file_path).suffix.lower()
        
        # For images, use vision API with base64 encoding
        if file_ext in IMAGE_EXTENSIONS:
            base64_image = self._encode_image_base64(file_path)
            mime_type = self._get_mime_type(file_path)
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.extraction_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        
        # For PDFs, extract text first
        elif file_ext == ".pdf":
            text_content = self._extract_text_from_pdf(file_path)
            messages = [
                {
                    "role": "user",
                    "content": f"{self.extraction_prompt}\n\nDocument content:\n{text_content}"
                }
            ]
        
        # For DOCX files
        elif file_ext == ".docx":
            text_content = self._extract_text_from_docx(file_path)
            messages = [
                {
                    "role": "user",
                    "content": f"{self.extraction_prompt}\n\nDocument content:\n{text_content}"
                }
            ]
        
        # For plain text files
        elif file_ext in TEXT_EXTENSIONS:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            messages = [
                {
                    "role": "user",
                    "content": f"{self.extraction_prompt}\n\nDocument content:\n{content}"
                }
            ]
        
        # For other formats (Excel, etc.), try to read as text
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()[:5000]  # Limit to 5000 chars for non-text formats
            
            messages = [
                {
                    "role": "user",
                    "content": f"{self.extraction_prompt}\n\nDocument content (first 5000 chars):\n{content}"
                }
            ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.zhipu_model,
                messages=messages,
                temperature=self.settings.llm_temperature,
                response_format={"type": "json_object"}
            )
            
            return self._parse_json_response(response.choices[0].message.content)
        
        except Exception as e:
            raise Exception(f"Zhipu AI extraction failed: {str(e)}")

# Example usage in your main app
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a document/image and run AI extraction.")
    parser.add_argument(
        "file",
        help="Path to file (pdf/doc/docx/txt/md/rtf/png/jpg/jpeg/webp/gif/bmp/tiff)"
    )
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
        hint1 = (backend_root / "workplaces" / "documents").resolve()
        hint2 = (repo_root / "workplaces" / "documents").resolve()
        raise FileNotFoundError(
            f"File not found: {raw_path}. Try a valid path, e.g. '.\\workplaces\\documents\\...'. "
            f"Checked common locations: {hint1} and {hint2}."
        )
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"Unsupported file type '{file_path.suffix}'. Allowed: {allowed}")

    agent = DocumentIngestor()
    data = agent.process(str(file_path))
    print("\nParsed output:")
    print(json.dumps(data, indent=2))