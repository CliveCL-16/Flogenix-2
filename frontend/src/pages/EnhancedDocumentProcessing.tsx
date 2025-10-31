import React, { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Upload, FileText, Image, FileCheck, AlertTriangle, CheckCircle, Eye, Download, Trash2, RefreshCw, Zap, Camera, Scan, Edit, Copy, X, Plus } from 'lucide-react';
import { apiClient } from '@/lib/api';

// Document processing interfaces
interface DocumentUpload {
  id: string;
  file: File;
  fileName: string;
  fileSize: number;
  fileType: string;
  uploadProgress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  claimId?: string;
  documentType: 'medical_record' | 'invoice' | 'prescription' | 'insurance_card' | 'id_document' | 'other';
}

interface OCRResult {
  id: string;
  documentId: string;
  confidence: number;
  processingTime: number;
  extractedText: string;
  structuredData: {
    patient_name?: string;
    patient_id?: string;
    date_of_service?: string;
    procedure_codes?: string[];
    diagnosis_codes?: string[];
    provider_name?: string;
    claim_amount?: number;
    insurance_provider?: string;
    policy_number?: string;
    [key: string]: any;
  };
  confidence_scores: {
    overall: number;
    fields: Record<string, number>;
  };
  validation_results: {
    field: string;
    status: 'valid' | 'invalid' | 'uncertain';
    confidence: number;
    suggestion?: string;
  }[];
  detected_anomalies: string[];
  quality_metrics: {
    image_quality: number;
    text_clarity: number;
    completeness: number;
    format_compliance: number;
  };
}

interface DocumentValidation {
  documentId: string;
  validation_status: 'passed' | 'failed' | 'needs_review';
  compliance_checks: {
    check_name: string;
    status: 'passed' | 'failed' | 'warning';
    details: string;
  }[];
  security_scan: {
    threats_detected: string[];
    safety_score: number;
  };
  data_quality: {
    completeness: number;
    accuracy: number;
    consistency: number;
  };
  recommendations: string[];
}

interface DocumentPreview {
  documentId: string;
  previewUrl: string;
  thumbnailUrl: string;
  pages: number;
  annotations: Array<{
    id: string;
    type: 'highlight' | 'box' | 'comment';
    page: number;
    coordinates: { x: number; y: number; width: number; height: number };
    content: string;
    confidence?: number;
  }>;
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getDocumentIcon = (fileType: string) => {
  if (fileType.startsWith('image/')) return <Image className="h-4 w-4" />;
  return <FileText className="h-4 w-4" />;
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed':
    case 'passed':
    case 'valid':
      return 'bg-green-100 text-green-800';
    case 'processing':
    case 'uploading':
    case 'needs_review':
    case 'uncertain':
      return 'bg-blue-100 text-blue-800';
    case 'failed':
    case 'invalid':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.9) return 'text-green-600';
  if (confidence >= 0.7) return 'text-yellow-600';
  return 'text-red-600';
};

