import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, CheckCircle, Clock, FileText, User, Building, Calendar, DollarSign, Upload, X, Eye } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, ClaimSubmission } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface FormData extends ClaimSubmission {
  service_date: string;
}

interface UploadedDocument {
  file: File;
  id?: string;
  upload_status?: string;
  ocr_processed?: boolean;
  extracted_text?: string;
  extracted_fields?: Record<string, any>;
  processing?: boolean;
  error?: string;
}

export default function SubmitClaim() {
  const { user, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [currentStep, setCurrentStep] = useState(1);
  
  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span>Loading...</span>
        </div>
      </div>
    );
  }
  
  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Authentication Required</h2>
          <p className="text-gray-600 mb-6">Please log in to submit a claim.</p>
          <Button onClick={() => navigate('/login')}>
            Go to Login
          </Button>
        </div>
      </div>
    );
  }
  const [submitting, setSubmitting] = useState(false);
  
  // Document upload state
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [ocrProcessing, setOcrProcessing] = useState(false);
  const [autoFillEnabled, setAutoFillEnabled] = useState(true);

  // Dynamic code lists loaded from API
  const [diagnosisCodes, setDiagnosisCodes] = useState<{code: string, description: string}[]>([]);
  const [procedureCodes, setProcedureCodes] = useState<{code: string, description: string}[]>([]);
  const [insuranceProviders, setInsuranceProviders] = useState<string[]>([]);
  const [loadingCodes, setLoadingCodes] = useState(true);

  const documentTypes = [
    { value: 'MEDICAL_BILL', label: 'Medical Bill' },
    { value: 'INSURANCE_CARD', label: 'Insurance Card' },
    { value: 'PRESCRIPTION', label: 'Prescription' },
    { value: 'MEDICAL_REPORT', label: 'Medical Report' },
    { value: 'REFERRAL', label: 'Referral' },
    { value: 'LAB_RESULT', label: 'Lab Result' },
    { value: 'IMAGING', label: 'Imaging' },
    { value: 'AUTHORIZATION', label: 'Authorization' },
    { value: 'OTHER', label: 'Other' },
  ];

  const [formData, setFormData] = useState<FormData>({
    patient_name: '',
    patient_id: '',
    insurance_provider: '',
    policy_number: '',
    diagnosis_code: '',
    procedure_code: '',
    service_date: '',
    claim_amount: 0,
    provider_name: '',
    provider_npi: '',
    notes: '',
    priority: 1,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load dropdown data on component mount
  useEffect(() => {
    loadFormData();
  }, []);

  const loadFormData = async () => {
    try {
      setLoadingCodes(true);
      
      // Load data from backend APIs
      try {
        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        
        // Load diagnosis codes
        const diagnosisResponse = await fetch(`${API_BASE_URL}/api/reference/diagnosis-codes`, {
          headers: { 'Content-Type': 'application/json' }
        });
        if (diagnosisResponse.ok) {
          const diagnosisData = await diagnosisResponse.json();
          setDiagnosisCodes(diagnosisData);
        } else {
          throw new Error('Failed to load diagnosis codes');
        }

        // Load procedure codes
        const procedureResponse = await fetch(`${API_BASE_URL}/api/reference/procedure-codes`, {
          headers: { 'Content-Type': 'application/json' }
        });
        if (procedureResponse.ok) {
          const procedureData = await procedureResponse.json();
          setProcedureCodes(procedureData);
        } else {
          throw new Error('Failed to load procedure codes');
        }

        // Load insurance providers
        const insuranceResponse = await fetch(`${API_BASE_URL}/api/reference/insurance-providers`, {
          headers: { 'Content-Type': 'application/json' }
        });
        if (insuranceResponse.ok) {
          const insuranceData = await insuranceResponse.json();
          // Convert objects to simple strings for the dropdown
          const providerNames = insuranceData.map((provider: any) => provider.name);
          setInsuranceProviders(providerNames);
        } else {
          throw new Error('Failed to load insurance providers');
        }

      } catch (apiError) {
        console.error('API loading failed, using fallback data:', apiError);
        
        // Fallback to hardcoded data if API fails
        setDiagnosisCodes([
          { code: "Z00.00", description: "General adult medical examination" },
          { code: "M25.511", description: "Pain in right shoulder" },
          { code: "E11.9", description: "Type 2 diabetes mellitus" },
          { code: "J06.9", description: "Acute upper respiratory infection" },
          { code: "K21.9", description: "Gastro-esophageal reflux disease" },
          { code: "M79.3", description: "Panniculitis, unspecified" },
          { code: "I10", description: "Essential hypertension" },
          { code: "C50.1", description: "Breast cancer (central portion)" },
          { code: "C50.2", description: "Breast cancer (upper-inner quadrant)" },
          { code: "I21.0", description: "ST elevation myocardial infarction" },
          { code: "I63.1", description: "Cerebral infarction due to embolism" },
          { code: "I63.2", description: "Cerebral infarction, unspecified" }
        ]);

        setProcedureCodes([
          { code: "99213", description: "Office visit, established patient, low complexity" },
          { code: "99214", description: "Office visit, established patient, moderate complexity" },
          { code: "99215", description: "Office visit, established patient, high complexity" },
          { code: "92004", description: "Ophthalmological examination and evaluation" },
          { code: "27447", description: "Arthroplasty, knee, condyle and plateau" },
          { code: "73721", description: "MRI lower extremity other than joint" },
          { code: "36415", description: "Collection of venous blood by venipuncture" },
          { code: "85025", description: "Blood count; complete (CBC), automated" }
        ]);

        setInsuranceProviders([
          'Blue Cross Blue Shield',
          'Aetna',
          'Cigna',
          'UnitedHealthcare',
          'Humana',
          'Kaiser Permanente',
          'Anthem',
          'Molina Healthcare',
        ]);
      }

    } catch (error) {
      console.error('Failed to load form data:', error);
      toast({
        title: 'Error Loading Data',
        description: 'Failed to load form options. Using fallback data.',
        variant: 'destructive',
      });
    } finally {
      setLoadingCodes(false);
    }
  };

  // File upload handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = async (files: File[]) => {
    const validFiles = files.filter(file => {
      const validTypes = ['image/jpeg', 'image/png', 'image/tiff', 'application/pdf'];
      const maxSize = 10 * 1024 * 1024; // 10MB
      
      if (!validTypes.includes(file.type)) {
        toast({
          title: 'Invalid File Type',
          description: `${file.name} is not a supported file type. Please upload images or PDFs.`,
          variant: 'destructive',
        });
        return false;
      }
      
      if (file.size > maxSize) {
        toast({
          title: 'File Too Large',
          description: `${file.name} is larger than 10MB. Please choose a smaller file.`,
          variant: 'destructive',
        });
        return false;
      }
      
      return true;
    });

    if (validFiles.length === 0) return;

    // Add files to upload state
    const newDocuments: UploadedDocument[] = validFiles.map(file => ({
      file,
      processing: false,
      ocr_processed: false
    }));

    setUploadedDocuments(prev => [...prev, ...newDocuments]);

    // Upload each file
    for (let i = 0; i < newDocuments.length; i++) {
      await uploadDocument(uploadedDocuments.length + i, newDocuments[i]);
    }
  };

  const uploadDocument = async (index: number, document: UploadedDocument) => {
    try {
      // Mark as processing
      setUploadedDocuments(prev => prev.map((doc, i) => 
        i === index ? { ...doc, processing: true } : doc
      ));

      // Simulate upload process - in real implementation this would call the backend
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update with simulated upload response
      setUploadedDocuments(prev => prev.map((doc, i) => 
        i === index ? { 
          ...doc, 
          id: `doc_${Date.now()}_${index}`,
          upload_status: 'completed',
          processing: false 
        } : doc
      ));

      toast({
        title: 'Document Uploaded',
        description: `${document.file.name} has been uploaded successfully.`,
      });

    } catch (error) {
      console.error('Upload failed:', error);
      setUploadedDocuments(prev => prev.map((doc, i) => 
        i === index ? { 
          ...doc, 
          processing: false,
          error: error instanceof Error ? error.message : 'Upload failed'
        } : doc
      ));
    }
  };

  const startOCRProcessing = async (docIndex: number, documentId: string) => {
    try {
      setOcrProcessing(true);
      
      // Simulate OCR processing - in real implementation this would poll the backend
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate extracted data
      const mockExtractedData = {
        patient_name: 'John Doe',
        policy_number: 'POL123456',
        claim_amount: '250.00',
        service_date: '2025-10-15'
      };
      
      // Update document with simulated OCR results
      setUploadedDocuments(prev => prev.map((doc, index) => 
        index === docIndex ? {
          ...doc,
          ocr_processed: true,
          extracted_text: 'Simulated extracted text from document...',
          extracted_fields: mockExtractedData,
          processing: false
        } : doc
      ));
      
      // Auto-fill form if enabled and fields extracted
      if (autoFillEnabled && mockExtractedData) {
        autoFillFromOCR(mockExtractedData);
      }
      
    } catch (error) {
      console.error('OCR processing failed:', error);
      setUploadedDocuments(prev => prev.map((doc, index) => 
        index === docIndex ? {
          ...doc,
          processing: false,
          error: 'OCR processing failed'
        } : doc
      ));
    } finally {
      setOcrProcessing(false);
    }
  };

  const autoFillFromOCR = (extractedFields: Record<string, any>) => {
    const fieldMapping: Record<string, string> = {
      'patient_name': 'patient_name',
      'patient_id': 'patient_id',
      'policy_number': 'policy_number',
      'diagnosis_code': 'diagnosis_code',
      'procedure_code': 'procedure_code',
      'amount': 'claim_amount',
      'service_date': 'service_date',
      'provider_name': 'provider_name',
      'insurance_provider': 'insurance_provider'
    };

    let updatedFields: Record<string, any> = {};
    let fieldsUpdated: string[] = [];

    Object.entries(extractedFields).forEach(([key, value]) => {
      const formField = fieldMapping[key];
      if (formField && value && !formData[formField as keyof FormData]) {
        updatedFields[formField] = value;
        fieldsUpdated.push(formField);
      }
    });

    if (fieldsUpdated.length > 0) {
      setFormData(prev => ({ ...prev, ...updatedFields }));
      toast({
        title: 'Form Auto-filled',
        description: `Updated ${fieldsUpdated.length} fields from document analysis.`,
      });
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'claim_amount' ? parseFloat(value) || 0 : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user makes selection
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.patient_name.trim()) newErrors.patient_name = 'Patient name is required';
    if (!formData.patient_id.trim()) newErrors.patient_id = 'Patient ID is required';
    if (!formData.insurance_provider) newErrors.insurance_provider = 'Insurance provider is required';
    if (!formData.policy_number.trim()) newErrors.policy_number = 'Policy number is required';
    if (!formData.diagnosis_code) newErrors.diagnosis_code = 'Diagnosis code is required';
    if (!formData.procedure_code) newErrors.procedure_code = 'Procedure code is required';
    if (!formData.service_date) newErrors.service_date = 'Service date is required';
    if (!formData.claim_amount || formData.claim_amount <= 0) newErrors.claim_amount = 'Valid claim amount is required';
    if (!formData.provider_name.trim()) newErrors.provider_name = 'Provider name is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors in the form before submitting.',
        variant: 'destructive',
      });
      return;
    }

    setSubmitting(true);

    try {
      const claim = await apiClient.submitClaim(formData);
      
      toast({
        title: 'Claim Submitted Successfully',
        description: `Your claim ${claim.claim_id} has been submitted and is being processed.`,
      });

      navigate(`/user/claim/${claim.claim_id}`);
    } catch (error) {
      toast({
        title: 'Submission Failed',
        description: error instanceof Error ? error.message : 'An error occurred while submitting your claim.',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const removeDocument = (index: number) => {
    setUploadedDocuments(prev => prev.filter((_, i) => i !== index));
  };

  const nextStep = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Submit New Claim</h1>
          <p className="text-gray-600 mt-2">Complete the form below to submit your insurance claim</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}>
                  {step}
                </div>
                <div className="ml-2">
                  <div className={`text-sm font-medium ${step <= currentStep ? 'text-blue-600' : 'text-gray-600'}`}>
                    {step === 1 && 'Patient Info'}
                    {step === 2 && 'Medical Details'}
                    {step === 3 && 'Documents & Review'}
                  </div>
                </div>
                {step < 3 && (
                  <div className={`w-16 h-1 mx-4 ${
                    step < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Step 1: Patient Information */}
          {currentStep === 1 && (
            <Card>
              <CardHeader>
                <CardTitle>Patient Information</CardTitle>
                <CardDescription>Enter the patient's basic information and insurance details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="patient_name">Patient Name *</Label>
                    <Input
                      id="patient_name"
                      name="patient_name"
                      value={formData.patient_name}
                      onChange={handleChange}
                      placeholder="Enter patient's full name"
                      className={errors.patient_name ? 'border-red-500' : ''}
                    />
                    {errors.patient_name && <p className="text-red-500 text-sm mt-1">{errors.patient_name}</p>}
                  </div>

                  <div>
                    <Label htmlFor="patient_id">Patient ID *</Label>
                    <Input
                      id="patient_id"
                      name="patient_id"
                      value={formData.patient_id}
                      onChange={handleChange}
                      placeholder="Enter patient ID"
                      className={errors.patient_id ? 'border-red-500' : ''}
                    />
                    {errors.patient_id && <p className="text-red-500 text-sm mt-1">{errors.patient_id}</p>}
                  </div>

                  <div>
                    <Label htmlFor="insurance_provider">Insurance Provider *</Label>
                    <Select
                      value={formData.insurance_provider}
                      onValueChange={(value) => handleSelectChange('insurance_provider', value)}
                    >
                      <SelectTrigger className={errors.insurance_provider ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select insurance provider" />
                      </SelectTrigger>
                      <SelectContent>
                        {(insuranceProviders || []).map((provider) => (
                          <SelectItem key={provider} value={provider}>
                            {provider}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.insurance_provider && <p className="text-red-500 text-sm mt-1">{errors.insurance_provider}</p>}
                  </div>

                  <div>
                    <Label htmlFor="policy_number">Policy Number *</Label>
                    <Input
                      id="policy_number"
                      name="policy_number"
                      value={formData.policy_number}
                      onChange={handleChange}
                      placeholder="Enter policy number"
                      className={errors.policy_number ? 'border-red-500' : ''}
                    />
                    {errors.policy_number && <p className="text-red-500 text-sm mt-1">{errors.policy_number}</p>}
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button type="button" onClick={nextStep}>
                    Next Step
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 2: Medical Details */}
          {currentStep === 2 && (
            <Card>
              <CardHeader>
                <CardTitle>Medical Details</CardTitle>
                <CardDescription>Enter the medical information for this claim</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {loadingCodes ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                      <span>Loading medical codes...</span>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <Label htmlFor="diagnosis_code">Diagnosis Code *</Label>
                      <Select
                        value={formData.diagnosis_code}
                        onValueChange={(value) => handleSelectChange('diagnosis_code', value)}
                      >
                        <SelectTrigger className={errors.diagnosis_code ? 'border-red-500' : ''}>
                          <SelectValue placeholder="Select diagnosis code" />
                        </SelectTrigger>
                        <SelectContent>
                          {(diagnosisCodes || []).map((diagnosis) => (
                            <SelectItem key={diagnosis.code} value={diagnosis.code}>
                              {diagnosis.code} - {diagnosis.description}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {errors.diagnosis_code && <p className="text-red-500 text-sm mt-1">{errors.diagnosis_code}</p>}
                    </div>

                    <div>
                      <Label htmlFor="procedure_code">Procedure Code *</Label>
                      <Select
                        value={formData.procedure_code}
                        onValueChange={(value) => handleSelectChange('procedure_code', value)}
                      >
                        <SelectTrigger className={errors.procedure_code ? 'border-red-500' : ''}>
                          <SelectValue placeholder="Select procedure code" />
                        </SelectTrigger>
                        <SelectContent>
                          {(procedureCodes || []).map((procedure) => (
                            <SelectItem key={procedure.code} value={procedure.code}>
                              {procedure.code} - {procedure.description}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {errors.procedure_code && <p className="text-red-500 text-sm mt-1">{errors.procedure_code}</p>}
                    </div>

                    <div>
                      <Label htmlFor="service_date">Service Date *</Label>
                      <Input
                        id="service_date"
                        name="service_date"
                        type="date"
                        value={formData.service_date}
                        onChange={handleChange}
                        className={errors.service_date ? 'border-red-500' : ''}
                      />
                      {errors.service_date && <p className="text-red-500 text-sm mt-1">{errors.service_date}</p>}
                    </div>

                    <div>
                      <Label htmlFor="claim_amount">Claim Amount *</Label>
                      <Input
                        id="claim_amount"
                        name="claim_amount"
                        type="number"
                        step="0.01"
                        value={formData.claim_amount || ''}
                        onChange={handleChange}
                        placeholder="0.00"
                        className={errors.claim_amount ? 'border-red-500' : ''}
                      />
                      {errors.claim_amount && <p className="text-red-500 text-sm mt-1">{errors.claim_amount}</p>}
                    </div>

                    <div>
                      <Label htmlFor="provider_name">Provider Name *</Label>
                      <Input
                        id="provider_name"
                        name="provider_name"
                        value={formData.provider_name}
                        onChange={handleChange}
                        placeholder="Enter provider name"
                        className={errors.provider_name ? 'border-red-500' : ''}
                      />
                      {errors.provider_name && <p className="text-red-500 text-sm mt-1">{errors.provider_name}</p>}
                    </div>

                    <div>
                      <Label htmlFor="provider_npi">Provider NPI</Label>
                      <Input
                        id="provider_npi"
                        name="provider_npi"
                        value={formData.provider_npi}
                        onChange={handleChange}
                        placeholder="Enter NPI number"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <Label htmlFor="notes">Additional Notes</Label>
                  <Textarea
                    id="notes"
                    name="notes"
                    value={formData.notes}
                    onChange={handleChange}
                    placeholder="Any additional information about this claim..."
                    rows={3}
                  />
                </div>

                <div className="flex justify-between">
                  <Button type="button" variant="outline" onClick={prevStep}>
                    Previous
                  </Button>
                  <Button type="button" onClick={nextStep}>
                    Next Step
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Step 3: Documents & Review */}
          {currentStep === 3 && (
            <div className="space-y-6">
              {/* Document Upload */}
              <Card>
                <CardHeader>
                  <CardTitle>Upload Documents</CardTitle>
                  <CardDescription>Upload supporting documents for your claim</CardDescription>
                </CardHeader>
                <CardContent>
                  <div
                    className={`border-2 border-dashed rounded-lg p-8 text-center ${
                      dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                    }`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                  >
                    <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <p className="text-lg font-medium text-gray-900 mb-2">
                      Drag and drop files here, or click to browse
                    </p>
                    <p className="text-sm text-gray-500 mb-4">
                      Supports: JPG, PNG, TIFF, PDF (max 10MB each)
                    </p>
                    <input
                      type="file"
                      multiple
                      accept="image/*,.pdf"
                      onChange={handleFileInput}
                      className="hidden"
                      id="file-upload"
                    />
                    <Button type="button" variant="outline" onClick={() => document.getElementById('file-upload')?.click()}>
                      Browse Files
                    </Button>
                  </div>

                  {/* Uploaded Documents */}
                  {uploadedDocuments.length > 0 && (
                    <div className="mt-6 space-y-3">
                      <h4 className="font-medium">Uploaded Documents</h4>
                      {uploadedDocuments.map((doc, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <FileText className="h-5 w-5 text-gray-500" />
                            <div>
                              <p className="font-medium">{doc.file.name}</p>
                              <p className="text-sm text-gray-500">
                                {(doc.file.size / 1024 / 1024).toFixed(2)} MB
                              </p>
                            </div>
                            {doc.processing && (
                              <div className="flex items-center space-x-2">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                <span className="text-sm text-blue-600">Processing...</span>
                              </div>
                            )}
                            {doc.ocr_processed && (
                              <Badge variant="secondary">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                OCR Complete
                              </Badge>
                            )}
                            {doc.error && (
                              <Badge variant="destructive">
                                <AlertCircle className="h-3 w-3 mr-1" />
                                Error
                              </Badge>
                            )}
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeDocument(index)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Review & Submit */}
              <Card>
                <CardHeader>
                  <CardTitle>Review & Submit</CardTitle>
                  <CardDescription>Review your claim details before submitting</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Patient:</span> {formData.patient_name || 'Not specified'}
                    </div>
                    <div>
                      <span className="font-medium">Patient ID:</span> {formData.patient_id || 'Not specified'}
                    </div>
                    <div>
                      <span className="font-medium">Insurance:</span> {formData.insurance_provider || 'Not specified'}
                    </div>
                    <div>
                      <span className="font-medium">Policy:</span> {formData.policy_number || 'Not specified'}
                    </div>
                    <div>
                      <span className="font-medium">Diagnosis:</span> {formData.diagnosis_code || 'Not specified'}
                    </div>
                    <div>
                      <span className="font-medium">Procedure:</span> {formData.procedure_code || 'Not specified'}
                    </div>
                    <div>
                      <span className="font-medium">Service Date:</span> {formData.service_date || 'Not specified'}
                    </div>
                    <div>
                      <span className="font-medium">Amount:</span> ${formData.claim_amount?.toFixed(2) || '0.00'}
                    </div>
                    <div>
                      <span className="font-medium">Provider:</span> {formData.provider_name || 'Not specified'}
                    </div>
                    <div>
                      <span className="font-medium">Documents:</span> {uploadedDocuments.length} uploaded
                    </div>
                  </div>

                  <div className="flex justify-between mt-8">
                    <Button type="button" variant="outline" onClick={prevStep}>
                      Previous
                    </Button>
                    <Button type="submit" disabled={submitting}>
                      {submitting ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Submitting...
                        </>
                      ) : (
                        'Submit Claim'
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}