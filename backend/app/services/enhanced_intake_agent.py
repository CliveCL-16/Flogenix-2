"""
Enhanced Intake Agent with OCR Document Processing

This module extends the basic intake agent to include OCR document processing
capabilities, allowing for automatic extraction of claim information from
uploaded documents.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from app.models import ClaimState, AgentReport, AgentStatus, ReasoningStep, ToolUsage
from app.services.ocr_service import ocr_service
from app.services.gemini_service import gemini_service
from app.services.agent_tools import validate_required_fields, extract_entities

logger = logging.getLogger(__name__)


class EnhancedIntakeAgent:
    """
    Enhanced intake agent with OCR document processing capabilities
    """
    
    def __init__(self):
        self.agent_name = "Enhanced Intake Agent"
        self.agent_type = "intake"
        self.ocr_service = ocr_service
        self.ai_service = gemini_service
        
    async def process_claim_with_documents(
        self, 
        state: ClaimState,
        document_paths: List[str] = None
    ) -> ClaimState:
        """
        Process claim with optional document OCR processing
        
        Args:
            state: Current claim state
            document_paths: List of paths to claim documents
            
        Returns:
            Updated claim state with OCR-extracted information
        """
        
        start_time = time.time()
        agent_report = AgentReport(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            status=AgentStatus.IN_PROGRESS,
            started_at=datetime.now(),
            reasoning_steps=[],
            tools_used=[]
        )
        
        try:
            # Step 1: Basic intake validation
            await self._add_reasoning_step(
                agent_report,
                "REASON",
                "Starting enhanced intake processing with document analysis capability"
            )
            
            # Get existing claim data
            claim_data = state.claim_data.copy()
            original_completeness = self._calculate_completeness(claim_data)
            
            await self._add_reasoning_step(
                agent_report,
                "OBSERVE",
                f"Original claim data completeness: {original_completeness:.1f}%"
            )
            
            # Step 2: Process documents if provided
            extracted_data = {}
            if document_paths:
                await self._add_reasoning_step(
                    agent_report,
                    "ACT",
                    f"Processing {len(document_paths)} document(s) with OCR"
                )
                
                extracted_data = await self._process_documents(
                    document_paths, agent_report
                )
            
            # Step 3: Merge OCR data with existing claim data
            if extracted_data:
                merged_data = await self._merge_claim_data(
                    claim_data, extracted_data, agent_report
                )
                state.claim_data.update(merged_data)
                
                new_completeness = self._calculate_completeness(state.claim_data)
                await self._add_reasoning_step(
                    agent_report,
                    "OBSERVE",
                    f"After OCR merge, completeness improved to: {new_completeness:.1f}%"
                )
            
            # Step 4: Enhanced validation with AI reasoning
            validation_result = await self._enhanced_validation(
                state.claim_data, agent_report
            )
            
            # Step 5: Entity extraction and enhancement
            entity_result = await self._enhanced_entity_extraction(
                state.claim_data, agent_report
            )
            
            # Step 6: Final quality assessment
            quality_score = await self._assess_data_quality(
                state.claim_data, agent_report
            )
            
            # Update state
            state.intake_completed = True
            
            # Complete agent report
            end_time = time.time()
            agent_report.status = AgentStatus.COMPLETED
            agent_report.completed_at = datetime.now()
            agent_report.duration_seconds = end_time - start_time
            agent_report.result = "COMPLETE"
            agent_report.confidence_score = quality_score
            
            await self._add_reasoning_step(
                agent_report,
                "COMPLETE",
                f"Enhanced intake completed with {quality_score:.1f}% confidence"
            )
            
            # Add report to state
            state.agent_reports.append(agent_report)
            
            return state
            
        except Exception as e:
            # Handle errors
            end_time = time.time()
            agent_report.status = AgentStatus.FAILED
            agent_report.completed_at = datetime.now()
            agent_report.duration_seconds = end_time - start_time
            agent_report.result = "FAILED"
            agent_report.error_message = str(e)
            
            await self._add_reasoning_step(
                agent_report,
                "ERROR",
                f"Enhanced intake failed: {str(e)}"
            )
            
            state.agent_reports.append(agent_report)
            logger.error(f"Enhanced intake agent failed: {e}")
            
            return state
    
    async def _process_documents(
        self, 
        document_paths: List[str], 
        agent_report: AgentReport
    ) -> Dict[str, Any]:
        """
        Process documents with OCR and extract claim-relevant information
        """
        
        extracted_data = {}
        
        for i, doc_path in enumerate(document_paths):
            try:
                # Log processing start
                tool_usage = ToolUsage(
                    tool_name="ocr_processor",
                    parameters={"document_path": doc_path},
                    result="",
                    success=False,
                    timestamp=datetime.now()
                )
                
                await self._add_reasoning_step(
                    agent_report,
                    "ACT",
                    f"Processing document {i+1}: {Path(doc_path).name}"
                )
                
                # Read and process document
                with open(doc_path, 'rb') as f:
                    image_data = f.read()
                
                # Process with OCR
                ocr_result = await self.ocr_service.process_document(
                    image_data=image_data,
                    provider=None,  # Use best available
                    fallback=True
                )
                
                if ocr_result.error:
                    tool_usage.result = f"OCR failed: {ocr_result.error}"
                    tool_usage.success = False
                    
                    await self._add_reasoning_step(
                        agent_report,
                        "OBSERVE",
                        f"OCR processing failed for document {i+1}: {ocr_result.error}"
                    )
                else:
                    # OCR successful
                    tool_usage.result = f"Extracted {len(ocr_result.text)} characters with {ocr_result.confidence:.1f}% confidence"
                    tool_usage.success = True
                    
                    await self._add_reasoning_step(
                        agent_report,
                        "OBSERVE",
                        f"OCR successful: {len(ocr_result.text)} chars, {ocr_result.confidence:.1f}% confidence"
                    )
                    
                    # Merge extracted fields
                    for field, value in ocr_result.extracted_fields.items():
                        if value and value.strip():
                            # Use highest confidence value if field already exists
                            if field in extracted_data:
                                existing_conf = extracted_data.get(f"{field}_confidence", 0)
                                if ocr_result.confidence > existing_conf:
                                    extracted_data[field] = value
                                    extracted_data[f"{field}_confidence"] = ocr_result.confidence
                                    extracted_data[f"{field}_source"] = f"document_{i+1}"
                            else:
                                extracted_data[field] = value
                                extracted_data[f"{field}_confidence"] = ocr_result.confidence
                                extracted_data[f"{field}_source"] = f"document_{i+1}"
                
                agent_report.tools_used.append(tool_usage)
                
            except Exception as e:
                tool_usage.result = f"Document processing error: {str(e)}"
                tool_usage.success = False
                agent_report.tools_used.append(tool_usage)
                
                await self._add_reasoning_step(
                    agent_report,
                    "ERROR",
                    f"Failed to process document {i+1}: {str(e)}"
                )
                
                logger.error(f"Document processing failed for {doc_path}: {e}")
        
        await self._add_reasoning_step(
            agent_report,
            "OBSERVE",
            f"OCR processing complete. Extracted {len(extracted_data)} fields"
        )
        
        return extracted_data
    
    async def _merge_claim_data(
        self, 
        original_data: Dict[str, Any], 
        extracted_data: Dict[str, Any],
        agent_report: AgentReport
    ) -> Dict[str, Any]:
        """
        Intelligently merge original claim data with OCR-extracted data
        """
        
        merged_data = original_data.copy()
        merge_actions = []
        
        # Define field mappings and priorities
        field_mappings = {
            "patient_name": ["patient_name", "name"],
            "patient_id": ["patient_id", "member_id", "id"],
            "policy_number": ["policy_number", "policy", "insurance_id"],
            "diagnosis_code": ["diagnosis_code", "icd_code", "dx"],
            "procedure_code": ["procedure_code", "cpt_code", "procedure"],
            "claim_amount": ["amount", "charge", "total"],
            "service_date": ["service_date", "date"],
            "provider_name": ["provider_name", "provider", "physician", "doctor"],
            "insurance_provider": ["insurance_provider", "insurance", "plan", "carrier"]
        }
        
        for target_field, source_fields in field_mappings.items():
            # Check if we have extracted data for this field
            extracted_value = None
            best_confidence = 0
            best_source = None
            
            for source_field in source_fields:
                if source_field in extracted_data:
                    confidence = extracted_data.get(f"{source_field}_confidence", 70)
                    if confidence > best_confidence:
                        extracted_value = extracted_data[source_field]
                        best_confidence = confidence
                        best_source = extracted_data.get(f"{source_field}_source", "OCR")
            
            if extracted_value:
                # Decide whether to use extracted value
                original_value = merged_data.get(target_field)
                
                if not original_value or original_value.strip() == "":
                    # No original value, use extracted
                    merged_data[target_field] = extracted_value
                    merge_actions.append(f"Added {target_field} from {best_source}")
                    
                elif best_confidence > 80 and original_value != extracted_value:
                    # High confidence extraction that differs from original
                    # Use AI to decide which is better
                    decision = await self._ai_resolve_field_conflict(
                        target_field, original_value, extracted_value, best_confidence
                    )
                    
                    if decision == "use_extracted":
                        merged_data[target_field] = extracted_value
                        merge_actions.append(f"Replaced {target_field} with OCR value (high confidence)")
                    else:
                        merge_actions.append(f"Kept original {target_field} (AI decision)")
                
                else:
                    # Keep original value
                    merge_actions.append(f"Kept original {target_field}")
        
        # Log merge actions
        if merge_actions:
            await self._add_reasoning_step(
                agent_report,
                "ACT",
                f"Data merge completed: {'; '.join(merge_actions)}"
            )
        
        return merged_data
    
    async def _ai_resolve_field_conflict(
        self, 
        field_name: str, 
        original_value: str, 
        extracted_value: str, 
        extraction_confidence: float
    ) -> str:
        """
        Use AI to resolve conflicts between original and extracted field values
        """
        
        if not self.ai_service:
            # No AI available, use confidence-based decision
            return "use_extracted" if extraction_confidence > 85 else "keep_original"
        
        try:
            prompt = f"""
            Analyze these conflicting values for the field '{field_name}' in a medical claim:
            
            Original value: "{original_value}"
            OCR extracted value: "{extracted_value}"
            OCR confidence: {extraction_confidence}%
            
            Which value appears more accurate for a medical claim? Consider:
            1. Format correctness (e.g., proper medical codes, dates, names)
            2. OCR confidence level
            3. Typical patterns in medical claims
            
            Respond with either "use_extracted" or "keep_original" and briefly explain why.
            """
            
            response = await self.ai_service.generate_response(prompt)
            
            if "use_extracted" in response.lower():
                return "use_extracted"
            else:
                return "keep_original"
                
        except Exception as e:
            logger.warning(f"AI field conflict resolution failed: {e}")
            # Fallback to confidence-based decision
            return "use_extracted" if extraction_confidence > 85 else "keep_original"
    
    async def _enhanced_validation(
        self, 
        claim_data: Dict[str, Any], 
        agent_report: AgentReport
    ) -> Dict[str, Any]:
        """
        Enhanced validation using AI reasoning
        """
        
        # Use existing validation tools
        tool_usage = ToolUsage(
            tool_name="validate_required_fields",
            parameters={"claim_data": claim_data},
            result="",
            success=False,
            timestamp=datetime.now()
        )
        
        try:
            validation_result = validate_required_fields(claim_data)
            tool_usage.result = str(validation_result)
            tool_usage.success = True
            
            await self._add_reasoning_step(
                agent_report,
                "ACT",
                "Running enhanced field validation"
            )
            
            # Additional AI-powered validation if available
            if self.ai_service:
                ai_validation = await self._ai_validate_claim_data(claim_data)
                validation_result.update(ai_validation)
                
                await self._add_reasoning_step(
                    agent_report,
                    "OBSERVE",
                    f"AI validation identified {len(ai_validation.get('issues', []))} additional issues"
                )
            
        except Exception as e:
            tool_usage.result = f"Validation error: {str(e)}"
            tool_usage.success = False
            validation_result = {"error": str(e)}
        
        agent_report.tools_used.append(tool_usage)
        return validation_result
    
    async def _enhanced_entity_extraction(
        self, 
        claim_data: Dict[str, Any], 
        agent_report: AgentReport
    ) -> Dict[str, Any]:
        """
        Enhanced entity extraction with AI analysis
        """
        
        tool_usage = ToolUsage(
            tool_name="extract_entities",
            parameters={"claim_data": claim_data},
            result="",
            success=False,
            timestamp=datetime.now()
        )
        
        try:
            entity_result = extract_entities(claim_data)
            tool_usage.result = str(entity_result)
            tool_usage.success = True
            
            await self._add_reasoning_step(
                agent_report,
                "ACT",
                "Extracting and analyzing claim entities"
            )
            
            await self._add_reasoning_step(
                agent_report,
                "OBSERVE",
                f"Extracted {entity_result.get('total_entities', 0)} entities"
            )
            
        except Exception as e:
            tool_usage.result = f"Entity extraction error: {str(e)}"
            tool_usage.success = False
            entity_result = {"error": str(e)}
        
        agent_report.tools_used.append(tool_usage)
        return entity_result
    
    async def _ai_validate_claim_data(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to perform additional validation on claim data
        """
        
        if not self.ai_service:
            return {}
        
        try:
            prompt = f"""
            Analyze this medical claim data for potential issues:
            
            {claim_data}
            
            Check for:
            1. Consistency between diagnosis and procedure codes
            2. Reasonable claim amounts for the procedures
            3. Proper date formats and logical dates
            4. Valid medical code formats (ICD-10, CPT)
            5. Completeness of required information
            
            Return a JSON object with:
            - "issues": list of identified problems
            - "suggestions": list of recommended fixes
            - "confidence": overall data quality score (0-100)
            """
            
            response = await self.ai_service.generate_response(prompt)
            
            # Try to parse JSON response
            import json
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback to text analysis
                return {
                    "issues": [],
                    "suggestions": [response],
                    "confidence": 75
                }
                
        except Exception as e:
            logger.warning(f"AI validation failed: {e}")
            return {}
    
    async def _assess_data_quality(
        self, 
        claim_data: Dict[str, Any], 
        agent_report: AgentReport
    ) -> float:
        """
        Assess overall data quality and return confidence score
        """
        
        quality_score = 0.0
        max_score = 100.0
        
        # Completeness score (40% of total)
        completeness = self._calculate_completeness(claim_data)
        quality_score += (completeness / 100.0) * 40
        
        # Format validation score (30% of total)
        format_score = self._validate_formats(claim_data)
        quality_score += (format_score / 100.0) * 30
        
        # Consistency score (30% of total)
        consistency_score = await self._check_consistency(claim_data)
        quality_score += (consistency_score / 100.0) * 30
        
        await self._add_reasoning_step(
            agent_report,
            "OBSERVE",
            f"Data quality assessment: {quality_score:.1f}% (completeness: {completeness:.1f}%, format: {format_score:.1f}%, consistency: {consistency_score:.1f}%)"
        )
        
        return min(quality_score, max_score)
    
    def _calculate_completeness(self, claim_data: Dict[str, Any]) -> float:
        """Calculate data completeness percentage"""
        
        required_fields = [
            "patient_name", "patient_id", "insurance_provider", "policy_number",
            "diagnosis_code", "procedure_code", "service_date", "claim_amount", "provider_name"
        ]
        
        completed_fields = 0
        for field in required_fields:
            value = claim_data.get(field)
            if value and str(value).strip():
                completed_fields += 1
        
        return (completed_fields / len(required_fields)) * 100
    
    def _validate_formats(self, claim_data: Dict[str, Any]) -> float:
        """Validate field formats and return score"""
        
        import re
        
        format_checks = 0
        passed_checks = 0
        
        # Diagnosis code format (ICD-10)
        diagnosis = claim_data.get("diagnosis_code", "")
        format_checks += 1
        if re.match(r'^[A-Z]\d{2}\.?\d*$', diagnosis):
            passed_checks += 1
        
        # Procedure code format (CPT)
        procedure = claim_data.get("procedure_code", "")
        format_checks += 1
        if re.match(r'^\d{5}$', procedure):
            passed_checks += 1
        
        # Claim amount format
        amount = claim_data.get("claim_amount")
        format_checks += 1
        if isinstance(amount, (int, float)) and amount > 0:
            passed_checks += 1
        
        # NPI format (if provided)
        npi = claim_data.get("provider_npi", "")
        if npi:
            format_checks += 1
            if re.match(r'^\d{10}$', npi):
                passed_checks += 1
        
        return (passed_checks / format_checks) * 100 if format_checks > 0 else 100
    
    async def _check_consistency(self, claim_data: Dict[str, Any]) -> float:
        """Check data consistency using AI if available"""
        
        if not self.ai_service:
            return 85.0  # Default score when AI not available
        
        try:
            prompt = f"""
            Rate the consistency of this medical claim data on a scale of 0-100:
            
            Diagnosis: {claim_data.get('diagnosis_code', 'Not provided')}
            Procedure: {claim_data.get('procedure_code', 'Not provided')}
            Amount: ${claim_data.get('claim_amount', 'Not provided')}
            Provider: {claim_data.get('provider_name', 'Not provided')}
            
            Consider:
            - Do the diagnosis and procedure codes make medical sense together?
            - Is the claim amount reasonable for this type of procedure?
            - Are there any obvious inconsistencies?
            
            Respond with just a number between 0-100.
            """
            
            response = await self.ai_service.generate_response(prompt)
            
            # Extract number from response
            import re
            match = re.search(r'\b(\d{1,3})\b', response)
            if match:
                score = int(match.group(1))
                return min(max(score, 0), 100)  # Clamp between 0-100
            
            return 85.0  # Default if no number found
            
        except Exception as e:
            logger.warning(f"AI consistency check failed: {e}")
            return 85.0  # Default score
    
    async def _add_reasoning_step(
        self, 
        agent_report: AgentReport, 
        step_type: str, 
        text: str
    ):
        """Add a reasoning step to the agent report"""
        
        step = ReasoningStep(
            step=len(agent_report.reasoning_steps) + 1,
            type=step_type,
            text=text,
            timestamp=datetime.now()
        )
        
        agent_report.reasoning_steps.append(step)


# Global instance for easy access
enhanced_intake_agent = EnhancedIntakeAgent()