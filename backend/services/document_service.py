import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any
import warnings
import os
import mimetypes
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    # Preferred Gemini SDK
    from google import genai as google_genai
    HAS_NEW_GENAI = True
except Exception:
    google_genai = None
    HAS_NEW_GENAI = False

legacy_genai = None

try:
    from config import get_settings
except ModuleNotFoundError:
    # Allows running this file directly: python services/document_service.py ...
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from config import get_settings


@dataclass
class DocumentServiceSettings:
    google_api_key: str | None
    llm_model: str = "gemini-2.5-flash-lite"
    llm_temperature: float = 0.7


def load_document_settings() -> DocumentServiceSettings:
    """Load only settings required for document ingestion.

    This keeps document testing independent from unrelated required fields
    in the main application settings (e.g., Supabase keys).
    """
    try:
        app_settings = get_settings()
        return DocumentServiceSettings(
            google_api_key=app_settings.google_api_key,
            llm_model=app_settings.llm_model,
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
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            llm_model=os.getenv("LLM_MODEL", "gemini-2.5-flash-lite"),
            llm_temperature=temp,
        )


def _validate_google_api_key(api_key: str | None) -> None:
    if not api_key or not api_key.strip():
        raise ValueError(
            "GOOGLE_API_KEY is missing. Add a valid key to backend/.env, then rerun."
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
            "GOOGLE_API_KEY appears to be a placeholder. Set your real Gemini API key in backend/.env."
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

class DocumentIngestor:
    def __init__(self):
        # 1. Fetch settings from your config system
        self.settings = load_document_settings()
        _validate_google_api_key(self.settings.google_api_key)
        
        # 2. Configure the Gemini SDK
        self._sdk = None
        self.model = None
        self.client = None

        if HAS_NEW_GENAI:
            self._sdk = "new"
            self.client = google_genai.Client(api_key=self.settings.google_api_key)
        else:
            # Fallback for older environments, imported lazily to avoid
            # deprecation warning when new SDK is available.
            global legacy_genai
            if legacy_genai is None:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", FutureWarning)
                        import google.generativeai as _legacy_genai
                    legacy_genai = _legacy_genai
                except Exception:
                    legacy_genai = None

        if legacy_genai is not None and self._sdk is None:
            self._sdk = "legacy"
            legacy_genai.configure(api_key=self.settings.google_api_key)
            self.model = legacy_genai.GenerativeModel(model_name=self.settings.llm_model)
        elif self._sdk is None:
            raise ImportError(
                "No Gemini SDK available. Install 'google-genai' or 'google-generativeai'."
            )

        self.extraction_prompt = """
        You are an enterprise document classification and information extraction system.

        Your job:
        1. Classify the document correctly into ONE department
        2. Extract structured business data
        3. Identify relationships between entities

        ----------------------------------------
        DEPARTMENT CLASSIFICATION RULES:

        - HR:
        Payslip, employee evaluation, payroll, hiring, resignation, benefits

        - Marketing:
        Campaign report, ROI report, advertisement, customer segmentation

        - Sales:
        Sales report, revenue data, pipeline, deals

        - Finance:
        Invoice, financial statement, budget, expense report

        - Legal:
        Contracts, agreements, compliance

        - Operations:
        Supply chain, logistics, inventory

        IMPORTANT:
        - "Job title" ≠ department
        - A "Marketing Executive payslip" is STILL HR

        ----------------------------------------
        OUTPUT FORMAT (STRICT JSON ONLY):

        {
        "document_type": "string",
        "department": "HR | Marketing | Sales | Finance | Legal | Operations",
        "confidence": float,
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
            "confidence": float
            }
        ]
        }

        ----------------------------------------
        EXTRACTION RULES:

        - Always extract monetary values (salary, ROI, cost)
        - Normalize numbers (no commas, use plain numbers)
        - Keep entity names consistent
        - Relationships must connect existing entities
        - If unsure, lower confidence score (0.5–0.7)

        ----------------------------------------
        Now analyze the provided document.
        """

    def _detect_mime_type(self, file_path: str) -> str:
        guessed, _ = mimetypes.guess_type(file_path)
        if guessed:
            return guessed

        ext = Path(file_path).suffix.lower()
        mapped = MIME_BY_EXTENSION.get(ext)
        if mapped:
            return mapped

        raise ValueError(
            f"Unknown MIME type for '{file_path}'. Please use a supported file extension."
        )

    def _upload_and_wait(self, file_path: str):
        if self._sdk == "new":
            mime_type = self._detect_mime_type(file_path)
            uploaded = self.client.files.upload(
                file=file_path,
                config={"mime_type": mime_type},
            )
            name = getattr(uploaded, "name", None)
            if not name:
                return uploaded

            # Some file types require background processing before generation.
            for _ in range(30):
                current = self.client.files.get(name=name)
                state = getattr(current, "state", None)
                state_name = getattr(state, "name", str(state)) if state is not None else "ACTIVE"
                if state_name not in {"PROCESSING", "STATE_UNSPECIFIED"}:
                    return current
                time.sleep(2)
            return current

        file = legacy_genai.upload_file(file_path)
        while file.state.name == "PROCESSING":
            time.sleep(2)
            file = legacy_genai.get_file(file.name)
        return file

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        return json.loads(text)

    def process(self, file_path: str) -> Dict[str, Any]:
        uploaded_file = self._upload_and_wait(file_path)

        if self._sdk == "new":
            response = self.client.models.generate_content(
                model=self.settings.llm_model,
                contents=[uploaded_file, self.extraction_prompt],
                config=google_genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=self.settings.llm_temperature,
                ),
            )
        else:
            response = self.model.generate_content(
                [uploaded_file, self.extraction_prompt],
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": self.settings.llm_temperature
                }
            )

        # Debug
        # print(response.text)
        return self._parse_json_response(response.text)

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