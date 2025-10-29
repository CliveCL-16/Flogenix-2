import { useState } from 'react';
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
import { AlertCircle, CheckCircle, Clock, FileText, User, Building, Calendar, DollarSign } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, ClaimSubmission } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface FormData extends ClaimSubmission {
  service_date: string;
}

const DIAGNOSIS_CODES = [
  { code: 'Z00.00', description: 'General adult medical examination' },
  { code: 'S52.501A', description: 'Unspecified fracture of lower end of right radius' },
  { code: 'M25.511', description: 'Pain in right shoulder' },
  { code: 'E11.9', description: 'Type 2 diabetes mellitus without complications' },
  { code: 'J06.9', description: 'Acute upper respiratory infection' },
  { code: 'K21.9', description: 'Gastro-esophageal reflux disease' },
  { code: 'M79.3', description: 'Panniculitis, unspecified' },
  { code: 'I10', description: 'Essential hypertension' },
];

const PROCEDURE_CODES = [
  { code: '99213', description: 'Office visit, established patient, low complexity' },
  { code: '99214', description: 'Office visit, established patient, moderate complexity' },
  { code: '99215', description: 'Office visit, established patient, high complexity' },
  { code: '92004', description: 'Ophthalmological examination' },
  { code: '27447', description: 'Knee arthroplasty' },
  { code: '73721', description: 'MRI lower extremity' },
  { code: '36415', description: 'Blood collection' },
  { code: '85025', description: 'Complete blood count' },
];

const INSURANCE_PROVIDERS = [
  'Blue Cross Blue Shield',
  'Aetna',
  'Cigna',
  'UnitedHealthcare',
  'Humana',
  'Kaiser Permanente',
  'Anthem',
  'Molina Healthcare',
];

