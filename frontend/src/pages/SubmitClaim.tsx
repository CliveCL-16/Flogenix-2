import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Activity, FileText, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiClient, ClaimSubmission } from "@/lib/api";

const SubmitClaim = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<ClaimSubmission>({
    patient_name: "",
    patient_id: "",
    insurance_provider: "",
    policy_number: "",
    diagnosis_code: "",
    procedure_code: "",
    claim_amount: 0,
    service_date: "",
    provider_name: "",
    provider_npi: "",
    notes: ""
  });

  // Medical code options based on backend validation
  const diagnosisCodes = [
    { value: "Z00.00", label: "Z00.00 - General adult medical examination" },
    { value: "M25.511", label: "M25.511 - Pain in right shoulder" },
    { value: "E11.9", label: "E11.9 - Type 2 diabetes mellitus" },
    { value: "J06.9", label: "J06.9 - Acute upper respiratory infection" },
    { value: "K21.9", label: "K21.9 - Gastro-esophageal reflux disease" },
    { value: "M79.3", label: "M79.3 - Panniculitis, unspecified" },
    { value: "I10", label: "I10 - Essential hypertension" },
    { value: "C50.1", label: "C50.1 - Breast cancer (central portion)" },
    { value: "C50.2", label: "C50.2 - Breast cancer (upper-inner quadrant)" },
    { value: "I21.0", label: "I21.0 - ST elevation myocardial infarction" },
    { value: "I63.1", label: "I63.1 - Cerebral infarction due to embolism" },
    { value: "I63.2", label: "I63.2 - Cerebral infarction, unspecified" }
  ];

  const procedureCodes = [
    { value: "99213", label: "99213 - Office visit, established patient, low complexity" },
    { value: "99214", label: "99214 - Office visit, established patient, moderate complexity" },
    { value: "99215", label: "99215 - Office visit, established patient, high complexity" },
    { value: "92004", label: "92004 - Ophthalmological examination and evaluation" },
    { value: "27447", label: "27447 - Arthroplasty, knee, condyle and plateau" },
    { value: "73721", label: "73721 - MRI lower extremity other than joint" },
    { value: "36415", label: "36415 - Collection of venous blood by venipuncture" },
    { value: "85025", label: "85025 - Blood count; complete (CBC), automated" }
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'claim_amount' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const claim = await apiClient.submitClaim(formData);
      
      toast({
        title: "Claim Submitted Successfully",
        description: `Your claim ${claim.claim_id} has been submitted and is being processed.`,
      });

      navigate("/user/claims");
    } catch (error) {
      toast({
        title: "Submission Failed",
        description: error instanceof Error ? error.message : "An error occurred while submitting your claim.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/user">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2" />
                Back to Portal
              </Button>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
                <Activity className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">Submit New Claim</h1>
                <p className="text-xs text-muted-foreground">File a healthcare claim for processing</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <Card className="p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
              <FileText className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-foreground">Claim Information</h2>
              <p className="text-muted-foreground">Please provide accurate information for your healthcare claim</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Patient Information */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground">Patient Information</h3>
                
                <div className="space-y-2">
                  <Label htmlFor="patient_name">Patient Name *</Label>
                  <Input
                    id="patient_name"
                    name="patient_name"
                    value={formData.patient_name}
                    onChange={handleChange}
                    required
                    placeholder="Enter patient full name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="patient_id">Patient ID *</Label>
                  <Input
                    id="patient_id"
                    name="patient_id"
                    value={formData.patient_id}
                    onChange={handleChange}
                    required
                    placeholder="Enter patient ID"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground">Insurance Details</h3>
                
                <div className="space-y-2">
                  <Label htmlFor="insurance_provider">Insurance Provider *</Label>
                  <Input
                    id="insurance_provider"
                    name="insurance_provider"
                    value={formData.insurance_provider}
                    onChange={handleChange}
                    required
                    placeholder="e.g., BlueCross BlueShield"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="policy_number">Policy Number *</Label>
                  <Input
                    id="policy_number"
                    name="policy_number"
                    value={formData.policy_number}
                    onChange={handleChange}
                    required
                    placeholder="Enter policy number"
                  />
                </div>
              </div>
            </div>

            {/* Medical Information */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground">Medical Information</h3>
                
                <div className="space-y-2">
                  <Label htmlFor="diagnosis_code">Diagnosis Code (ICD-10) *</Label>
                  <Select value={formData.diagnosis_code} onValueChange={(value) => handleSelectChange('diagnosis_code', value)} required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select diagnosis code" />
                    </SelectTrigger>
                    <SelectContent>
                      {diagnosisCodes.map((code) => (
                        <SelectItem key={code.value} value={code.value}>
                          {code.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="procedure_code">Procedure Code (CPT) *</Label>
                  <Select value={formData.procedure_code} onValueChange={(value) => handleSelectChange('procedure_code', value)} required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select procedure code" />
                    </SelectTrigger>
                    <SelectContent>
                      {procedureCodes.map((code) => (
                        <SelectItem key={code.value} value={code.value}>
                          {code.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="service_date">Service Date *</Label>
                  <Input
                    id="service_date"
                    name="service_date"
                    type="date"
                    value={formData.service_date}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground">Provider & Financial</h3>
                
                <div className="space-y-2">
                  <Label htmlFor="provider_name">Provider Name *</Label>
                  <Input
                    id="provider_name"
                    name="provider_name"
                    value={formData.provider_name}
                    onChange={handleChange}
                    required
                    placeholder="Healthcare provider name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="provider_npi">Provider NPI</Label>
                  <Input
                    id="provider_npi"
                    name="provider_npi"
                    value={formData.provider_npi}
                    onChange={handleChange}
                    placeholder="National Provider Identifier"
                    maxLength={10}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="claim_amount">Claim Amount ($) *</Label>
                  <Input
                    id="claim_amount"
                    name="claim_amount"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.claim_amount}
                    onChange={handleChange}
                    required
                    placeholder="0.00"
                  />
                </div>
              </div>
            </div>

            {/* Additional Notes */}
            <div className="space-y-2">
              <Label htmlFor="notes">Additional Notes</Label>
              <Textarea
                id="notes"
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                placeholder="Any additional information about this claim..."
                rows={4}
                maxLength={500}
              />
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-4 pt-6">
              <Button 
                type="submit" 
                disabled={isSubmitting}
                className="flex-1"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Claim"
                )}
              </Button>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => navigate("/user")}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      </main>
    </div>
  );
};

export default SubmitClaim;