export default function EnhancedDocumentProcessing() {
  const [uploads, setUploads] = useState<DocumentUpload[]>([]);
  const [ocrResults, setOcrResults] = useState<Record<string, OCRResult>>({});
  const [validationResults, setValidationResults] = useState<Record<string, DocumentValidation>>({});
  const [documentPreviews, setDocumentPreviews] = useState<Record<string, DocumentPreview>>({});
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [processingQueue, setProcessingQueue] = useState<string[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [selectedClaimId, setSelectedClaimId] = useState<string>('');
  const [batchProcessing, setBatchProcessing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // File upload handling
  const handleFiles = useCallback(async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    
    for (const file of fileArray) {
      // Validate file type and size
      if (!isValidFileType(file.type)) {
        alert(`File type ${file.type} is not supported`);
        continue;
      }
      
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        alert(`File ${file.name} is too large. Maximum size is 10MB`);
        continue;
      }

      const documentId = `doc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      const newUpload: DocumentUpload = {
        id: documentId,
        file,
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        uploadProgress: 0,
        status: 'uploading',
        claimId: selectedClaimId || undefined,
        documentType: detectDocumentType(file.name)
      };

      setUploads(prev => [...prev, newUpload]);
      
      // Start upload and processing
      await uploadDocument(newUpload);
    }
  }, [selectedClaimId]);

  const isValidFileType = (fileType: string): boolean => {
    const allowedTypes = [
      'application/pdf',
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/tiff',
      'image/bmp',
      'text/plain',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    return allowedTypes.includes(fileType);
  };

  const detectDocumentType = (fileName: string): DocumentUpload['documentType'] => {
    const name = fileName.toLowerCase();
    if (name.includes('medical') || name.includes('record')) return 'medical_record';
    if (name.includes('invoice') || name.includes('bill')) return 'invoice';
    if (name.includes('prescription') || name.includes('rx')) return 'prescription';
    if (name.includes('insurance') || name.includes('card')) return 'insurance_card';
    if (name.includes('id') || name.includes('license')) return 'id_document';
    return 'other';
  };

  const uploadDocument = async (upload: DocumentUpload) => {
    try {
      // Simulate upload progress
      for (let progress = 0; progress <= 100; progress += 20) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setUploads(prev => prev.map(u => 
          u.id === upload.id ? { ...u, uploadProgress: progress } : u
        ));
      }

      // Update status to processing
      setUploads(prev => prev.map(u => 
        u.id === upload.id ? { ...u, status: 'processing' } : u
      ));

      // Add to processing queue
      setProcessingQueue(prev => [...prev, upload.id]);

      // Start OCR processing
      await processDocumentOCR(upload);
      
    } catch (error) {
      console.error('Upload failed:', error);
      setUploads(prev => prev.map(u => 
        u.id === upload.id ? { ...u, status: 'failed' } : u
      ));
    }
  };

  const processDocumentOCR = async (upload: DocumentUpload) => {
    try {
      // Get real OCR results from backend
      const ocrResults = await apiClient.getDocumentOCRResults(upload.id);
      
      // Convert backend response to frontend format
      const ocrResult: OCRResult = {
        id: `ocr-${upload.id}`,
        documentId: upload.id,
        confidence: ocrResults.confidence,
        processingTime: ocrResults.processing_time,
        extractedText: ocrResults.extracted_text,
        structuredData: ocrResults.extracted_data,
        confidence_scores: {
          overall: ocrResults.confidence,
          fields: ocrResults.field_confidence || {}
        },
        validation_results: ocrResults.validation_results || [],
        detected_anomalies: ocrResults.detected_anomalies || [],
        quality_metrics: ocrResults.quality_metrics || {
          image_quality: 0.9,
          text_clarity: 0.85,
          completeness: 0.92,
          format_compliance: 0.88
        }
      };

      setOcrResults(prev => [...prev, ocrResult]);

      // Get document validation
      const validationResult = await apiClient.getDocumentValidation(upload.id);
      
      const validation: DocumentValidation = {
        documentId: upload.id,
        validation_status: validationResult.status,
        compliance_checks: validationResult.compliance_checks || [],
        security_scan: validationResult.security_scan || {
          threats_detected: [],
          safety_score: 1.0
        },
        data_quality: validationResult.data_quality || {
          completeness: 0.9,
          accuracy: 0.85,
          consistency: 0.92
        },
        recommendations: validationResult.recommendations || []
      };

      setValidationResults(prev => [...prev, validation]);
        detected_anomalies: [],
        quality_metrics: {
          image_quality: 0.91,
          text_clarity: 0.88,
          completeness: 0.94,
          format_compliance: 0.87
        }
      };

      setOcrResults(prev => ({ ...prev, [upload.id]: mockOCRResult }));

      // Generate document validation
      const mockValidation: DocumentValidation = {
        documentId: upload.id,
        validation_status: 'passed',
        compliance_checks: [
          { check_name: 'HIPAA Compliance', status: 'passed', details: 'All privacy requirements met' },
          { check_name: 'Data Completeness', status: 'passed', details: 'All required fields present' },
          { check_name: 'Format Validation', status: 'warning', details: 'Some fields need verification' }
        ],
        security_scan: {
          threats_detected: [],
          safety_score: 0.96
        },
        data_quality: {
          completeness: 0.94,
          accuracy: 0.87,
          consistency: 0.91
        },
        recommendations: [
          'Verify procedure codes against latest CPT standards',
          'Cross-reference patient information with existing records'
        ]
      };

      setValidationResults(prev => ({ ...prev, [upload.id]: mockValidation }));

      // Generate document preview
      const mockPreview: DocumentPreview = {
        documentId: upload.id,
        previewUrl: URL.createObjectURL(upload.file),
        thumbnailUrl: URL.createObjectURL(upload.file),
        pages: 1,
        annotations: [
          {
            id: 'ann-1',
            type: 'highlight',
            page: 1,
            coordinates: { x: 50, y: 100, width: 200, height: 20 },
            content: 'Patient Name',
            confidence: 0.95
          },
          {
            id: 'ann-2',
            type: 'box',
            page: 1,
            coordinates: { x: 50, y: 150, width: 150, height: 30 },
            content: 'Claim Amount',
            confidence: 0.89
          }
        ]
      };

      setDocumentPreviews(prev => ({ ...prev, [upload.id]: mockPreview }));

      // Update upload status
      setUploads(prev => prev.map(u => 
        u.id === upload.id ? { ...u, status: 'completed' } : u
      ));

      // Remove from processing queue
      setProcessingQueue(prev => prev.filter(id => id !== upload.id));

    } catch (error) {
      console.error('OCR processing failed:', error);
      setUploads(prev => prev.map(u => 
        u.id === upload.id ? { ...u, status: 'failed' } : u
      ));
      setProcessingQueue(prev => prev.filter(id => id !== upload.id));
    }
  };

  const generateMockExtractedText = (docType: DocumentUpload['documentType']): string => {
    switch (docType) {
      case 'medical_record':
        return 'PATIENT: John Doe\nDATE: 01/15/2024\nDIAGNOSIS: M54.2 - Cervicalgia\nPROCEDURE: 97110 - Therapeutic exercises\nPROVIDER: Dr. Smith\nAMOUNT: $250.00';
      case 'invoice':
        return 'INVOICE #12345\nDATE: 01/15/2024\nPATIENT: John Doe\nSERVICE: Physical Therapy\nAMOUNT: $250.00\nINSURANCE: Blue Cross Blue Shield';
      case 'prescription':
        return 'RX: Ibuprofen 600mg\nQUANTITY: 30 tablets\nSIG: Take 1 tablet every 6 hours as needed\nPATIENT: John Doe\nPRESCRIBER: Dr. Smith';
      default:
        return 'Document content extracted successfully. All text has been processed and structured data identified.';
    }
  };

  const generateMockStructuredData = (docType: DocumentUpload['documentType']) => {
    const baseData = {
      patient_name: 'John Doe',
      date_of_service: '2024-01-15'
    };

    switch (docType) {
      case 'medical_record':
        return {
          ...baseData,
          diagnosis_codes: ['M54.2'],
          procedure_codes: ['97110'],
          provider_name: 'Dr. Smith',
          claim_amount: 250.00
        };
      case 'invoice':
        return {
          ...baseData,
          invoice_number: '12345',
          service_description: 'Physical Therapy',
          claim_amount: 250.00,
          insurance_provider: 'Blue Cross Blue Shield'
        };
      default:
        return baseData;
    }
  };

  // Drag and drop handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  const reprocessDocument = async (documentId: string) => {
    const upload = uploads.find(u => u.id === documentId);
    if (upload) {
      setUploads(prev => prev.map(u => 
        u.id === documentId ? { ...u, status: 'processing' } : u
      ));
      await processDocumentOCR(upload);
    }
  };

  const deleteDocument = (documentId: string) => {
    setUploads(prev => prev.filter(u => u.id !== documentId));
    setOcrResults(prev => {
      const newResults = { ...prev };
      delete newResults[documentId];
      return newResults;
    });
    setValidationResults(prev => {
      const newResults = { ...prev };
      delete newResults[documentId];
      return newResults;
    });
    setDocumentPreviews(prev => {
      const newResults = { ...prev };
      delete newResults[documentId];
      return newResults;
    });
    if (selectedDocument === documentId) {
      setSelectedDocument(null);
    }
  };

  const downloadExtractedData = (documentId: string) => {
    const ocrResult = ocrResults[documentId];
    if (ocrResult) {
      const data = {
        document_id: documentId,
        extracted_text: ocrResult.extractedText,
        structured_data: ocrResult.structuredData,
        confidence_scores: ocrResult.confidence_scores,
        quality_metrics: ocrResult.quality_metrics
      };
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `extracted_data_${documentId}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  const processBatch = async () => {
    setBatchProcessing(true);
    
    const pendingUploads = uploads.filter(u => u.status === 'completed');
    
    for (const upload of pendingUploads) {
      // Simulate batch processing
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    setBatchProcessing(false);
    alert(`Processed ${pendingUploads.length} documents in batch`);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Enhanced Document Processing</h1>
            <p className="text-gray-600">AI-powered document upload, OCR, and data extraction</p>
          </div>
          <div className="flex items-center space-x-2">
            <Select value={selectedClaimId} onValueChange={setSelectedClaimId}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Associate with claim" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">No claim association</SelectItem>
                <SelectItem value="CLM-2024-001">CLM-2024-001</SelectItem>
                <SelectItem value="CLM-2024-002">CLM-2024-002</SelectItem>
                <SelectItem value="CLM-2024-003">CLM-2024-003</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              onClick={processBatch}
              disabled={batchProcessing || uploads.filter(u => u.status === 'completed').length === 0}
              variant="outline"
            >
              {batchProcessing ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Batch Process
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-12rem)]">
          {/* Upload and Document List */}
          <div className="lg:col-span-1 space-y-6">
            {/* Upload Area */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Upload className="h-5 w-5" />
                  <span>Document Upload</span>
                </CardTitle>
                <CardDescription>
                  Drag and drop files or click to browse
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
                    ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg font-medium mb-2">Drop files here</p>
                  <p className="text-sm text-gray-600 mb-4">
                    Supports PDF, Images, Word docs up to 10MB
                  </p>
                  <Button variant="outline">
                    <Plus className="h-4 w-4 mr-2" />
                    Browse Files
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.jpg,.jpeg,.png,.tiff,.bmp,.doc,.docx,.txt"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Processing Queue */}
            {processingQueue.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    <span>Processing Queue</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {processingQueue.map(docId => {
                      const upload = uploads.find(u => u.id === docId);
                      return upload ? (
                        <div key={docId} className="flex items-center justify-between p-2 bg-blue-50 rounded">
                          <span className="text-sm">{upload.fileName}</span>
                          <Badge className="bg-blue-500">Processing OCR</Badge>
                        </div>
                      ) : null;
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Document List */}
            <Card className="flex-1">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-5 w-5" />
                    <span>Documents ({uploads.length})</span>
                  </div>
                  <Badge variant="outline">
                    {uploads.filter(u => u.status === 'completed').length} processed
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-96">
                  <div className="space-y-2 p-4">
                    {uploads.map((upload) => (
                      <div
                        key={upload.id}
                        className={`p-3 border rounded cursor-pointer transition-colors hover:bg-gray-50 
                          ${selectedDocument === upload.id ? 'border-blue-500 bg-blue-50' : ''}`}
                        onClick={() => setSelectedDocument(upload.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3 flex-1">
                            {getDocumentIcon(upload.fileType)}
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-sm truncate">{upload.fileName}</div>
                              <div className="text-xs text-gray-500">
                                {formatFileSize(upload.fileSize)} • {upload.documentType.replace('_', ' ')}
                              </div>
                              {upload.claimId && (
                                <div className="text-xs text-blue-600">
                                  Associated with {upload.claimId}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Badge className={getStatusColor(upload.status)}>
                              {upload.status}
                            </Badge>
                            <Button
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteDocument(upload.id);
                              }}
                              size="sm"
                              variant="ghost"
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                        
                        {upload.status === 'uploading' && (
                          <div className="mt-2">
                            <Progress value={upload.uploadProgress} className="h-1" />
                          </div>
                        )}

                        {upload.status === 'completed' && ocrResults[upload.id] && (
                          <div className="mt-2 flex items-center space-x-4 text-xs text-gray-600">
                            <span>Confidence: {(ocrResults[upload.id].confidence * 100).toFixed(1)}%</span>
                            <span>Quality: {(Object.values(ocrResults[upload.id].quality_metrics).reduce((a, b) => a + b, 0) / Object.values(ocrResults[upload.id].quality_metrics).length * 100).toFixed(0)}%</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* Document Details */}
          <div className="lg:col-span-2">
            {selectedDocument ? (
              <Card className="h-full">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2">
                      <Eye className="h-5 w-5" />
                      <span>Document Details</span>
                    </CardTitle>
                    <div className="flex items-center space-x-2">
                      {ocrResults[selectedDocument] && (
                        <Button
                          onClick={() => downloadExtractedData(selectedDocument)}
                          size="sm"
                          variant="outline"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Export Data
                        </Button>
                      )}
                      <Button
                        onClick={() => reprocessDocument(selectedDocument)}
                        size="sm"
                        variant="outline"
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Reprocess
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <Tabs defaultValue="preview" className="h-full">
                    <TabsList className="grid w-full grid-cols-5 px-4">
                      <TabsTrigger value="preview">Preview</TabsTrigger>
                      <TabsTrigger value="extracted">Extracted Data</TabsTrigger>
                      <TabsTrigger value="validation">Validation</TabsTrigger>
                      <TabsTrigger value="quality">Quality</TabsTrigger>
                      <TabsTrigger value="raw">Raw Text</TabsTrigger>
                    </TabsList>

                    <ScrollArea className="h-[calc(100vh-20rem)] px-4">
                      {/* Preview Tab */}
                      <TabsContent value="preview" className="space-y-4 mt-4">
                        {documentPreviews[selectedDocument] && (
                          <div className="space-y-4">
                            <div className="flex items-center justify-center p-8 border rounded-lg bg-gray-50">
                              <img
                                src={documentPreviews[selectedDocument].previewUrl}
                                alt="Document preview"
                                className="max-w-full max-h-96 object-contain"
                              />
                            </div>
                            
                            {documentPreviews[selectedDocument].annotations.length > 0 && (
                              <Card>
                                <CardHeader>
                                  <CardTitle className="text-sm">Detected Fields</CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <div className="space-y-2">
                                    {documentPreviews[selectedDocument].annotations.map((annotation) => (
                                      <div key={annotation.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                                        <span className="text-sm font-medium">{annotation.content}</span>
                                        <div className="flex items-center space-x-2">
                                          <Badge variant="outline" className={annotation.type === 'highlight' ? 'bg-yellow-100' : 'bg-blue-100'}>
                                            {annotation.type}
                                          </Badge>
                                          {annotation.confidence && (
                                            <span className={`text-xs ${getConfidenceColor(annotation.confidence)}`}>
                                              {(annotation.confidence * 100).toFixed(0)}%
                                            </span>
                                          )}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </CardContent>
                              </Card>
                            )}
                          </div>
                        )}
                      </TabsContent>

                      {/* Extracted Data Tab */}
                      <TabsContent value="extracted" className="space-y-4 mt-4">
                        {ocrResults[selectedDocument] && (
                          <div className="space-y-4">
                            <Card>
                              <CardHeader>
                                <CardTitle className="text-sm">Structured Data</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  {Object.entries(ocrResults[selectedDocument].structuredData).map(([key, value]) => (
                                    <div key={key} className="space-y-1">
                                      <Label className="text-xs font-medium capitalize">
                                        {key.replace('_', ' ')}
                                      </Label>
                                      <div className="flex items-center space-x-2">
                                        <Input
                                          value={Array.isArray(value) ? value.join(', ') : String(value)}
                                          readOnly
                                          className="text-sm"
                                        />
                                        <Button size="sm" variant="ghost">
                                          <Copy className="h-3 w-3" />
                                        </Button>
                                        <Button size="sm" variant="ghost">
                                          <Edit className="h-3 w-3" />
                                        </Button>
                                      </div>
                                      {ocrResults[selectedDocument].confidence_scores.fields[key] && (
                                        <div className="text-xs text-gray-500">
                                          Confidence: {(ocrResults[selectedDocument].confidence_scores.fields[key] * 100).toFixed(1)}%
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>

                            <Card>
                              <CardHeader>
                                <CardTitle className="text-sm">Field Validation</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="space-y-2">
                                  {ocrResults[selectedDocument].validation_results.map((result, index) => (
                                    <div key={index} className="flex items-center justify-between p-2 border rounded">
                                      <div className="flex items-center space-x-2">
                                        {result.status === 'valid' ? (
                                          <CheckCircle className="h-4 w-4 text-green-500" />
                                        ) : result.status === 'invalid' ? (
                                          <X className="h-4 w-4 text-red-500" />
                                        ) : (
                                          <AlertTriangle className="h-4 w-4 text-yellow-500" />
                                        )}
                                        <span className="text-sm capitalize">{result.field.replace('_', ' ')}</span>
                                      </div>
                                      <div className="flex items-center space-x-2">
                                        <Badge className={getStatusColor(result.status)}>
                                          {result.status}
                                        </Badge>
                                        <span className={`text-xs ${getConfidenceColor(result.confidence)}`}>
                                          {(result.confidence * 100).toFixed(0)}%
                                        </span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>
                          </div>
                        )}
                      </TabsContent>

                      {/* Validation Tab */}
                      <TabsContent value="validation" className="space-y-4 mt-4">
                        {validationResults[selectedDocument] && (
                          <div className="space-y-4">
                            <Card>
                              <CardHeader>
                                <CardTitle className="text-sm">Compliance Checks</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="space-y-3">
                                  {validationResults[selectedDocument].compliance_checks.map((check, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 border rounded">
                                      <div className="flex items-center space-x-3">
                                        {check.status === 'passed' ? (
                                          <CheckCircle className="h-4 w-4 text-green-500" />
                                        ) : check.status === 'failed' ? (
                                          <X className="h-4 w-4 text-red-500" />
                                        ) : (
                                          <AlertTriangle className="h-4 w-4 text-yellow-500" />
                                        )}
                                        <div>
                                          <div className="font-medium text-sm">{check.check_name}</div>
                                          <div className="text-xs text-gray-600">{check.details}</div>
                                        </div>
                                      </div>
                                      <Badge className={getStatusColor(check.status)}>
                                        {check.status}
                                      </Badge>
                                    </div>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>

                            <Card>
                              <CardHeader>
                                <CardTitle className="text-sm">Security Scan</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="space-y-3">
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm">Safety Score</span>
                                    <div className="flex items-center space-x-2">
                                      <Progress 
                                        value={validationResults[selectedDocument].security_scan.safety_score * 100} 
                                        className="w-20 h-2" 
                                      />
                                      <span className="text-sm font-medium">
                                        {(validationResults[selectedDocument].security_scan.safety_score * 100).toFixed(1)}%
                                      </span>
                                    </div>
                                  </div>
                                  
                                  {validationResults[selectedDocument].security_scan.threats_detected.length === 0 ? (
                                    <div className="flex items-center space-x-2 text-green-600">
                                      <CheckCircle className="h-4 w-4" />
                                      <span className="text-sm">No threats detected</span>
                                    </div>
                                  ) : (
                                    <div className="space-y-1">
                                      {validationResults[selectedDocument].security_scan.threats_detected.map((threat, index) => (
                                        <div key={index} className="flex items-center space-x-2 text-red-600">
                                          <AlertTriangle className="h-4 w-4" />
                                          <span className="text-sm">{threat}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </CardContent>
                            </Card>

                            <Card>
                              <CardHeader>
                                <CardTitle className="text-sm">Data Quality Metrics</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="space-y-3">
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm">Completeness</span>
                                    <div className="flex items-center space-x-2">
                                      <Progress 
                                        value={validationResults[selectedDocument].data_quality.completeness * 100} 
                                        className="w-20 h-2" 
                                      />
                                      <span className="text-sm">{(validationResults[selectedDocument].data_quality.completeness * 100).toFixed(0)}%</span>
                                    </div>
                                  </div>
                                  
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm">Accuracy</span>
                                    <div className="flex items-center space-x-2">
                                      <Progress 
                                        value={validationResults[selectedDocument].data_quality.accuracy * 100} 
                                        className="w-20 h-2" 
                                      />
                                      <span className="text-sm">{(validationResults[selectedDocument].data_quality.accuracy * 100).toFixed(0)}%</span>
                                    </div>
                                  </div>
                                  
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm">Consistency</span>
                                    <div className="flex items-center space-x-2">
                                      <Progress 
                                        value={validationResults[selectedDocument].data_quality.consistency * 100} 
                                        className="w-20 h-2" 
                                      />
                                      <span className="text-sm">{(validationResults[selectedDocument].data_quality.consistency * 100).toFixed(0)}%</span>
                                    </div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>

                            {validationResults[selectedDocument].recommendations.length > 0 && (
                              <Card>
                                <CardHeader>
                                  <CardTitle className="text-sm">Recommendations</CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <div className="space-y-2">
                                    {validationResults[selectedDocument].recommendations.map((rec, index) => (
                                      <div key={index} className="flex items-start space-x-2">
                                        <CheckCircle className="h-4 w-4 text-blue-500 mt-0.5" />
                                        <span className="text-sm">{rec}</span>
                                      </div>
                                    ))}
                                  </div>
                                </CardContent>
                              </Card>
                            )}
                          </div>
                        )}
                      </TabsContent>

                      {/* Quality Tab */}
                      <TabsContent value="quality" className="space-y-4 mt-4">
                        {ocrResults[selectedDocument] && (
                          <div className="space-y-4">
                            <Card>
                              <CardHeader>
                                <CardTitle className="text-sm">Processing Metrics</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  <div>
                                    <Label className="text-xs">Overall Confidence</Label>
                                    <div className="flex items-center space-x-2 mt-1">
                                      <Progress value={ocrResults[selectedDocument].confidence * 100} className="flex-1 h-2" />
                                      <span className="text-sm font-medium">
                                        {(ocrResults[selectedDocument].confidence * 100).toFixed(1)}%
                                      </span>
                                    </div>
                                  </div>
                                  
                                  <div>
                                    <Label className="text-xs">Processing Time</Label>
                                    <div className="text-lg font-medium mt-1">
                                      {ocrResults[selectedDocument].processingTime.toFixed(1)}s
                                    </div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>

                            <Card>
                              <CardHeader>
                                <CardTitle className="text-sm">Quality Metrics</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="space-y-3">
                                  {Object.entries(ocrResults[selectedDocument].quality_metrics).map(([metric, value]) => (
                                    <div key={metric} className="flex items-center justify-between">
                                      <span className="text-sm capitalize">{metric.replace('_', ' ')}</span>
                                      <div className="flex items-center space-x-2">
                                        <Progress value={value * 100} className="w-20 h-2" />
                                        <span className="text-sm w-12">{(value * 100).toFixed(0)}%</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>

                            {ocrResults[selectedDocument].detected_anomalies.length > 0 && (
                              <Card>
                                <CardHeader>
                                  <CardTitle className="text-sm">Detected Anomalies</CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <div className="space-y-2">
                                    {ocrResults[selectedDocument].detected_anomalies.map((anomaly, index) => (
                                      <div key={index} className="flex items-center space-x-2">
                                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                                        <span className="text-sm">{anomaly}</span>
                                      </div>
                                    ))}
                                  </div>
                                </CardContent>
                              </Card>
                            )}
                          </div>
                        )}
                      </TabsContent>

                      {/* Raw Text Tab */}
                      <TabsContent value="raw" className="space-y-4 mt-4">
                        {ocrResults[selectedDocument] && (
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-sm">Extracted Text</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="relative">
                                <textarea
                                  value={ocrResults[selectedDocument].extractedText}
                                  readOnly
                                  className="w-full h-64 p-3 border rounded text-sm font-mono resize-none"
                                />
                                <Button
                                  onClick={() => navigator.clipboard.writeText(ocrResults[selectedDocument].extractedText)}
                                  size="sm"
                                  variant="outline"
                                  className="absolute top-2 right-2"
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </TabsContent>
                    </ScrollArea>
                  </Tabs>
                </CardContent>
              </Card>
            ) : (
              <Card className="h-full flex items-center justify-center">
                <CardContent>
                  <div className="text-center text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <div>Select a document from the list to view details</div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}