export default function EnterpriseSubmitClaim() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [eligibilityChecking, setEligibilityChecking] = useState(false);
  const [eligibilityStatus, setEligibilityStatus] = useState<'unknown' | 'checking' | 'eligible' | 'ineligible'>('unknown');

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

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    if (step === 1) {
      if (!formData.patient_name) newErrors.patient_name = 'Patient name is required';
      if (!formData.patient_id) newErrors.patient_id = 'Patient ID is required';
      if (!formData.insurance_provider) newErrors.insurance_provider = 'Insurance provider is required';
      if (!formData.policy_number) newErrors.policy_number = 'Policy number is required';
    } else if (step === 2) {
      if (!formData.diagnosis_code) newErrors.diagnosis_code = 'Diagnosis code is required';
      if (!formData.procedure_code) newErrors.procedure_code = 'Procedure code is required';
      if (!formData.service_date) newErrors.service_date = 'Service date is required';
      if (!formData.claim_amount || formData.claim_amount <= 0) newErrors.claim_amount = 'Valid claim amount is required';
    } else if (step === 3) {
      if (!formData.provider_name) newErrors.provider_name = 'Provider name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      if (currentStep === 1) {
        // Check eligibility when moving from step 1 to 2
        checkEligibility();
      }
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    setCurrentStep(currentStep - 1);
  };

  const checkEligibility = async () => {
    setEligibilityChecking(true);
    setEligibilityStatus('checking');

    try {
      // Simulate eligibility check
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock eligibility response (in production, this would call a real API)
      const isEligible = Math.random() > 0.2; // 80% success rate
      setEligibilityStatus(isEligible ? 'eligible' : 'ineligible');
      
      if (!isEligible) {
        toast({
          title: 'Eligibility Issue',
          description: 'Patient may not be eligible for this procedure. Please verify coverage details.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      setEligibilityStatus('unknown');
      toast({
        title: 'Eligibility Check Failed',
        description: 'Unable to verify eligibility. You can still submit the claim.',
        variant: 'destructive',
      });
    } finally {
      setEligibilityChecking(false);
    }
  };

  const handleSubmit = async () => {
    if (!validateStep(3)) return;

    setSubmitting(true);
    try {
      const claim = await apiClient.submitClaim(formData);
      
      toast({
        title: 'Claim Submitted Successfully!',
        description: `Claim ${claim.claim_id} has been submitted and queued for processing.`,
      });

      // Navigate to claim details
      navigate(`/user/claim/${claim.claim_id}`);
      
    } catch (error) {
      toast({
        title: 'Submission Failed',
        description: error instanceof Error ? error.message : 'Failed to submit claim. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const updateFormData = (field: keyof FormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const progressPercentage = (currentStep / 4) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Submit New Claim</h1>
              <p className="text-gray-600 mt-1">Complete the form below to submit your healthcare claim</p>
            </div>
            <Badge variant="secondary">Step {currentStep} of 4</Badge>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Progress</span>
            <span className="text-sm text-gray-500">{currentStep} of 4 steps</span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>

        {/* Step Indicators */}
        <div className="flex justify-between items-center mb-8">
          {[
            { step: 1, title: 'Patient Info', icon: User },
            { step: 2, title: 'Medical Details', icon: FileText },
            { step: 3, title: 'Provider Info', icon: Building },
            { step: 4, title: 'Review & Submit', icon: CheckCircle },
          ].map(({ step, title, icon: Icon }) => (
            <div key={step} className="flex items-center">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                step <= currentStep
                  ? 'bg-blue-600 border-blue-600 text-white'
                  : 'border-gray-300 text-gray-500'
              }`}>
                {step < currentStep ? (
                  <CheckCircle className="h-5 w-5" />
                ) : (
                  <Icon className="h-5 w-5" />
                )}
              </div>
              <span className={`ml-2 text-sm font-medium ${
                step <= currentStep ? 'text-blue-600' : 'text-gray-500'
              }`}>
                {title}
              </span>
              {step < 4 && <div className="hidden sm:block w-16 h-0.5 bg-gray-300 ml-4" />}
            </div>
          ))}
        </div>

        {/* Form Steps */}
        <Card>
          <CardHeader>
            <CardTitle>
              {currentStep === 1 && 'Patient & Insurance Information'}
              {currentStep === 2 && 'Medical Details'}
              {currentStep === 3 && 'Provider Information'}
              {currentStep === 4 && 'Review & Submit'}
            </CardTitle>
            <CardDescription>
              {currentStep === 1 && 'Enter patient demographics and insurance details'}
              {currentStep === 2 && 'Provide medical codes and claim amount'}
              {currentStep === 3 && 'Healthcare provider information'}
              {currentStep === 4 && 'Review all information before submitting'}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Step 1: Patient Information */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="patient_name">Patient Name *</Label>
                    <Input
                      id="patient_name"
                      value={formData.patient_name}
                      onChange={(e) => updateFormData('patient_name', e.target.value)}
                      placeholder="John Doe"
                      className={errors.patient_name ? 'border-red-500' : ''}
                    />
                    {errors.patient_name && (
                      <p className="text-sm text-red-500">{errors.patient_name}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="patient_id">Patient ID *</Label>
                    <Input
                      id="patient_id"
                      value={formData.patient_id}
                      onChange={(e) => updateFormData('patient_id', e.target.value)}
                      placeholder="PAT-12345"
                      className={errors.patient_id ? 'border-red-500' : ''}
                    />
                    {errors.patient_id && (
                      <p className="text-sm text-red-500">{errors.patient_id}</p>
                    )}
                  </div>
                </div>

                <Separator />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="insurance_provider">Insurance Provider *</Label>
                    <Select 
                      value={formData.insurance_provider} 
                      onValueChange={(value) => updateFormData('insurance_provider', value)}
                    >
                      <SelectTrigger className={errors.insurance_provider ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select insurance provider" />
                      </SelectTrigger>
                      <SelectContent>
                        {INSURANCE_PROVIDERS.map((provider) => (
                          <SelectItem key={provider} value={provider}>
                            {provider}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.insurance_provider && (
                      <p className="text-sm text-red-500">{errors.insurance_provider}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="policy_number">Policy Number *</Label>
                    <Input
                      id="policy_number"
                      value={formData.policy_number}
                      onChange={(e) => updateFormData('policy_number', e.target.value)}
                      placeholder="POL-67890"
                      className={errors.policy_number ? 'border-red-500' : ''}
                    />
                    {errors.policy_number && (
                      <p className="text-sm text-red-500">{errors.policy_number}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Medical Details */}
            {currentStep === 2 && (
              <div className="space-y-6">
                {/* Eligibility Status */}
                {eligibilityStatus !== 'unknown' && (
                  <div className={`p-4 rounded-lg border ${
                    eligibilityStatus === 'eligible' 
                      ? 'bg-green-50 border-green-200' 
                      : eligibilityStatus === 'ineligible'
                      ? 'bg-red-50 border-red-200'
                      : 'bg-blue-50 border-blue-200'
                  }`}>
                    <div className="flex items-center gap-2">
                      {eligibilityStatus === 'checking' && <Clock className="h-5 w-5 text-blue-600 animate-spin" />}
                      {eligibilityStatus === 'eligible' && <CheckCircle className="h-5 w-5 text-green-600" />}
                      {eligibilityStatus === 'ineligible' && <AlertCircle className="h-5 w-5 text-red-600" />}
                      <span className="font-medium">
                        {eligibilityStatus === 'checking' && 'Checking eligibility...'}
                        {eligibilityStatus === 'eligible' && 'Patient is eligible for coverage'}
                        {eligibilityStatus === 'ineligible' && 'Eligibility verification failed'}
                      </span>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="diagnosis_code">Diagnosis Code (ICD-10) *</Label>
                    <Select 
                      value={formData.diagnosis_code} 
                      onValueChange={(value) => updateFormData('diagnosis_code', value)}
                    >
                      <SelectTrigger className={errors.diagnosis_code ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select diagnosis code" />
                      </SelectTrigger>
                      <SelectContent>
                        {DIAGNOSIS_CODES.map((diagnosis) => (
                          <SelectItem key={diagnosis.code} value={diagnosis.code}>
                            {diagnosis.code} - {diagnosis.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.diagnosis_code && (
                      <p className="text-sm text-red-500">{errors.diagnosis_code}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="procedure_code">Procedure Code (CPT) *</Label>
                    <Select 
                      value={formData.procedure_code} 
                      onValueChange={(value) => updateFormData('procedure_code', value)}
                    >
                      <SelectTrigger className={errors.procedure_code ? 'border-red-500' : ''}>
                        <SelectValue placeholder="Select procedure code" />
                      </SelectTrigger>
                      <SelectContent>
                        {PROCEDURE_CODES.map((procedure) => (
                          <SelectItem key={procedure.code} value={procedure.code}>
                            {procedure.code} - {procedure.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.procedure_code && (
                      <p className="text-sm text-red-500">{errors.procedure_code}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="service_date">Service Date *</Label>
                    <Input
                      id="service_date"
                      type="date"
                      value={formData.service_date}
                      onChange={(e) => updateFormData('service_date', e.target.value)}
                      max={new Date().toISOString().split('T')[0]}
                      className={errors.service_date ? 'border-red-500' : ''}
                    />
                    {errors.service_date && (
                      <p className="text-sm text-red-500">{errors.service_date}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="claim_amount">Claim Amount (USD) *</Label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="claim_amount"
                        type="number"
                        min="0"
                        step="0.01"
                        value={formData.claim_amount || ''}
                        onChange={(e) => updateFormData('claim_amount', parseFloat(e.target.value) || 0)}
                        placeholder="150.00"
                        className={`pl-10 ${errors.claim_amount ? 'border-red-500' : ''}`}
                      />
                    </div>
                    {errors.claim_amount && (
                      <p className="text-sm text-red-500">{errors.claim_amount}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Provider Information */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="provider_name">Provider Name *</Label>
                    <Input
                      id="provider_name"
                      value={formData.provider_name}
                      onChange={(e) => updateFormData('provider_name', e.target.value)}
                      placeholder="Dr. Jane Smith"
                      className={errors.provider_name ? 'border-red-500' : ''}
                    />
                    {errors.provider_name && (
                      <p className="text-sm text-red-500">{errors.provider_name}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="provider_npi">Provider NPI (Optional)</Label>
                    <Input
                      id="provider_npi"
                      value={formData.provider_npi || ''}
                      onChange={(e) => updateFormData('provider_npi', e.target.value)}
                      placeholder="1234567890"
                      maxLength={10}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="priority">Claim Priority</Label>
                  <Select 
                    value={formData.priority?.toString()} 
                    onValueChange={(value) => updateFormData('priority', parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select priority level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">Normal - Standard processing</SelectItem>
                      <SelectItem value="2">High - Expedited processing</SelectItem>
                      <SelectItem value="3">Urgent - Emergency processing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="notes">Additional Notes (Optional)</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes || ''}
                    onChange={(e) => updateFormData('notes', e.target.value)}
                    placeholder="Any additional information about this claim..."
                    rows={4}
                  />
                </div>
              </div>
            )}

            {/* Step 4: Review */}
            {currentStep === 4 && (
              <div className="space-y-6">
                <div className="bg-gray-50 p-6 rounded-lg">
                  <h3 className="text-lg font-semibold mb-4">Review Your Claim</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Patient Information</h4>
                      <dl className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Name:</dt>
                          <dd>{formData.patient_name}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Patient ID:</dt>
                          <dd>{formData.patient_id}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Insurance:</dt>
                          <dd>{formData.insurance_provider}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Policy:</dt>
                          <dd>{formData.policy_number}</dd>
                        </div>
                      </dl>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Medical Details</h4>
                      <dl className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Diagnosis:</dt>
                          <dd>{formData.diagnosis_code}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Procedure:</dt>
                          <dd>{formData.procedure_code}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Service Date:</dt>
                          <dd>{formData.service_date}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Amount:</dt>
                          <dd>${formData.claim_amount.toFixed(2)}</dd>
                        </div>
                      </dl>
                    </div>
                  </div>

                  <Separator className="my-4" />

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Provider Information</h4>
                    <dl className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Provider:</dt>
                        <dd>{formData.provider_name}</dd>
                      </div>
                      {formData.provider_npi && (
                        <div className="flex justify-between">
                          <dt className="text-gray-600">NPI:</dt>
                          <dd>{formData.provider_npi}</dd>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Priority:</dt>
                        <dd>
                          {formData.priority === 1 && 'Normal'}
                          {formData.priority === 2 && 'High'}
                          {formData.priority === 3 && 'Urgent'}
                        </dd>
                      </div>
                    </dl>
                  </div>

                  {formData.notes && (
                    <>
                      <Separator className="my-4" />
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Additional Notes</h4>
                        <p className="text-sm text-gray-600">{formData.notes}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-6">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentStep === 1}
              >
                Previous
              </Button>

              <div className="flex gap-2">
                {currentStep < 4 ? (
                  <Button onClick={handleNext} disabled={eligibilityChecking}>
                    {eligibilityChecking ? 'Checking Eligibility...' : 'Next'}
                  </Button>
                ) : (
                  <Button onClick={handleSubmit} disabled={submitting}>
                    {submitting ? 'Submitting...' : 'Submit Claim'}
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}