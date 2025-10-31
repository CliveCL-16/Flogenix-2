"""
OCR Processing Service for Flogenix Platform

This service provides comprehensive OCR (Optical Character Recognition) capabilities
for processing claim documents including medical bills, insurance cards, and forms.

Supports multiple OCR providers:
- Tesseract OCR (Open source, offline)
- Google Cloud Vision API (High accuracy)
- Azure Computer Vision (Enterprise features)
- OpenAI Vision API (AI-powered text extraction)

Features:
- Multi-provider fallback system
- Intelligent text extraction and field detection
- Medical document template recognition
- Confidence scoring and quality validation
- Async processing support
"""

import os
import io
import json
import base64
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import asyncio

from PIL import Image, ImageEnhance
import pytesseract
import cv2
import numpy as np

# Google Cloud Vision (optional)
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

# Azure Computer Vision (optional)
try:
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
    from msrest.authentication import CognitiveServicesCredentials
    AZURE_VISION_AVAILABLE = True
except ImportError:
    AZURE_VISION_AVAILABLE = False

# Gemini AI Vision (optional)
try:
    import google.generativeai as genai
    GEMINI_VISION_AVAILABLE = True
except ImportError:
    GEMINI_VISION_AVAILABLE = False

# OpenAI Vision (optional - kept for compatibility)
try:
    import openai
    OPENAI_VISION_AVAILABLE = True
except ImportError:
    OPENAI_VISION_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """OCR processing result with extracted text and metadata"""
    text: str
    confidence: float
    provider: str
    processing_time: float
    extracted_fields: Dict[str, Any]
    raw_data: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class DocumentField:
    """Extracted document field with location and confidence"""
    name: str
    value: str
    confidence: float
    coordinates: Optional[Dict[str, int]] = None


