"""
Document Processing API Endpoints for Flogenix Platform

Provides endpoints for:
- Document upload and validation
- OCR processing of claim documents
- Document storage and retrieval
- Document metadata management
"""

import os
import uuid
import mimetypes
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_database_session
from app.core.security import get_current_user
from app.core.models import User, Claim
from app.services.ocr_service import ocr_service
from app.core.config import get_settings

settings = get_settings()

router = APIRouter()

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    document_id: str
    filename: str
    file_size: int
    content_type: str
    upload_status: str
    ocr_processed: bool = False
    ocr_confidence: Optional[float] = None
    extracted_text: Optional[str] = None
    extracted_fields: Dict[str, Any] = {}
    processing_time: Optional[float] = None
    error: Optional[str] = None


class DocumentProcessingRequest(BaseModel):
    """Request model for document processing"""
    document_id: str
    ocr_provider: Optional[str] = Field(None, description="Specific OCR provider to use")
    extract_fields: bool = Field(True, description="Whether to extract medical fields")


class DocumentSearchRequest(BaseModel):
    """Request model for document search"""
    claim_id: Optional[str] = None
    document_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    has_ocr: Optional[bool] = None


class DocumentMetadata(BaseModel):
    """Document metadata model"""
    document_id: str
    filename: str
    file_size: int
    content_type: str
    upload_date: datetime
    uploaded_by: str
    claim_id: Optional[str] = None
    document_type: Optional[str] = None
    ocr_processed: bool = False
    ocr_confidence: Optional[float] = None
    processing_status: str


def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file"""
    
    # Check file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {file.size} exceeds maximum allowed size {MAX_FILE_SIZE} bytes"
        )
    
    # Check content type
    allowed_mime_types = {
        'application/pdf',
        'image/png',
        'image/jpeg',
        'image/tiff',
        'image/bmp'
    }
    
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Content type {file.content_type} not allowed"
        )
    
    return True


def save_uploaded_file(file: UploadFile, document_id: str) -> Path:
    """Save uploaded file to disk"""
    
    # Create unique filename
    file_ext = Path(file.filename or "").suffix.lower()
    safe_filename = f"{document_id}{file_ext}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    return file_path


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    claim_id: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    process_ocr: bool = Form(True),
    ocr_provider: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Upload a document and optionally process with OCR
    
    - **file**: The document file to upload
    - **claim_id**: Associated claim ID (optional)
    - **document_type**: Type of document (e.g., 'medical_bill', 'insurance_card')
    - **process_ocr**: Whether to process document with OCR
    - **ocr_provider**: Specific OCR provider to use
    """
    
    try:
        # Validate file
        validate_file(file)
        
        # Generate document ID
        document_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        
        # Verify claim exists if provided
        if claim_id:
            claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
            if not claim:
                raise HTTPException(status_code=404, detail="Claim not found")
        
        # Save file
        file_path = save_uploaded_file(file, document_id)
        file_size = file_path.stat().st_size
        
        # Create response
        response = DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename or "unknown",
            file_size=file_size,
            content_type=file.content_type or "unknown",
            upload_status="success"
        )
        
        # Process OCR if requested
        if process_ocr:
            background_tasks.add_task(
                process_document_ocr,
                document_id,
                file_path,
                ocr_provider,
                db
            )
            response.upload_status = "uploaded_processing"
        
        # Store document metadata in database
        # Note: You'll need to create a Document model in your database
        # For now, we'll just log the upload
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


async def process_document_ocr(
    document_id: str,
    file_path: Path,
    ocr_provider: Optional[str],
    db: Session
):
    """Background task to process document with OCR"""
    
    try:
        # Read image file
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        # Process with OCR
        result = await ocr_service.process_document(
            image_data=image_data,
            provider=ocr_provider,
            fallback=True
        )
        
        # Update document metadata with OCR results
        # This would normally update the database Document record
        # For now, we'll create a JSON file with the results
        
        result_file = file_path.with_suffix('.ocr.json')
        with open(result_file, 'w') as f:
            import json
            json.dump({
                "document_id": document_id,
                "text": result.text,
                "confidence": result.confidence,
                "provider": result.provider,
                "processing_time": result.processing_time,
                "extracted_fields": result.extracted_fields,
                "error": result.error,
                "processed_at": datetime.now().isoformat()
            }, f, indent=2)
        
    except Exception as e:
        # Log error
        error_file = file_path.with_suffix('.error.json')
        with open(error_file, 'w') as f:
            import json
            json.dump({
                "document_id": document_id,
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }, f, indent=2)


