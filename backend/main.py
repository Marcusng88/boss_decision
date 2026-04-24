"""
Main FastAPI application for AI Boss Decision Engine.
Multi-agent decision support system with LangChain integration.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import tempfile
import os
from datetime import datetime

from config import get_settings
from db import DatabaseService

# Import services lazily to avoid import-time configuration errors
# from services.cloudinary_service import get_cloudinary_service
# from services.document_service import DocumentIngestor  
# from services.data_writer_agent import get_data_writer_agent

# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="Multi-agent decision support system for strategic business questions"
)

# CORS middleware (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database service
db = DatabaseService()


# ============================================
# Request/Response Models
# ============================================

class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint."""
    query: str
    context: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    submitted_by: Optional[str] = None


class EmployeeResponse(BaseModel):
    """Response model for employee endpoint."""
    employee: dict
    hr_records: list[dict]
    sales_records: list[dict]


# ============================================
# Routes
# ============================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "message": f"{settings.app_name} API",
        "version": settings.api_version
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check with database connectivity."""
    try:
        # Test database connection
        supabase = db.client
        response = supabase.table('department').select('count').execute()
        
        return {
            "status": "healthy",
            "database": "connected",
            "supabase": "ok"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/api/employees/{employee_id}")
async def get_employee(employee_id: int):
    """Get employee profile with related records."""
    try:
        employee = await db.get_employee(employee_id)
        hr_records = await db.get_employee_hr_records(employee_id)
        sales_records = await db.get_employee_sales_records(employee_id)
        
        return {
            "employee": employee,
            "hr_records": hr_records,
            "sales_records": sales_records
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Employee not found: {str(e)}")


@app.get("/api/cases/{case_id}")
async def get_case(case_id: int):
    """Get decision case with evidence and output."""
    try:
        evidence = await db.get_case_evidence(case_id)
        decision = await db.get_decision_output(case_id)
        
        return {
            "case_id": case_id,
            "evidence": evidence,
            "decision": decision
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Case not found: {str(e)}")


@app.post("/api/analyze")
async def analyze_query(request: AnalyzeRequest):
    """
    Main decision engine endpoint.
    Analyzes a business question using multi-agent system.
    
    TODO: Implement full agent orchestration (see agents/ folder)
    """
    try:
        # Create decision case
        case = await db.create_decision_case(
            question=request.query,
            context=request.context,
            target_type=request.target_type,
            target_id=request.target_id,
            submitted_by=request.submitted_by
        )
        
        # TODO: Implement multi-agent pipeline
        # 1. Evidence retrieval (retrieve relevant records)
        # 2. Agent analysis (HR, Sales, Legal, Finance, Marketing, Supply Chain)
        # 3. Manager synthesis (aggregate agent outputs)
        # 4. Save decision output
        
        # For now, return case ID with placeholder
        return {
            "status": "processing",
            "case_id": case['case_id'],
            "message": "Decision case created. Multi-agent pipeline not yet implemented.",
            "query": request.query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    custom_extraction: Optional[str] = Form(None)
):
    """
    Upload a document, extract data with AI, and write to database.
    
    Flow:
    1. Upload file to Cloudinary
    2. Create source_document record
    3. Extract data with Zhipu GLM (document_service.py)
    4. Write data to appropriate tables with Zhipu AI (data_writer_agent.py)
    
    Args:
        file: Document file to upload
        custom_extraction: Optional user-requested data to extract (will use ai_justification if not standard column)
    """
    print("\n" + "="*80)
    print("DOCUMENT UPLOAD PIPELINE STARTED")
    print("="*80)
    print(f"File: {file.filename}")
    print(f"Custom extraction requested: {custom_extraction if custom_extraction else 'None'}")
    print()
    
    try:
        # Validate file type
        print("[STEP 0] Validating file type...")
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.md', '.png', '.jpg', '.jpeg', '.xlsx', '.csv'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            print(f"[STEP 0] FAILED - Unsupported file type: {file_ext}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        print(f"[STEP 0] SUCCESS - File type validated: {file_ext}")
        
        # Read file content
        file_content = await file.read()
        print(f"[STEP 0] File read successfully, size: {len(file_content)} bytes")
        print()
        
        # Step 1: Upload to Cloudinary
        print("[STEP 1] CLOUDINARY UPLOAD - Starting upload to Cloudinary...")
        from services.cloudinary_service import get_cloudinary_service
        
        cloudinary_service = get_cloudinary_service()
        upload_result = cloudinary_service.upload_from_bytes(
            file_bytes=file_content,
            filename=file.filename,
            folder="documents",
            doc_type=None  # Will be determined by AI
        )
        
        if not upload_result["success"]:
            print(f"[STEP 1] FAILED - Cloudinary upload error: {upload_result.get('error')}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {upload_result.get('error')}")
        
        file_url = upload_result["url"]
        print(f"[STEP 1] SUCCESS - File uploaded to Cloudinary")
        print(f"         URL: {file_url}")
        print()
        
        # Step 2: Generate next source_id
        print("[STEP 2] SOURCE DOCUMENT - Creating source_document record...")
        max_id_result = db.client.table("source_document")\
            .select("source_id")\
            .order("source_id", desc=True)\
            .limit(1)\
            .execute()
        
        if max_id_result.data and len(max_id_result.data) > 0:
            source_id = max_id_result.data[0]["source_id"] + 1
        else:
            source_id = 501  # Start from 501 if no records exist
        
        print(f"         Generated source_id: {source_id}")
        
        # Step 3: Create source_document record
        source_doc_data = {
            "source_id": source_id,  # Manually generated ID
            "doc_type": "Unknown",  # Will be updated after extraction
            "title": file.filename,
            "file_path": file_url,
            "extracted_at": None,  # Not yet processed
            "notes": f"Uploaded via API at {datetime.now().isoformat()}"
        }
        
        result = db.client.table("source_document")\
            .insert(source_doc_data)\
            .execute()
        
        if not result.data:
            print("[STEP 2] FAILED - Could not insert source_document record")
            raise HTTPException(status_code=500, detail="Failed to create source document record")
        
        print(f"[STEP 2] SUCCESS - source_document record created (ID: {source_id})")
        print()
        
        # Step 3: Extract data with document_service (Zhipu GLM)
        print("[STEP 3] DOCUMENT EXTRACTION - Starting AI extraction with Zhipu GLM...")
        extraction_json = None
        doc_type = "Unknown"
        
        try:
            # Save file temporarily for document service
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            print(f"         Temp file created: {temp_file_path}")
            
            try:
                from services.document_service import DocumentIngestor
                
                document_ingestor = DocumentIngestor()
                print("         Calling document_service.process()...")
                extraction_json = document_ingestor.process(temp_file_path)
                doc_type = extraction_json.get("document_type", "Unknown")
                
                print(f"[STEP 3] SUCCESS - Document extracted")
                print(f"         Document Type: {doc_type}")
                print(f"         Department: {extraction_json.get('department', 'N/A')}")
                print(f"         Entities extracted: {len(extraction_json.get('entities', []))}")
                
                # If no entities, show full extraction JSON for debugging
                if len(extraction_json.get('entities', [])) == 0:
                    print(f"         ⚠️  WARNING: No entities found!")
                    print(f"         Full extraction JSON:")
                    import json
                    print(f"         {json.dumps(extraction_json, indent=10)[:1000]}")
                print()
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
            # Update source_document with extracted doc_type
            print(f"         Updating source_document with doc_type: {doc_type}")
            db.client.table("source_document")\
                .update({
                    "doc_type": doc_type,
                    "extracted_at": datetime.now().isoformat()
                })\
                .eq("source_id", source_id)\
                .execute()
            print(f"         source_document updated successfully")
            print()
            
        except Exception as e:
            # Extraction failed, but document is uploaded
            print(f"[STEP 3] FAILED - Document extraction error:")
            print(f"         Error: {str(e)}")
            import traceback
            print(f"         Traceback:")
            print(traceback.format_exc())
            print()
            extraction_json = None
        
        # Step 4 & 5: Write extracted data to database with data_writer_agent (Zhipu AI)
        if extraction_json:
            print("[STEP 4-5] DATA WRITER AGENT - Starting intelligent SQL generation and database write...")
            try:
                from services.data_writer_agent import get_data_writer_agent
                
                data_writer = get_data_writer_agent()
                print("         Calling data_writer.process_document_extraction()...")
                write_result = data_writer.process_document_extraction(
                    extraction_json=extraction_json,
                    source_id=source_id,
                    custom_extraction=custom_extraction
                )
                
                if write_result["success"]:
                    print(f"[STEP 4-5] SUCCESS - Data written to database")
                    print(f"           Rows inserted: {write_result.get('execution_results', {}).get('rows_inserted', 0)}")
                    print()
                    print("="*80)
                    print("PIPELINE COMPLETED SUCCESSFULLY")
                    print("="*80)
                    print()
                else:
                    print(f"[STEP 4-5] PARTIAL FAILURE - Data write had issues")
                    exec_results = write_result.get('execution_results', {})
                    error_msg = exec_results.get('error') or write_result.get('error', 'Unknown error')
                    print(f"           Error: {error_msg}")
                    print(f"           Rows inserted: {exec_results.get('rows_inserted', 0)}/{exec_results.get('total_statements', 0)} statements")
                    
                    # Show failed statement details
                    failed_details = [d for d in exec_results.get('details', []) if not d.get('success', False)]
                    if failed_details:
                        print(f"           Failed statements:")
                        for detail in failed_details[:3]:  # Show up to 3 failures
                            print(f"             - {detail.get('statement', 'N/A')[:80]}...")
                            print(f"               Error: {detail.get('error', 'N/A')}")
                    print()
                
                return {
                    "success": write_result["success"],
                    "source_id": source_id,
                    "file_url": file_url,
                    "doc_type": doc_type,
                    "department": extraction_json.get("department"),
                    "extraction_status": "completed",
                    "data_written": write_result.get("execution_results", {}).get("rows_inserted", 0),
                    "details": write_result
                }
            
            except Exception as e:
                # Data writing failed, but extraction succeeded
                print(f"[STEP 4-5] FAILED - Data writer agent error:")
                print(f"           Error: {str(e)}")
                import traceback
                print(f"           Traceback:")
                print(traceback.format_exc())
                print()
                print("="*80)
                print("PIPELINE FAILED AT DATA WRITING STEP")
                print("="*80)
                print()
                
                return {
                    "success": False,
                    "source_id": source_id,
                    "file_url": file_url,
                    "doc_type": doc_type,
                    "extraction_status": "completed",
                    "write_status": "failed",
                    "error": f"Data writing failed: {str(e)}",
                    "extraction_data": extraction_json
                }
        else:
            # No extraction - just return upload success
            print("[STEP 3] WARNING - Extraction failed or was skipped")
            print("         Returning upload-only success (no data extraction/writing)")
            print()
            print("="*80)
            print("PIPELINE COMPLETED WITH WARNINGS (extraction skipped)")
            print("="*80)
            print()
            
            return {
                "success": True,
                "source_id": source_id,
                "file_url": file_url,
                "doc_type": doc_type,
                "extraction_status": "skipped",
                "message": "Document uploaded successfully. AI extraction skipped or failed."
            }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in upload: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Upload process failed: {str(e)}")


@app.get("/api/documents")
async def list_documents(
    doc_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Get list of uploaded documents with optional filtering.
    
    Query params:
    - doc_type: Filter by document type (HR, Sales, Finance, etc.)
    - limit: Max number of results (default 50)
    - offset: Pagination offset (default 0)
    """
    try:
        query = db.client.table("source_document")\
            .select("*")\
            .order("created_at", desc=True)
        
        # Apply filter if doc_type provided
        if doc_type:
            query = query.eq("doc_type", doc_type)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        # Get total count
        count_query = db.client.table("source_document").select("count", count="exact")
        if doc_type:
            count_query = count_query.eq("doc_type", doc_type)
        count_result = count_query.execute()
        total = count_result.count if hasattr(count_result, 'count') else len(result.data)
        
        return {
            "documents": result.data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.get("/api/documents/{source_id}")
async def get_document(source_id: int):
    """Get single document by ID with related records."""
    try:
        # Get document
        doc_result = db.client.table("source_document")\
            .select("*")\
            .eq("source_id", source_id)\
            .single()\
            .execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_result.data
        
        # Get related records from various tables
        related_records = {}
        
        # Check each table for records linked to this source_id
        tables = ["hr_record", "sales_record", "finance_record", "marketing_record", "supply_record", "legal_policy"]
        
        for table in tables:
            try:
                result = db.client.table(table)\
                    .select("*")\
                    .eq("source_id", source_id)\
                    .execute()
                if result.data:
                    related_records[table] = result.data
            except:
                pass
        
        return {
            "document": document,
            "related_records": related_records
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.delete("/api/documents/{source_id}")
async def delete_document(source_id: int):
    """Delete a document and its related records."""
    try:
        # Get document to get Cloudinary public_id
        doc_result = db.client.table("source_document")\
            .select("file_path")\
            .eq("source_id", source_id)\
            .single()\
            .execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = doc_result.data["file_path"]
        
        # Extract Cloudinary public_id from URL
        # URL format: https://res.cloudinary.com/cloud_name/resource_type/upload/v123/public_id.ext
        if "cloudinary.com" in file_path:
            try:
                parts = file_path.split("/upload/")
                if len(parts) > 1:
                    public_id_with_ext = "/".join(parts[1].split("/")[1:])
                    public_id = public_id_with_ext.rsplit(".", 1)[0]
                    
                    # Delete from Cloudinary
                    from services.cloudinary_service import get_cloudinary_service
                    cloudinary_service = get_cloudinary_service()
                    cloudinary_service.delete_document(public_id)
            except:
                pass  # Continue even if Cloudinary deletion fails
        
        # Delete from database (CASCADE will remove related records)
        db.client.table("source_document")\
            .delete()\
            .eq("source_id", source_id)\
            .execute()
        
        return {
            "success": True,
            "message": f"Document {source_id} deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


# ============================================
# Run Server
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True  # Auto-reload on code changes (development only)
    )