class OCRService:
    """
    Comprehensive OCR service with multiple provider support
    """
    
    def __init__(self):
        self.providers = {}
        self.default_provider = "tesseract"
        self._setup_providers()
        
        # Medical document field patterns
        self.medical_field_patterns = {
            "patient_name": [
                r"patient\s*name\s*:?\s*([A-Za-z\s,]+)",
                r"name\s*:?\s*([A-Za-z\s,]+)",
                r"patient\s*:?\s*([A-Za-z\s,]+)"
            ],
            "patient_id": [
                r"patient\s*id\s*:?\s*([A-Z0-9]+)",
                r"id\s*:?\s*([A-Z0-9]+)",
                r"member\s*id\s*:?\s*([A-Z0-9]+)"
            ],
            "policy_number": [
                r"policy\s*#?\s*:?\s*([A-Z0-9]+)",
                r"policy\s*number\s*:?\s*([A-Z0-9]+)",
                r"insurance\s*id\s*:?\s*([A-Z0-9]+)"
            ],
            "service_date": [
                r"date\s*of\s*service\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"service\s*date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            ],
            "diagnosis_code": [
                r"diagnosis\s*code\s*:?\s*([A-Z]\d{2}\.?\d*)",
                r"icd\s*-?\s*10\s*:?\s*([A-Z]\d{2}\.?\d*)",
                r"dx\s*:?\s*([A-Z]\d{2}\.?\d*)"
            ],
            "procedure_code": [
                r"procedure\s*code\s*:?\s*(\d{5})",
                r"cpt\s*:?\s*(\d{5})",
                r"hcpcs\s*:?\s*([A-Z0-9]{5})"
            ],
            "amount": [
                r"amount\s*:?\s*\$?(\d+\.?\d*)",
                r"total\s*:?\s*\$?(\d+\.?\d*)",
                r"charge\s*:?\s*\$?(\d+\.?\d*)"
            ],
            "provider_name": [
                r"provider\s*:?\s*([A-Za-z\s,\.]+)",
                r"physician\s*:?\s*([A-Za-z\s,\.]+)",
                r"doctor\s*:?\s*([A-Za-z\s,\.]+)"
            ],
            "insurance_provider": [
                r"insurance\s*:?\s*([A-Za-z\s]+)",
                r"plan\s*:?\s*([A-Za-z\s]+)",
                r"carrier\s*:?\s*([A-Za-z\s]+)"
            ]
        }
    
    def _setup_providers(self):
        """Initialize available OCR providers"""
        
        # Tesseract (always available)
        self.providers["tesseract"] = self._setup_tesseract()
        
        # Google Cloud Vision
        if GOOGLE_VISION_AVAILABLE and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                self.providers["google"] = vision.ImageAnnotatorClient()
                logger.info("Google Cloud Vision API initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Vision: {e}")
        
        # Azure Computer Vision
        if AZURE_VISION_AVAILABLE and os.getenv("AZURE_VISION_KEY"):
            try:
                self.providers["azure"] = ComputerVisionClient(
                    os.getenv("AZURE_VISION_ENDPOINT", ""),
                    CognitiveServicesCredentials(os.getenv("AZURE_VISION_KEY"))
                )
                logger.info("Azure Computer Vision initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure Vision: {e}")
        
        # Gemini Vision
        if GEMINI_VISION_AVAILABLE and os.getenv("GEMINI_API_KEY"):
            try:
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                self.providers["gemini"] = True
                logger.info("Gemini Vision API initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Vision: {e}")
        
        # OpenAI Vision (optional fallback)
        if OPENAI_VISION_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                openai.api_key = os.getenv("OPENAI_API_KEY")
                self.providers["openai"] = True
                logger.info("OpenAI Vision API initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI Vision: {e}")
        
        logger.info(f"OCR providers available: {list(self.providers.keys())}")
    
    def _setup_tesseract(self) -> bool:
        """Setup Tesseract OCR"""
        try:
            # Try to find tesseract executable
            tesseract_path = pytesseract.pytesseract.tesseract_cmd
            if not os.path.exists(tesseract_path):
                # Common installation paths
                possible_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    "/usr/bin/tesseract",
                    "/usr/local/bin/tesseract"
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        break
                else:
                    logger.warning("Tesseract executable not found. Please install Tesseract OCR.")
                    return False
            
            # Test tesseract
            test_image = Image.new('RGB', (100, 30), color='white')
            pytesseract.image_to_string(test_image)
            logger.info("Tesseract OCR initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Tesseract: {e}")
            return False
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy
        """
        try:
            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL to OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
            
            # Convert back to PIL
            processed_image = Image.fromarray(processed)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(processed_image)
            enhanced = enhancer.enhance(1.5)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}. Using original image.")
            return image
    
    async def extract_text_tesseract(self, image: Image.Image) -> OCRResult:
        """Extract text using Tesseract OCR"""
        start_time = datetime.now()
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Configure Tesseract
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/-:()$ '
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            # Get confidence data
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extract structured fields
            extracted_fields = self._extract_medical_fields(text)
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                provider="tesseract",
                processing_time=processing_time,
                extracted_fields=extracted_fields,
                raw_data={"tesseract_data": data}
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Tesseract OCR failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                provider="tesseract",
                processing_time=processing_time,
                extracted_fields={},
                raw_data={},
                error=str(e)
            )
    
    async def extract_text_google(self, image: Image.Image) -> OCRResult:
        """Extract text using Google Cloud Vision API"""
        if "google" not in self.providers:
            return OCRResult(
                text="", confidence=0.0, provider="google",
                processing_time=0.0, extracted_fields={}, raw_data={},
                error="Google Vision API not available"
            )
        
        start_time = datetime.now()
        
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create vision image object
            vision_image = vision.Image(content=img_byte_arr)
            
            # Perform text detection
            client = self.providers["google"]
            response = client.text_detection(image=vision_image)
            
            if response.error.message:
                raise Exception(response.error.message)
            
            texts = response.text_annotations
            
            if not texts:
                extracted_text = ""
                confidence = 0.0
            else:
                extracted_text = texts[0].description
                # Google doesn't provide confidence per text, estimate based on detection
                confidence = 85.0  # Google Vision typically has high confidence
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extract structured fields
            extracted_fields = self._extract_medical_fields(extracted_text)
            
            return OCRResult(
                text=extracted_text.strip(),
                confidence=confidence,
                provider="google",
                processing_time=processing_time,
                extracted_fields=extracted_fields,
                raw_data={"google_response": response.__dict__}
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Google Vision OCR failed: {e}")
            return OCRResult(
                text="", confidence=0.0, provider="google",
                processing_time=processing_time, extracted_fields={}, raw_data={},
                error=str(e)
            )
    
    async def extract_text_gemini(self, image: Image.Image) -> OCRResult:
        """Extract text using Gemini Vision API with intelligent field extraction"""
        if "gemini" not in self.providers:
            return OCRResult(
                text="", confidence=0.0, provider="gemini",
                processing_time=0.0, extracted_fields={}, raw_data={},
                error="Gemini Vision API not available"
            )
        
        start_time = datetime.now()
        
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Initialize Gemini model
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Craft medical document analysis prompt
            prompt = """
            Analyze this medical document image and extract all text and relevant information.
            
            Please provide a detailed extraction in JSON format with these sections:
            1. "text": All readable text content from the document
            2. "fields": Extracted medical claim fields including:
               - patient_name: Patient's full name
               - patient_id: Patient ID or member ID
               - policy_number: Insurance policy number
               - service_date: Date of service (YYYY-MM-DD format)
               - diagnosis_code: ICD-10 diagnosis code
               - procedure_code: CPT procedure code
               - amount: Claim amount or total charge
               - provider_name: Healthcare provider name
               - insurance_provider: Insurance company name
               - provider_npi: National Provider Identifier (if present)
            3. "document_type": Type of document (medical_bill, insurance_card, prescription, etc.)
            4. "confidence": Your confidence in the extraction (0-100)
            
            Only include fields that are clearly visible and readable. Use null for missing fields.
            Ensure dates are in YYYY-MM-DD format and amounts are numeric values only.
            """
            
            # Process with Gemini
            response = model.generate_content([prompt, image])
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Try to parse JSON response
            extracted_fields = {}
            confidence = 85.0  # Default confidence for Gemini
            
            try:
                # Clean the response text to extract JSON
                response_text = response.text
                
                # Find JSON content in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    import json
                    parsed_response = json.loads(json_match.group())
                    
                    extracted_text = parsed_response.get("text", response_text)
                    extracted_fields = parsed_response.get("fields", {})
                    confidence = parsed_response.get("confidence", 85.0)
                    
                    # Clean up extracted fields (remove null values and empty strings)
                    extracted_fields = {k: v for k, v in extracted_fields.items() 
                                      if v is not None and str(v).strip()}
                else:
                    # Fallback to pattern extraction if JSON parsing fails
                    extracted_text = response_text
                    extracted_fields = self._extract_medical_fields(response_text)
                    
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse Gemini JSON response: {e}")
                extracted_text = response.text
                # Fall back to pattern extraction
                extracted_fields = self._extract_medical_fields(response.text)
            
            return OCRResult(
                text=extracted_text.strip(),
                confidence=confidence,
                provider="gemini",
                processing_time=processing_time,
                extracted_fields=extracted_fields,
                raw_data={"gemini_response": response.text}
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Gemini Vision OCR failed: {e}")
            return OCRResult(
                text="", confidence=0.0, provider="gemini",
                processing_time=processing_time, extracted_fields={}, raw_data={},
                error=str(e)
            )
    
    async def extract_text_openai(self, image: Image.Image) -> OCRResult:
        """Extract text using OpenAI Vision API with intelligent field extraction"""
        if "openai" not in self.providers:
            return OCRResult(
                text="", confidence=0.0, provider="openai",
                processing_time=0.0, extracted_fields={}, raw_data={},
                error="OpenAI Vision API not available"
            )
        
        start_time = datetime.now()
        
        try:
            # Convert image to base64
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
            
            # Create OpenAI client
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Craft medical document analysis prompt
            prompt = """
            Analyze this medical document and extract all text and relevant information.
            
            Please provide:
            1. All text content (preserve formatting where possible)
            2. Extract these specific fields if present:
               - Patient Name
               - Patient ID
               - Policy Number
               - Service Date
               - Diagnosis Code (ICD-10)
               - Procedure Code (CPT)
               - Amount/Charge
               - Provider Name
               - Insurance Provider
            
            Return response in JSON format with 'text' and 'fields' sections.
            """
            
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Try to parse JSON response
            extracted_fields = {}
            try:
                parsed_response = json.loads(content)
                extracted_text = parsed_response.get("text", content)
                extracted_fields = parsed_response.get("fields", {})
            except json.JSONDecodeError:
                extracted_text = content
                # Fall back to pattern extraction
                extracted_fields = self._extract_medical_fields(content)
            
            # OpenAI Vision typically has high confidence
            confidence = 90.0
            
            return OCRResult(
                text=extracted_text.strip(),
                confidence=confidence,
                provider="openai",
                processing_time=processing_time,
                extracted_fields=extracted_fields,
                raw_data={"openai_response": response.__dict__}
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"OpenAI Vision OCR failed: {e}")
            return OCRResult(
                text="", confidence=0.0, provider="openai",
                processing_time=processing_time, extracted_fields={}, raw_data={},
                error=str(e)
            )
    
    def _extract_medical_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract medical claim fields from text using regex patterns
        """
        import re
        
        extracted_fields = {}
        text_lower = text.lower()
        
        for field_name, patterns in self.medical_field_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean up the value
                    value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
                    extracted_fields[field_name] = value
                    break  # Use first match
        
        return extracted_fields
    
    async def process_document(
        self, 
        image_data: Union[bytes, Image.Image], 
        provider: Optional[str] = None,
        fallback: bool = True
    ) -> OCRResult:
        """
        Process document with specified or best available OCR provider
        
        Args:
            image_data: Image bytes or PIL Image
            provider: Specific provider to use ('tesseract', 'google', 'azure', 'openai')
            fallback: Whether to try alternative providers if primary fails
            
        Returns:
            OCRResult with extracted text and fields
        """
        
        # Convert bytes to PIL Image if needed
        if isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        else:
            image = image_data
        
        # Determine provider order
        provider_order = []
        if provider and provider in self.providers:
            provider_order.append(provider)
        
        if fallback:
            # Add remaining providers in order of preference
            preferred_order = ["gemini", "openai", "google", "azure", "tesseract"]
            for prov in preferred_order:
                if prov in self.providers and prov not in provider_order:
                    provider_order.append(prov)
        
        if not provider_order:
            provider_order = [self.default_provider]
        
        # Try providers in order
        last_error = None
        for prov in provider_order:
            try:
                logger.info(f"Trying OCR with provider: {prov}")
                
                if prov == "tesseract":
                    result = await self.extract_text_tesseract(image)
                elif prov == "google":
                    result = await self.extract_text_google(image)
                elif prov == "gemini":
                    result = await self.extract_text_gemini(image)
                elif prov == "openai":
                    result = await self.extract_text_openai(image)
                else:
                    continue
                
                # Check if result is usable
                if result.error is None and (result.text.strip() or result.extracted_fields):
                    logger.info(f"OCR successful with {prov}: {result.confidence:.1f}% confidence")
                    return result
                
                last_error = result.error
                
            except Exception as e:
                logger.warning(f"OCR provider {prov} failed: {e}")
                last_error = str(e)
                continue
        
        # If all providers failed, return error result
        return OCRResult(
            text="",
            confidence=0.0,
            provider="failed",
            processing_time=0.0,
            extracted_fields={},
            raw_data={},
            error=f"All OCR providers failed. Last error: {last_error}"
        )
    
    async def process_claim_documents(
        self, 
        documents: List[Union[bytes, Image.Image]]
    ) -> List[OCRResult]:
        """
        Process multiple claim documents concurrently
        
        Args:
            documents: List of images (bytes or PIL Images)
            
        Returns:
            List of OCRResult objects
        """
        
        tasks = []
        for i, doc in enumerate(documents):
            task = self.process_document(doc, provider=None, fallback=True)
            tasks.append(task)
        
        # Process all documents concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(OCRResult(
                    text="",
                    confidence=0.0,
                    provider="error",
                    processing_time=0.0,
                    extracted_fields={},
                    raw_data={},
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def validate_extracted_fields(self, fields: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate extracted medical fields for completeness and format
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ["patient_name", "service_date"]
        for field in required_fields:
            if field not in fields or not fields[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate specific field formats
        if "diagnosis_code" in fields:
            import re
            code = fields["diagnosis_code"]
            if not re.match(r'^[A-Z]\d{2}\.?\d*$', code):
                errors.append(f"Invalid diagnosis code format: {code}")
        
        if "procedure_code" in fields:
            code = fields["procedure_code"]
            if not re.match(r'^\d{5}$', code):
                errors.append(f"Invalid procedure code format: {code}")
        
        if "amount" in fields:
            try:
                amount = float(fields["amount"].replace("$", "").replace(",", ""))
                if amount <= 0:
                    errors.append("Amount must be greater than 0")
            except ValueError:
                errors.append(f"Invalid amount format: {fields['amount']}")
        
        return len(errors) == 0, errors
    
    def get_available_providers(self) -> List[str]:
        """Get list of available OCR providers"""
        return list(self.providers.keys())
    
    def get_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available providers"""
        info = {}
        
        for provider in self.providers.keys():
            if provider == "tesseract":
                info[provider] = {
                    "name": "Tesseract OCR",
                    "type": "Open Source",
                    "cost": "Free",
                    "accuracy": "Good",
                    "speed": "Fast",
                    "features": ["Offline", "No API limits"]
                }
            elif provider == "gemini":
                info[provider] = {
                    "name": "Google Gemini Vision",
                    "type": "AI API",
                    "cost": "Pay per use",
                    "accuracy": "Excellent",
                    "speed": "Fast",
                    "features": ["AI-powered", "Context understanding", "Structured extraction", "Medical document specialization"]
                }
            elif provider == "google":
                info[provider] = {
                    "name": "Google Cloud Vision",
                    "type": "Cloud API",
                    "cost": "Pay per use",
                    "accuracy": "Excellent",
                    "speed": "Fast",
                    "features": ["High accuracy", "Multiple languages"]
                }
            elif provider == "azure":
                info[provider] = {
                    "name": "Azure Computer Vision",
                    "type": "Cloud API",
                    "cost": "Pay per use",
                    "accuracy": "Excellent",
                    "speed": "Fast",
                    "features": ["Enterprise features", "High accuracy"]
                }
            elif provider == "openai":
                info[provider] = {
                    "name": "OpenAI Vision",
                    "type": "AI API",
                    "cost": "Pay per use",
                    "accuracy": "Excellent",
                    "speed": "Medium",
                    "features": ["AI-powered", "Context understanding", "Structured extraction"]
                }
        
        return info


# Global OCR service instance
ocr_service = OCRService()


# Utility functions for easy access
async def extract_text_from_image(
    image_data: Union[bytes, Image.Image], 
    provider: Optional[str] = None
) -> OCRResult:
    """Convenience function to extract text from image"""
    return await ocr_service.process_document(image_data, provider)


async def process_claim_document(image_data: Union[bytes, Image.Image]) -> Dict[str, Any]:
    """
    Process a claim document and return structured data
    
    Returns:
        Dictionary with extracted text, fields, and processing metadata
    """
    result = await ocr_service.process_document(image_data)
    
    return {
        "text": result.text,
        "fields": result.extracted_fields,
        "confidence": result.confidence,
        "provider": result.provider,
        "processing_time": result.processing_time,
        "success": result.error is None,
        "error": result.error
    }