@router.post("/documents/{document_id}/process", response_model=DocumentUploadResponse)
async def process_document(
    document_id: str,
    processing_request: DocumentProcessingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process an uploaded document with OCR
    
    - **document_id**: ID of the uploaded document
    - **ocr_provider**: Specific OCR provider to use
    - **extract_fields**: Whether to extract medical fields
    """
    
    try:
        # Find document file
        document_files = list(UPLOAD_DIR.glob(f"{document_id}.*"))
        document_files = [f for f in document_files if not f.suffix.startswith('.ocr') and not f.suffix.startswith('.error')]
        
        if not document_files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = document_files[0]
        
        # Read image file
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        # Process with OCR
        start_time = datetime.now()
        result = await ocr_service.process_document(
            image_data=image_data,
            provider=processing_request.ocr_provider,
            fallback=True
        )
        
        # Create response
        response = DocumentUploadResponse(
            document_id=document_id,
            filename=file_path.name,
            file_size=file_path.stat().st_size,
            content_type=mimetypes.guess_type(str(file_path))[0] or "unknown",
            upload_status="processed",
            ocr_processed=True,
            ocr_confidence=result.confidence,
            extracted_text=result.text,
            extracted_fields=result.extracted_fields,
            processing_time=result.processing_time,
            error=result.error
        )
        
        # Save OCR results
        result_file = file_path.with_suffix('.ocr.json')
        with open(result_file, 'w') as f:
            import json
            json.dump({
                "document_id": document_id,
                "text": result.text,
                "confidence": result.confidence,
                "provider": result.provider,
                "processing_time": result.processing_time,
                "extracted_fields": result.extracted_fields,
                "error": result.error,
                "processed_at": datetime.now().isoformat()
            }, f, indent=2)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download a document file"""
    
    try:
        # Find document file
        document_files = list(UPLOAD_DIR.glob(f"{document_id}.*"))
        document_files = [f for f in document_files if not f.suffix.startswith('.ocr') and not f.suffix.startswith('.error')]
        
        if not document_files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = document_files[0]
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type=mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")


@router.get("/documents/{document_id}/ocr", response_model=Dict[str, Any])
async def get_document_ocr(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get OCR results for a document"""
    
    try:
        # Find OCR result file
        ocr_files = list(UPLOAD_DIR.glob(f"{document_id}.*.ocr.json"))
        
        if not ocr_files:
            raise HTTPException(status_code=404, detail="OCR results not found")
        
        ocr_file = ocr_files[0]
        
        # Read OCR results
        with open(ocr_file, 'r') as f:
            import json
            ocr_data = json.load(f)
        
        return ocr_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OCR results: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document and associated files"""
    
    try:
        # Find all files for this document
        document_files = list(UPLOAD_DIR.glob(f"{document_id}.*"))
        
        if not document_files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete all files
        deleted_files = []
        for file_path in document_files:
            file_path.unlink()
            deleted_files.append(file_path.name)
        
        return {
            "message": "Document deleted successfully",
            "deleted_files": deleted_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/documents/search", response_model=List[DocumentMetadata])
async def search_documents(
    claim_id: Optional[str] = None,
    document_type: Optional[str] = None,
    has_ocr: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Search documents by various criteria"""
    
    try:
        # List all document files
        document_files = list(UPLOAD_DIR.glob("DOC-*.{pdf,png,jpg,jpeg,tiff,bmp}"))
        
        documents = []
        for file_path in document_files[offset:offset+limit]:
            # Extract document ID from filename
            doc_id = file_path.stem.split('.')[0]
            
            # Check if OCR results exist
            ocr_file = file_path.with_suffix('.ocr.json')
            has_ocr_results = ocr_file.exists()
            
            ocr_confidence = None
            if has_ocr_results:
                try:
                    with open(ocr_file, 'r') as f:
                        import json
                        ocr_data = json.load(f)
                        ocr_confidence = ocr_data.get('confidence')
                except:
                    pass
            
            # Apply filters
            if has_ocr is not None and has_ocr != has_ocr_results:
                continue
            
            document = DocumentMetadata(
                document_id=doc_id,
                filename=file_path.name,
                file_size=file_path.stat().st_size,
                content_type=mimetypes.guess_type(str(file_path))[0] or "unknown",
                upload_date=datetime.fromtimestamp(file_path.stat().st_ctime),
                uploaded_by=current_user.email,  # Simplified
                ocr_processed=has_ocr_results,
                ocr_confidence=ocr_confidence,
                processing_status="completed" if has_ocr_results else "uploaded"
            )
            
            documents.append(document)
        
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")


@router.get("/documents/providers")
async def get_ocr_providers(current_user: User = Depends(get_current_user)):
    """Get available OCR providers and their information"""
    
    return {
        "available_providers": ocr_service.get_available_providers(),
        "provider_info": ocr_service.get_provider_info(),
        "default_provider": ocr_service.default_provider
    }


@router.post("/documents/batch-upload")
async def batch_upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    claim_id: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    process_ocr: bool = Form(True),
    ocr_provider: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Upload multiple documents at once
    
    - **files**: List of document files to upload
    - **claim_id**: Associated claim ID (optional)
    - **document_type**: Type of documents
    - **process_ocr**: Whether to process documents with OCR
    - **ocr_provider**: Specific OCR provider to use
    """
    
    try:
        if len(files) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
        
        results = []
        
        for file in files:
            # Validate file
            validate_file(file)
            
            # Generate document ID
            document_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
            
            # Save file
            file_path = save_uploaded_file(file, document_id)
            file_size = file_path.stat().st_size
            
            # Create response
            response = DocumentUploadResponse(
                document_id=document_id,
                filename=file.filename or "unknown",
                file_size=file_size,
                content_type=file.content_type or "unknown",
                upload_status="success"
            )
            
            # Process OCR if requested
            if process_ocr:
                background_tasks.add_task(
                    process_document_ocr,
                    document_id,
                    file_path,
                    ocr_provider,
                    db
                )
                response.upload_status = "uploaded_processing"
            
            results.append(response)
        
        return {
            "message": f"Successfully uploaded {len(results)} documents",
            "documents": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload documents: {str(e)}")


@router.get("/documents/stats")
async def get_document_stats(current_user: User = Depends(get_current_user)):
    """Get document processing statistics"""
    
    try:
        # Count files by type
        all_files = list(UPLOAD_DIR.glob("DOC-*.*"))
        
        stats = {
            "total_documents": 0,
            "processed_documents": 0,
            "file_types": {},
            "total_size": 0,
            "avg_confidence": 0.0,
            "processing_status": {
                "uploaded": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            }
        }
        
        confidences = []
        
        for file_path in all_files:
            if file_path.suffix in ['.ocr', '.error']:
                continue
                
            stats["total_documents"] += 1
            stats["total_size"] += file_path.stat().st_size
            
            # Count by file type
            ext = file_path.suffix.lower()
            stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
            
            # Check processing status
            doc_id = file_path.stem.split('.')[0]
            ocr_file = UPLOAD_DIR / f"{doc_id}.ocr.json"
            error_file = UPLOAD_DIR / f"{doc_id}.error.json"
            
            if error_file.exists():
                stats["processing_status"]["failed"] += 1
            elif ocr_file.exists():
                stats["processing_status"]["completed"] += 1
                stats["processed_documents"] += 1
                
                # Read confidence
                try:
                    with open(ocr_file, 'r') as f:
                        import json
                        ocr_data = json.load(f)
                        confidence = ocr_data.get('confidence', 0)
                        if confidence > 0:
                            confidences.append(confidence)
                except:
                    pass
            else:
                stats["processing_status"]["uploaded"] += 1
        
        if confidences:
            stats["avg_confidence"] = sum(confidences) / len(confidences)
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")