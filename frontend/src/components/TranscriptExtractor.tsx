'use client';

import { useState } from 'react';
import { useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { extractWithCustomCategories, saveFlaggedResponse, uploadTranscriptPDF, type ExtractRequest, type ExtractionResponse, type CustomCategory, type FlaggedResponseRequest, type UserInfo } from '@/lib/api';
import { FileText, Loader2, Download, AlertCircle, CheckCircle, Plus, X, Settings, Flag, Save, Eye, BookOpen, Upload, Edit, History, AlertTriangle, Info, FileDown } from 'lucide-react';
import SOPManager from './SOPManager';
import VisitSummaryPDF from './VisitSummaryPDF';
import { PDFDownloadLink } from '@react-pdf/renderer';

// Confidence indicator component
const ConfidenceIndicator = ({ confidence, reasoning, issues, suggestions }: {
  confidence: 'high' | 'medium' | 'low';
  reasoning: string;
  issues?: string[];
  suggestions?: string[];
}) => {
  const getConfidenceColor = (conf: string) => {
    switch (conf) {
      case 'high': return 'text-green-600 bg-green-50 border-green-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getConfidenceIcon = (conf: string) => {
    switch (conf) {
      case 'high': return <CheckCircle className="w-4 h-4" />;
      case 'medium': return <AlertTriangle className="w-4 h-4" />;
      case 'low': return <AlertCircle className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  return (
    <div className="mt-2">
      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${getConfidenceColor(confidence)}`}>
        {getConfidenceIcon(confidence)}
        {confidence.charAt(0).toUpperCase() + confidence.slice(1)} Confidence
      </div>
      <div className="mt-1 text-xs text-gray-600">
        <p className="font-medium">Reasoning:</p>
        <p>{reasoning}</p>
        {issues && issues.length > 0 && (
          <div className="mt-1">
            <p className="font-medium text-red-600">Issues:</p>
            <ul className="list-disc list-inside">
              {issues.map((issue, idx) => (
                <li key={idx}>{issue}</li>
              ))}
            </ul>
          </div>
        )}
        {suggestions && suggestions.length > 0 && (
          <div className="mt-1">
            <p className="font-medium text-blue-600">Suggestions:</p>
            <ul className="list-disc list-inside">
              {suggestions.map((suggestion, idx) => (
                <li key={idx}>{suggestion}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

// Flagged item wrapper component
const FlaggedItem = ({ isFlagged, children }: { isFlagged: boolean; children: React.ReactNode }) => {
  if (!isFlagged) return <>{children}</>;
  
  return (
    <div className="border-2 border-red-200 bg-red-50 p-3 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <Flag className="w-4 h-4 text-red-600" />
        <span className="text-sm font-medium text-red-700">Flagged for Review</span>
      </div>
      {children}
    </div>
  );
};

export default function TranscriptExtractor() {
  const { user } = useUser();
  const router = useRouter();
  const [transcriptText, setTranscriptText] = useState('');
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCustomCategories, setShowCustomCategories] = useState(false);
  const [customCategories, setCustomCategories] = useState<CustomCategory[]>([
    {
      name: "billing_follow_up",
      description: "Extract any billing-related tasks or follow-ups mentioned",
      field_type: "structured",
      required_fields: ["task_description", "department", "priority"],
      optional_fields: ["due_date", "notes"]
    }
  ]);

  const [newCategory, setNewCategory] = useState({
    name: '',
    description: '',
    field_type: 'structured' as 'structured' | 'text',
    required_fields: '',
    optional_fields: ''
  });

  // Flagged response handling
  const [isFlagged, setIsFlagged] = useState(false);
  const [flaggedData, setFlaggedData] = useState<ExtractionResponse | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [isSavingFlagged, setIsSavingFlagged] = useState(false);
  const [showTranscript, setShowTranscript] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isCancelled, setIsCancelled] = useState(false);
  
  // SOP management
  const [showSOPManager, setShowSOPManager] = useState(false);
  const [selectedSOPs, setSelectedSOPs] = useState<number[]>([]);
  
  // PDF transcript upload
  const [uploadingTranscript, setUploadingTranscript] = useState(false);
  const [transcriptFile, setTranscriptFile] = useState<File | null>(null);
  
  // PDF generation state
  const [patientName, setPatientName] = useState('Patient');
  const [clinicName, setClinicName] = useState('Animal Hospital');
  
  // Editable extraction data for review
  const [editableExtraction, setEditableExtraction] = useState<{
    follow_up_tasks: Array<{description: string, priority: string, due_date?: string, assigned_to?: string}>;
    medication_instructions: Array<{medication_name: string, dosage: string, frequency: string, duration?: string, special_instructions?: string}>;
    client_reminders: Array<{description: string, reminder_type: string, priority?: string, due_date?: string}>;
    clinician_todos: Array<{description: string, task_type: string, priority?: string, due_date?: string}>;
    custom_extractions?: Record<string, {
      extracted_data: string;
      confidence: string;
      reasoning?: string;
    }>;
  } | null>(null);

  const addCustomCategory = () => {
    if (!newCategory.name.trim() || !newCategory.description.trim()) {
      setError('Category name and description are required');
      return;
    }

    const requiredFields = newCategory.required_fields
      .split(',')
      .map(field => field.trim())
      .filter(field => field.length > 0);

    const optionalFields = newCategory.optional_fields
      .split(',')
      .map(field => field.trim())
      .filter(field => field.length > 0);

    const category: CustomCategory = {
      name: newCategory.name.trim(),
      description: newCategory.description.trim(),
      field_type: newCategory.field_type,
      required_fields: requiredFields,
      optional_fields: optionalFields.length > 0 ? optionalFields : undefined
    };

    setCustomCategories([...customCategories, category]);
    setNewCategory({
      name: '',
      description: '',
      field_type: 'structured',
      required_fields: '',
      optional_fields: ''
    });
    setError(null);
  };

  const removeCustomCategory = (index: number) => {
    setCustomCategories(customCategories.filter((_, i) => i !== index));
  };

  // Helper to parse extracted_data string to object
  function parseExtractedData(data: string): Record<string, string> | string {
    try {
      // Try to parse as JSON first
      if (data.trim().startsWith('{') && data.trim().endsWith('}')) {
        // Replace single quotes with double quotes for JSON.parse
        const jsonReady = data.replace(/([a-zA-Z0-9_]+):/g, '"$1":').replace(/'/g, '"');
        return JSON.parse(jsonReady) as Record<string, string>;
      }
      return data;
    } catch {
      // Fallback: split by comma and colon
      return data.split(',').reduce((acc, pair) => {
        const [k, v] = pair.split(':');
        if (k && v) acc[k.trim()] = v.trim();
        return acc;
      }, {} as Record<string, string>);
    }
  }

  // Helper functions for editing extraction data
  const initializeEditableExtraction = (extraction: ExtractionResponse['extraction']) => {
    setEditableExtraction({
      follow_up_tasks: (extraction.follow_up_tasks ?? []) as Array<{description: string, priority: string, due_date?: string, assigned_to?: string}>,
      medication_instructions: (extraction.medication_instructions ?? []) as Array<{medication_name: string, dosage: string, frequency: string, duration?: string, special_instructions?: string}>,
      client_reminders: (extraction.client_reminders ?? []) as Array<{description: string, reminder_type: string, priority?: string, due_date?: string}>,
      clinician_todos: (extraction.clinician_todos ?? []) as Array<{description: string, task_type: string, priority?: string, due_date?: string}>,
      custom_extractions: (extraction.custom_extractions ?? {}) as Record<string, {
        extracted_data: string;
        confidence: string;
        reasoning?: string;
      }>
    });
  };

  const updateFollowUpTask = (index: number, field: string, value: string) => {
    if (!editableExtraction) return;
    const updatedTasks = [...editableExtraction.follow_up_tasks];
    updatedTasks[index] = { ...updatedTasks[index], [field]: value } as typeof updatedTasks[0];
    setEditableExtraction({ ...editableExtraction, follow_up_tasks: updatedTasks });
  };

  const updateMedication = (index: number, field: string, value: string) => {
    if (!editableExtraction) return;
    const updatedMeds = [...editableExtraction.medication_instructions];
    updatedMeds[index] = { ...updatedMeds[index], [field]: value } as typeof updatedMeds[0];
    setEditableExtraction({ ...editableExtraction, medication_instructions: updatedMeds });
  };

  const updateClientReminder = (index: number, field: string, value: string) => {
    if (!editableExtraction) return;
    const updatedReminders = [...editableExtraction.client_reminders];
    updatedReminders[index] = { ...updatedReminders[index], [field]: value } as typeof updatedReminders[0];
    setEditableExtraction({ ...editableExtraction, client_reminders: updatedReminders });
  };

  const updateClinicianTodo = (index: number, field: string, value: string) => {
    if (!editableExtraction) return;
    const updatedTodos = [...editableExtraction.clinician_todos];
    updatedTodos[index] = { ...updatedTodos[index], [field]: value } as typeof updatedTodos[0];
    setEditableExtraction({ ...editableExtraction, clinician_todos: updatedTodos });
  };

  const addFollowUpTask = () => {
    if (!editableExtraction) return;
    const newTask = { description: '', priority: 'medium', due_date: '', assigned_to: 'clinician' };
    setEditableExtraction({
      ...editableExtraction,
      follow_up_tasks: [...editableExtraction.follow_up_tasks, newTask]
    });
  };

  const addMedication = () => {
    if (!editableExtraction) return;
    const newMed = { medication_name: '', dosage: '', frequency: '', duration: '30 days', special_instructions: '' };
    setEditableExtraction({
      ...editableExtraction,
      medication_instructions: [...editableExtraction.medication_instructions, newMed]
    });
  };

  const addClientReminder = () => {
    if (!editableExtraction) return;
    const newReminder = { description: '', reminder_type: 'other', priority: 'medium', due_date: '' };
    setEditableExtraction({
      ...editableExtraction,
      client_reminders: [...editableExtraction.client_reminders, newReminder]
    });
  };

  const addClinicianTodo = () => {
    if (!editableExtraction) return;
    const newTodo = { description: '', task_type: 'other', priority: 'medium', due_date: '' };
    setEditableExtraction({
      ...editableExtraction,
      clinician_todos: [...editableExtraction.clinician_todos, newTodo]
    });
  };

  const removeItem = (category: 'follow_up_tasks' | 'medication_instructions' | 'client_reminders' | 'clinician_todos', index: number) => {
    if (!editableExtraction) return;
    const updatedArray = editableExtraction[category].filter((_, i) => i !== index);
    setEditableExtraction({ ...editableExtraction, [category]: updatedArray });
  };

  const updateCustomExtraction = (categoryName: string, field: 'extracted_data' | 'confidence' | 'reasoning', value: string) => {
    if (!editableExtraction?.custom_extractions) return;
    const updatedCustomExtractions = { ...editableExtraction.custom_extractions };
    if (updatedCustomExtractions[categoryName]) {
      updatedCustomExtractions[categoryName] = {
        ...updatedCustomExtractions[categoryName],
        [field]: value
      };
      setEditableExtraction({ ...editableExtraction, custom_extractions: updatedCustomExtractions });
    }
  };

  const addCustomExtraction = () => {
    if (!editableExtraction) return;
    const newCategoryName = prompt('Enter category name for new custom extraction:');
    if (!newCategoryName?.trim()) return;
    
    const updatedCustomExtractions = { ...(editableExtraction.custom_extractions ?? {}) };
    updatedCustomExtractions[newCategoryName] = {
      extracted_data: '',
      confidence: 'medium',
      reasoning: ''
    };
    setEditableExtraction({ ...editableExtraction, custom_extractions: updatedCustomExtractions });
  };

  const removeCustomExtraction = (categoryName: string) => {
    if (!editableExtraction?.custom_extractions) return;
    const updatedCustomExtractions = { ...editableExtraction.custom_extractions };
    delete updatedCustomExtractions[categoryName];
    setEditableExtraction({ ...editableExtraction, custom_extractions: updatedCustomExtractions });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transcriptText.trim()) {
      setError('Please enter transcript text');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);
    setIsFlagged(false);
    setFlaggedData(null);
    setEditableExtraction(null);

    try {
      // Get Clerk user ID from auth context
      if (!user?.id) {
        setError('User not authenticated');
        return;
      }
      
      // Prepare user info from Clerk
      const userInfo: UserInfo = {
        id: user.id,
        email: user.emailAddresses?.[0]?.emailAddress,
        name: user.fullName ?? `${user.firstName ?? ''} ${user.lastName ?? ''}`.trim()
      };

      const request: ExtractRequest = {
        transcript_text: transcriptText,
        notes: notes || undefined,
        user_id: user.id, // Send actual Clerk user ID
        user_info: userInfo, // Send user info for creation/finding
        custom_categories: customCategories.length > 0 ? customCategories : undefined,
        sop_ids: selectedSOPs.length > 0 ? selectedSOPs : undefined
      };

      // Log the request body
      console.log('🚀 API Request Body:', JSON.stringify(request, null, 2));
      console.log('🔍 User ID being sent:', user.id);
      console.log('🔍 Custom categories:', customCategories);

      const response = await extractWithCustomCategories(request);
      
      // Log the response body
      console.log('📥 API Response Body:', JSON.stringify(response, null, 2));
      
      // Check if response is flagged for review or confidence is medium/low
      const flagged = response.flagged === true || ['medium', 'low'].includes((response.confidence_level ?? '').toLowerCase());
      if (flagged) {
        setIsFlagged(true);
        setFlaggedData(response);
        setResult(response);
        // Initialize editable extraction data
        initializeEditableExtraction(response.extraction);
      } else {
        setResult(response);
      }
    } catch (err) {
      console.error('❌ API Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveFlaggedResponse = async () => {
    if (!flaggedData || !editableExtraction) return;

    setIsSavingFlagged(true);
    setError(null);

    try {
      // Use the editable extraction data instead of the original
      const updatedExtractionData = {
        ...flaggedData.extraction,
        ...editableExtraction,
        flagged: false
      };

      const request: FlaggedResponseRequest = {
        transcript_id: flaggedData.transcript?.id ?? 0,
        extraction_data: updatedExtractionData as unknown as Record<string, unknown>,
        review_notes: reviewNotes,
        reviewed_by: 'human'
      };

      // Log the flagged response save request
      console.log('🚀 Save Flagged Response Request:', JSON.stringify(request, null, 2));

      const response = await saveFlaggedResponse(request);
      
      // Log the flagged response save response
      console.log('📥 Save Flagged Response Response:', JSON.stringify(response, null, 2));
      
      // Update the result to show it's been saved
      setResult({
        ...flaggedData,
        extraction: updatedExtractionData as ExtractionResponse['extraction'],
        flagged: false,
        confidence_level: 'reviewed',
        message: 'Response saved after human review'
      });
      
      setIsFlagged(false);
      setFlaggedData(null);
      setReviewNotes('');
      setEditableExtraction(null);
      setIsEditing(false);
      setShowTranscript(true);
      
    } catch (err) {
      console.error('❌ Save Flagged Response Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while saving');
    } finally {
      setIsSavingFlagged(false);
    }
  };

  const downloadResults = () => {
    if (!result) return;
    
    const dataStr = JSON.stringify(result, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'extraction-results.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleTranscriptFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setTranscriptFile(file);
      setError(null);
    }
  };

  const handleUploadTranscriptPDF = async () => {
    if (!transcriptFile) return;
    
    setUploadingTranscript(true);
    setError(null);
    
    try {
      const result = await uploadTranscriptPDF(transcriptFile);
      
      if (result.success && result.extracted_text) {
        setTranscriptText(result.extracted_text);
        setTranscriptFile(null);
        // Reset file input
        const fileInput = document.getElementById('transcript-file') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      } else {
        throw new Error(result.error ?? 'Failed to extract text from PDF');
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload transcript PDF');
    } finally {
      setUploadingTranscript(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Extract Medical Actions
              </CardTitle>
              <CardDescription>
                Enter medical visit transcript text to extract actionable items, medications, and follow-up tasks
              </CardDescription>
            </div>
            <Button
              onClick={() => router.push('/review_extractions')}
              variant="outline"
              className="flex items-center gap-2"
            >
              <History className="w-4 h-4" />
              Review Extractions
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="transcript">Medical Transcript *</Label>
                                  <div className="flex gap-2">
                    <Input
                      id="transcript-file"
                      type="file"
                      accept=".pdf"
                      onChange={handleTranscriptFileSelect}
                      className="hidden"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => document.getElementById('transcript-file')?.click()}
                      className="flex items-center gap-2"
                    >
                      <Upload className="w-4 h-4" />
                      Upload PDF
                    </Button>
                  </div>
              </div>
              
              {transcriptFile && (
                <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-blue-800">
                      <FileText className="w-4 h-4 inline mr-2" />
                      Selected: {transcriptFile.name} ({(transcriptFile.size / 1024).toFixed(1)} KB)
                    </p>
                    <Button
                      type="button"
                      variant="default"
                      size="sm"
                      onClick={handleUploadTranscriptPDF}
                      disabled={uploadingTranscript}
                      className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
                    >
                      {uploadingTranscript ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Extracting...
                        </>
                      ) : (
                        <>
                          <FileText className="w-4 h-4" />
                          Extract Text from PDF
                        </>
                      )}
                    </Button>
                  </div>
                  {!transcriptText && (
                    <p className="text-xs text-blue-600 mt-2">
                      Click &ldquo;Extract Text from PDF&rdquo; to process the file and populate the transcript field below.
                    </p>
                  )}
                </div>
              )}
              
              <Textarea
                id="transcript"
                placeholder="Paste the medical visit transcript here or upload a PDF file..."
                value={transcriptText}
                onChange={(e) => setTranscriptText(e.target.value)}
                className="min-h-[200px]"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Additional Notes (Optional)</Label>
              <Textarea
                id="notes"
                placeholder="Any additional context or notes..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="min-h-[100px]"
              />
            </div>

            {/* PDF Customization Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="patient-name">Patient Name (for PDF)</Label>
                <Input
                  id="patient-name"
                  placeholder="e.g., Korra Trujillo"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="clinic-name">Clinic Name (for PDF)</Label>
                <Input
                  id="clinic-name"
                  placeholder="e.g., Berthoud Animal Hospital"
                  value={clinicName}
                  onChange={(e) => setClinicName(e.target.value)}
                />
              </div>
            </div>

            {/* Custom Categories Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-base font-medium">Custom Extraction Categories</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCustomCategories(!showCustomCategories)}
                  className="flex items-center gap-2"
                >
                  <Settings className="w-4 h-4" />
                  {showCustomCategories ? 'Hide' : 'Configure'}
                </Button>
              </div>

              {showCustomCategories && (
                <Card className="border-dashed border-2 border-slate-300">
                  <CardContent className="pt-6">
                    <div className="space-y-4">
                      {/* Existing Categories */}
                      {customCategories.length > 0 && (
                        <div className="space-y-3">
                          <Label className="text-sm font-medium text-slate-700">Current Categories:</Label>
                          {customCategories.map((category, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                              <div className="flex-1">
                                <p className="font-medium text-sm">{category.name}</p>
                                <p className="text-xs text-slate-600">{category.description}</p>
                                <p className="text-xs text-slate-500">
                                  Type: {category.field_type} | 
                                  Required: {category.required_fields.join(', ')}
                                  {category.optional_fields && ` | Optional: ${category.optional_fields.join(', ')}`}
                                </p>
                              </div>
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => removeCustomCategory(index)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Add New Category Form */}
                      <div className="space-y-4 pt-4 border-t border-slate-200">
                        <Label className="text-sm font-medium text-slate-700">Add New Category:</Label>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="category-name">Category Name *</Label>
                            <Input
                              id="category-name"
                              placeholder="e.g., billing_follow_up"
                              value={newCategory.name}
                              onChange={(e) => setNewCategory({...newCategory, name: e.target.value})}
                            />
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="field-type">Field Type *</Label>
                            <select
                              id="field-type"
                              value={newCategory.field_type}
                              onChange={(e) => setNewCategory({...newCategory, field_type: e.target.value as 'structured' | 'text'})}
                              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="structured">Structured</option>
                              <option value="text">Text</option>
                            </select>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="category-description">Description *</Label>
                          <Textarea
                            id="category-description"
                            placeholder="Describe what this category should extract..."
                            value={newCategory.description}
                            onChange={(e) => setNewCategory({...newCategory, description: e.target.value})}
                            className="min-h-[80px]"
                          />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="required-fields">Required Fields (comma-separated)</Label>
                            <Input
                              id="required-fields"
                              placeholder="e.g., task_description, department, priority"
                              value={newCategory.required_fields}
                              onChange={(e) => setNewCategory({...newCategory, required_fields: e.target.value})}
                            />
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="optional-fields">Optional Fields (comma-separated)</Label>
                            <Input
                              id="optional-fields"
                              placeholder="e.g., due_date, notes"
                              value={newCategory.optional_fields}
                              onChange={(e) => setNewCategory({...newCategory, optional_fields: e.target.value})}
                            />
                          </div>
                        </div>

                        <Button
                          type="button"
                          onClick={addCustomCategory}
                          variant="outline"
                          className="w-full"
                        >
                          <Plus className="w-4 h-4 mr-2" />
                          Add Category
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* SOP Management Section - All buttons have type="button" to prevent form submission */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-base font-medium">Clinic Policies & Procedures (SOPs)</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSOPManager(!showSOPManager)}
                  className="flex items-center gap-2"
                >
                  <BookOpen className="w-4 h-4" />
                  {showSOPManager ? 'Hide' : 'Manage SOPs'}
                </Button>
              </div>

              {showSOPManager && (
                <SOPManager
                  selectedSOPs={selectedSOPs}
                  onSOPSelectionChange={setSelectedSOPs}
                />
              )}

              {selectedSOPs.length > 0 && !showSOPManager && (
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <BookOpen className="w-4 h-4 inline mr-2" />
                    {selectedSOPs.length} SOP{selectedSOPs.length !== 1 ? 's' : ''} selected for context
                  </p>
                </div>
              )}
            </div>

            <Button 
              type="submit" 
              disabled={isLoading || !transcriptText.trim()}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4 mr-2" />
                  Extract Medical Actions
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">Error: {error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Flagged Response Display Interface */}
      {isFlagged && flaggedData && !isEditing && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-700">
              <Flag className="w-5 h-5" />
              Flagged for Review
            </CardTitle>
            <CardDescription>
              This extraction requires human review before saving
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Transcript Toggle */}
            <div className="flex items-center justify-between">
              <Label className="text-base font-medium">Original Transcript</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowTranscript(!showTranscript)}
                className="flex items-center gap-2"
              >
                {showTranscript ? (
                  <>
                    <Eye className="w-4 h-4" />
                    Hide Transcript
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    Show Transcript
                  </>
                )}
              </Button>
            </div>

            {/* Transcript Display */}
            {showTranscript && (
              <div className="bg-white p-4 rounded-lg border">
                <Label className="text-sm font-medium text-slate-700 mb-2">Medical Transcript</Label>
                <div className="bg-slate-50 p-3 rounded text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                  {flaggedData.transcript?.transcript_text}
                </div>
              </div>
            )}

            {/* Extraction Results Display */}
            <div className="space-y-4">
              <Label className="text-base font-medium">Extracted Medical Actions</Label>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-slate-800 mb-2">Follow-up Tasks</h4>
                  <div className="space-y-2">
                    {flaggedData.extraction.follow_up_tasks.length > 0 ? (
                      <>
                        {flaggedData.extraction.follow_up_tasks.map((task, index) => {
                          const isFlagged = flaggedData.confidence_details?.flagged_sections?.follow_up_tasks?.includes(index) ?? false;
                          const confidenceInfo = flaggedData.confidence_details?.item_confidence?.follow_up_tasks?.[index]?.confidence;
                          
                          return (
                            <FlaggedItem key={index} isFlagged={isFlagged}>
                              <div className="text-sm p-2 bg-slate-50 rounded">
                                <p className="font-medium">{task.description}</p>
                                <p className="text-slate-600">Priority: {task.priority}</p>
                                {task.due_date && <p className="text-slate-600">Due: {task.due_date}</p>}
                                {confidenceInfo && (
                                  <ConfidenceIndicator
                                    confidence={confidenceInfo.confidence}
                                    reasoning={confidenceInfo.reasoning}
                                    issues={confidenceInfo.issues}
                                    suggestions={confidenceInfo.suggestions}
                                  />
                                )}
                              </div>
                            </FlaggedItem>
                          );
                        })}
                      </>
                    ) : (
                      <p className="text-slate-500 text-sm">No follow-up tasks found</p>
                    )}
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-slate-800 mb-2">Medications</h4>
                  <div className="space-y-2">
                    {flaggedData.extraction.medication_instructions.length > 0 ? (
                      <>
                        {flaggedData.extraction.medication_instructions.map((med, index) => {
                          const isFlagged = flaggedData.confidence_details?.flagged_sections?.medication_instructions?.includes(index) ?? false;
                          const confidenceInfo = flaggedData.confidence_details?.item_confidence?.medication_instructions?.[index]?.confidence;
                          
                          return (
                            <FlaggedItem key={index} isFlagged={isFlagged}>
                              <div className="text-sm p-2 bg-slate-50 rounded">
                                <p className="font-medium">{med.medication_name}</p>
                                <p className="text-slate-600">{med.dosage} - {med.frequency}</p>
                                <p className="text-slate-600">Duration: {med.duration}</p>
                                {confidenceInfo && (
                                  <ConfidenceIndicator
                                    confidence={confidenceInfo.confidence}
                                    reasoning={confidenceInfo.reasoning}
                                    issues={confidenceInfo.issues}
                                    suggestions={confidenceInfo.suggestions}
                                  />
                                )}
                              </div>
                            </FlaggedItem>
                          );
                        })}
                      </>
                    ) : (
                      <p className="text-slate-500 text-sm">No medications found</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-slate-800 mb-2">Client Reminders</h4>
                  <div className="space-y-2">
                    {flaggedData.extraction.client_reminders.length > 0 ? (
                      <>
                        {flaggedData.extraction.client_reminders.map((reminder, index) => {
                          const isFlagged = flaggedData.confidence_details?.flagged_sections?.client_reminders?.includes(index) ?? false;
                          const confidenceInfo = flaggedData.confidence_details?.item_confidence?.client_reminders?.[index]?.confidence;
                          
                          return (
                            <FlaggedItem key={index} isFlagged={isFlagged}>
                              <div className="text-sm p-2 bg-slate-50 rounded">
                                <p className="font-medium">{reminder.description}</p>
                                <p className="text-slate-600">Type: {reminder.reminder_type}</p>
                                <p className="text-slate-600">Priority: {reminder.priority}</p>
                                {confidenceInfo && (
                                  <ConfidenceIndicator
                                    confidence={confidenceInfo.confidence}
                                    reasoning={confidenceInfo.reasoning}
                                    issues={confidenceInfo.issues}
                                    suggestions={confidenceInfo.suggestions}
                                  />
                                )}
                              </div>
                            </FlaggedItem>
                          );
                        })}
                      </>
                    ) : (
                      <p className="text-slate-500 text-sm">No client reminders found</p>
                    )}
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-slate-800 mb-2">Clinician Tasks</h4>
                  <div className="space-y-2">
                    {flaggedData.extraction.clinician_todos.length > 0 ? (
                      <>
                        {flaggedData.extraction.clinician_todos.map((todo, index) => {
                          const isFlagged = flaggedData.confidence_details?.flagged_sections?.clinician_todos?.includes(index) ?? false;
                          const confidenceInfo = flaggedData.confidence_details?.item_confidence?.clinician_todos?.[index]?.confidence;
                          
                          return (
                            <FlaggedItem key={index} isFlagged={isFlagged}>
                              <div className="text-sm p-2 bg-slate-50 rounded">
                                <p className="font-medium">{todo.description}</p>
                                <p className="text-slate-600">Type: {todo.task_type}</p>
                                <p className="text-slate-600">Priority: {todo.priority}</p>
                                {confidenceInfo && (
                                  <ConfidenceIndicator
                                    confidence={confidenceInfo.confidence}
                                    reasoning={confidenceInfo.reasoning}
                                    issues={confidenceInfo.issues}
                                    suggestions={confidenceInfo.suggestions}
                                  />
                                )}
                              </div>
                            </FlaggedItem>
                          );
                        })}
                      </>
                    ) : (
                      <p className="text-slate-500 text-sm">No clinician tasks found</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Custom Extractions Display */}
              {flaggedData.extraction.custom_extractions && Object.keys(flaggedData.extraction.custom_extractions).length > 0 && (
                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-slate-800 mb-2">Custom Extractions</h4>
                  <div className="space-y-4">
                    {Object.entries(flaggedData.extraction.custom_extractions).map(([cat, val]) => {
                      const parsed = val as {extracted_data: string, confidence?: string, reasoning?: string};
                      const extracted = parsed.extracted_data;
                      const parsedData = typeof extracted === 'string' ? parseExtractedData(extracted) : extracted;
                      return (
                        <div key={cat} className="text-sm p-2 bg-slate-50 rounded">
                          <div className="font-semibold text-slate-700 mb-1">{cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                          <div className="mb-1">
                            {typeof parsedData === 'object' ? (
                              <ul className="ml-4 list-disc">
                                {Object.entries(parsedData).map(([k, v]) => (
                                  <li key={k}><span className="font-medium">{k}:</span> {String(v)}</li>
                                ))}
                              </ul>
                            ) : (
                              <span>{String(parsedData)}</span>
                            )}
                          </div>
                          <div className="text-xs text-slate-600 mb-1">Confidence: {parsed.confidence}</div>
                          {parsed.reasoning && <div className="text-xs text-slate-500">Reasoning: {parsed.reasoning}</div>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                onClick={() => {
                  setIsEditing(true);
                  initializeEditableExtraction(flaggedData.extraction);
                }}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit & Save Extraction
              </Button>
              
              <Button
                onClick={() => {
                  setIsCancelled(true);
                  setIsFlagged(false);
                  setFlaggedData(null);
                  setShowTranscript(true);
                  setIsEditing(false);
                }}
                variant="outline"
                className="flex-1"
              >
                <X className="w-4 h-4 mr-2" />
                Cancel Review
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Flagged Response Edit Interface */}
      {isFlagged && flaggedData && editableExtraction && isEditing && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-700">
              <Flag className="w-5 h-5" />
              Edit Extraction
            </CardTitle>
            <CardDescription>
              Edit the extracted medical actions below. You can modify any details before saving.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Review Notes */}
            <div className="space-y-2">
              <Label htmlFor="review-notes">Review Notes (Optional)</Label>
              <Textarea
                id="review-notes"
                placeholder="Add any notes about your review..."
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                className="min-h-[100px]"
              />
            </div>

            {/* Editable Follow-up Tasks */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-base font-medium">Follow-up Tasks</Label>
                <Button type="button" variant="outline" size="sm" onClick={addFollowUpTask}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Task
                </Button>
              </div>
              <div className="space-y-3">
                {editableExtraction.follow_up_tasks.map((task, index) => {
                  const confidenceInfo = flaggedData?.confidence_details?.item_confidence?.follow_up_tasks?.[index]?.confidence;
                  
                  return (
                    <div key={index} className="p-4 bg-white rounded-lg border space-y-3">
                      {/* Confidence Indicator */}
                      {confidenceInfo && (
                        <div className="mb-2">
                          <ConfidenceIndicator
                            confidence={confidenceInfo.confidence}
                            reasoning={confidenceInfo.reasoning}
                            issues={confidenceInfo.issues}
                            suggestions={confidenceInfo.suggestions}
                          />
                        </div>
                      )}
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <Label>Description</Label>
                          <Input
                            value={task.description}
                            onChange={(e) => updateFollowUpTask(index, 'description', e.target.value)}
                            placeholder="Task description"
                          />
                        </div>
                        <div>
                          <Label>Priority</Label>
                          <select
                            value={task.priority}
                            onChange={(e) => updateFollowUpTask(index, 'priority', e.target.value)}
                            className="w-full px-3 py-2 border border-slate-300 rounded-md"
                          >
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                          </select>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <Label>Due Date</Label>
                          <Input
                            value={task.due_date ?? ''}
                            onChange={(e) => updateFollowUpTask(index, 'due_date', e.target.value)}
                            placeholder="e.g., in 2 weeks"
                          />
                        </div>
                        <div>
                          <Label>Assigned To</Label>
                          <select
                            value={task.assigned_to ?? 'clinician'}
                            onChange={(e) => updateFollowUpTask(index, 'assigned_to', e.target.value)}
                            className="w-full px-3 py-2 border border-slate-300 rounded-md"
                          >
                            <option value="clinician">Clinician</option>
                            <option value="client">Client</option>
                          </select>
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeItem('follow_up_tasks', index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <X className="w-4 h-4 mr-2" />
                        Remove Task
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Editable Medications */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-base font-medium">Medications</Label>
                <Button type="button" variant="outline" size="sm" onClick={addMedication}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Medication
                </Button>
              </div>
              <div className="space-y-3">
                {editableExtraction.medication_instructions.map((med, index) => {
                  const confidenceInfo = flaggedData?.confidence_details?.item_confidence?.medication_instructions?.[index]?.confidence;
                  
                  return (
                    <div key={index} className="p-4 bg-white rounded-lg border space-y-3">
                      {/* Confidence Indicator */}
                      {confidenceInfo && (
                        <div className="mb-2">
                          <ConfidenceIndicator
                            confidence={confidenceInfo.confidence}
                            reasoning={confidenceInfo.reasoning}
                            issues={confidenceInfo.issues}
                            suggestions={confidenceInfo.suggestions}
                          />
                        </div>
                      )}
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div>
                          <Label>Medication Name</Label>
                          <Input
                            value={med.medication_name}
                            onChange={(e) => updateMedication(index, 'medication_name', e.target.value)}
                            placeholder="e.g., lisinopril"
                          />
                        </div>
                        <div>
                          <Label>Dosage</Label>
                          <Input
                            value={med.dosage}
                            onChange={(e) => updateMedication(index, 'dosage', e.target.value)}
                            placeholder="e.g., 10mg"
                          />
                        </div>
                        <div>
                          <Label>Frequency</Label>
                          <Input
                            value={med.frequency}
                            onChange={(e) => updateMedication(index, 'frequency', e.target.value)}
                            placeholder="e.g., once daily"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <Label>Duration</Label>
                          <Input
                            value={med.duration ?? ''}
                            onChange={(e) => updateMedication(index, 'duration', e.target.value)}
                            placeholder="e.g., 30 days"
                          />
                        </div>
                        <div>
                          <Label>Special Instructions</Label>
                          <Input
                            value={med.special_instructions ?? ''}
                            onChange={(e) => updateMedication(index, 'special_instructions', e.target.value)}
                            placeholder="e.g., take with food"
                          />
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeItem('medication_instructions', index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <X className="w-4 h-4 mr-2" />
                        Remove Medication
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Editable Client Reminders */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-base font-medium">Client Reminders</Label>
                <Button type="button" variant="outline" size="sm" onClick={addClientReminder}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Reminder
                </Button>
              </div>
              <div className="space-y-3">
                {editableExtraction.client_reminders.map((reminder, index) => {
                  const confidenceInfo = flaggedData?.confidence_details?.item_confidence?.client_reminders?.[index]?.confidence;
                  
                  return (
                    <div key={index} className="p-4 bg-white rounded-lg border space-y-3">
                      {/* Confidence Indicator */}
                      {confidenceInfo && (
                        <div className="mb-2">
                          <ConfidenceIndicator
                            confidence={confidenceInfo.confidence}
                            reasoning={confidenceInfo.reasoning}
                            issues={confidenceInfo.issues}
                            suggestions={confidenceInfo.suggestions}
                          />
                        </div>
                      )}
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <Label>Description</Label>
                          <Input
                            value={reminder.description}
                            onChange={(e) => updateClientReminder(index, 'description', e.target.value)}
                            placeholder="Reminder description"
                          />
                        </div>
                        <div>
                          <Label>Reminder Type</Label>
                          <select
                            value={reminder.reminder_type}
                            onChange={(e) => updateClientReminder(index, 'reminder_type', e.target.value)}
                            className="w-full px-3 py-2 border border-slate-300 rounded-md"
                          >
                            <option value="appointment">Appointment</option>
                            <option value="medication">Medication</option>
                            <option value="test">Test</option>
                            <option value="other">Other</option>
                          </select>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <Label>Priority</Label>
                          <select
                            value={reminder.priority ?? 'medium'}
                            onChange={(e) => updateClientReminder(index, 'priority', e.target.value)}
                            className="w-full px-3 py-2 border border-slate-300 rounded-md"
                          >
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                          </select>
                        </div>
                        <div>
                          <Label>Due Date</Label>
                          <Input
                            value={reminder.due_date ?? ''}
                            onChange={(e) => updateClientReminder(index, 'due_date', e.target.value)}
                            placeholder="e.g., in 2 weeks"
                          />
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeItem('client_reminders', index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <X className="w-4 h-4 mr-2" />
                        Remove Reminder
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Editable Clinician Tasks */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-base font-medium">Clinician Tasks</Label>
                <Button type="button" variant="outline" size="sm" onClick={addClinicianTodo}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Task
                </Button>
              </div>
              <div className="space-y-3">
                {editableExtraction.clinician_todos.map((todo, index) => {
                  const confidenceInfo = flaggedData?.confidence_details?.item_confidence?.clinician_todos?.[index]?.confidence;
                  
                  return (
                    <div key={index} className="p-4 bg-white rounded-lg border space-y-3">
                      {/* Confidence Indicator */}
                      {confidenceInfo && (
                        <div className="mb-2">
                          <ConfidenceIndicator
                            confidence={confidenceInfo.confidence}
                            reasoning={confidenceInfo.reasoning}
                            issues={confidenceInfo.issues}
                            suggestions={confidenceInfo.suggestions}
                          />
                        </div>
                      )}
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <Label>Description</Label>
                          <Input
                            value={todo.description}
                            onChange={(e) => updateClinicianTodo(index, 'description', e.target.value)}
                            placeholder="Task description"
                          />
                        </div>
                        <div>
                          <Label>Task Type</Label>
                          <select
                            value={todo.task_type}
                            onChange={(e) => updateClinicianTodo(index, 'task_type', e.target.value)}
                            className="w-full px-3 py-2 border border-slate-300 rounded-md"
                          >
                            <option value="follow_up">Follow-up</option>
                            <option value="referral">Referral</option>
                            <option value="documentation">Documentation</option>
                            <option value="other">Other</option>
                          </select>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <Label>Priority</Label>
                          <select
                            value={todo.priority ?? 'medium'}
                            onChange={(e) => updateClinicianTodo(index, 'priority', e.target.value)}
                            className="w-full px-3 py-2 border border-slate-300 rounded-md"
                          >
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                          </select>
                        </div>
                        <div>
                          <Label>Due Date</Label>
                          <Input
                            value={todo.due_date ?? ''}
                            onChange={(e) => updateClinicianTodo(index, 'due_date', e.target.value)}
                            placeholder="e.g., in 2 weeks"
                          />
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeItem('clinician_todos', index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <X className="w-4 h-4 mr-2" />
                        Remove Task
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Editable Custom Extractions */}
            {editableExtraction.custom_extractions && Object.keys(editableExtraction.custom_extractions).length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label className="text-base font-medium">Custom Extractions</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addCustomExtraction}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Custom Extraction
                  </Button>
                </div>
                <div className="space-y-3">
                  {Object.entries(editableExtraction.custom_extractions).map(([categoryName, extraction]) => (
                    <div key={categoryName} className="p-4 bg-white rounded-lg border space-y-3">
                      <div className="flex items-center justify-between">
                        <Label className="text-base font-medium text-purple-700">
                          {categoryName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </Label>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeCustomExtraction(categoryName)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <X className="w-4 h-4 mr-2" />
                          Remove
                        </Button>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <Label>Extracted Data</Label>
                          <Textarea
                            value={extraction.extracted_data}
                            onChange={(e) => updateCustomExtraction(categoryName, 'extracted_data', e.target.value)}
                            placeholder="Enter extracted data..."
                            className="min-h-[80px]"
                          />
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div>
                            <Label>Confidence</Label>
                            <select
                              value={extraction.confidence}
                              onChange={(e) => updateCustomExtraction(categoryName, 'confidence', e.target.value)}
                              className="w-full px-3 py-2 border border-slate-300 rounded-md"
                            >
                              <option value="high">High</option>
                              <option value="medium">Medium</option>
                              <option value="low">Low</option>
                            </select>
                          </div>
                          <div>
                            <Label>Reasoning (Optional)</Label>
                            <Input
                              value={extraction.reasoning ?? ''}
                              onChange={(e) => updateCustomExtraction(categoryName, 'reasoning', e.target.value)}
                              placeholder="Reasoning for extraction..."
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex gap-2">
              <Button
                onClick={handleSaveFlaggedResponse}
                disabled={isSavingFlagged}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                {isSavingFlagged ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Edited Extraction
                  </>
                )}
              </Button>
              
              <Button
                onClick={() => {
                  setIsEditing(false);
                  setReviewNotes('');
                  setEditableExtraction(null);
                }}
                variant="outline"
                className="flex-1"
              >
                <X className="w-4 h-4 mr-2" />
                Cancel Editing
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cancelled Extraction Display */}
      {isCancelled && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-700">
              <X className="w-5 h-5" />
              Extraction Cancelled
            </CardTitle>
            <CardDescription>
              The extraction review was cancelled. No changes were saved.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-slate-800 mb-2">Follow-up Tasks</h4>
                <div className="space-y-2">
                  <p className="text-slate-500 text-sm">No follow-up tasks found</p>
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-slate-800 mb-2">Medications</h4>
                <div className="space-y-2">
                  <p className="text-slate-500 text-sm">No medications found</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-slate-800 mb-2">Client Reminders</h4>
                <div className="space-y-2">
                  <p className="text-slate-500 text-sm">No client reminders found</p>
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-slate-800 mb-2">Clinician Tasks</h4>
                <div className="space-y-2">
                  <p className="text-slate-500 text-sm">No clinician tasks found</p>
                </div>
              </div>
            </div>

            <Button 
              onClick={() => {
                setIsCancelled(false);
                setResult(null);
                setTranscriptText('');
                setNotes('');
                setCustomCategories([
                  {
                    name: "billing_follow_up",
                    description: "Extract any billing-related tasks or follow-ups mentioned",
                    field_type: "structured",
                    required_fields: ["task_description", "department", "priority"],
                    optional_fields: ["due_date", "notes"]
                  }
                ]);
                setSelectedSOPs([]);
                setShowSOPManager(false);
                setShowCustomCategories(false);
              }}
              variant="outline"
              className="w-full"
            >
              <FileText className="w-4 h-4 mr-2" />
              Start New Extraction
            </Button>
          </CardContent>
        </Card>
      )}

      {result && !isFlagged && !isCancelled && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-700">
              <CheckCircle className="w-5 h-5" />
              Extraction Complete
            </CardTitle>
            <CardDescription>
              Successfully extracted medical actions from the transcript
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-slate-800 mb-2">Follow-up Tasks</h4>
                <div className="space-y-2">
                  {result.extraction.follow_up_tasks.length > 0 ? (
                    result.extraction.follow_up_tasks.map((task, index) => (
                      <div key={index} className="text-sm p-2 bg-slate-50 rounded">
                        <p className="font-medium">{task.description}</p>
                        <p className="text-slate-600">Priority: {task.priority}</p>
                        {task.due_date && <p className="text-slate-600">Due: {task.due_date}</p>}
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-500 text-sm">No follow-up tasks found</p>
                  )}
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-slate-800 mb-2">Medications</h4>
                <div className="space-y-2">
                  {result.extraction.medication_instructions.length > 0 ? (
                    result.extraction.medication_instructions.map((med, index) => (
                      <div key={index} className="text-sm p-2 bg-slate-50 rounded">
                        <p className="font-medium">{med.medication_name}</p>
                        <p className="text-slate-600">{med.dosage} - {med.frequency}</p>
                        <p className="text-slate-600">Duration: {med.duration}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-500 text-sm">No medications found</p>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-slate-800 mb-2">Client Reminders</h4>
                <div className="space-y-2">
                  {result.extraction.client_reminders.length > 0 ? (
                    result.extraction.client_reminders.map((reminder, index) => (
                      <div key={index} className="text-sm p-2 bg-slate-50 rounded">
                        <p className="font-medium">{reminder.description}</p>
                        <p className="text-slate-600">Type: {reminder.reminder_type}</p>
                        <p className="text-slate-600">Priority: {reminder.priority}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-500 text-sm">No client reminders found</p>
                  )}
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-slate-800 mb-2">Clinician Tasks</h4>
                <div className="space-y-2">
                  {result.extraction.clinician_todos.length > 0 ? (
                    result.extraction.clinician_todos.map((todo, index) => (
                      <div key={index} className="text-sm p-2 bg-slate-50 rounded">
                        <p className="font-medium">{todo.description}</p>
                        <p className="text-slate-600">Type: {todo.task_type}</p>
                        <p className="text-slate-600">Priority: {todo.priority}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-500 text-sm">No clinician tasks found</p>
                  )}
                </div>
              </div>
            </div>

            {/* Custom Extractions Display */}
            {result.extraction.custom_extractions && Object.keys(result.extraction.custom_extractions).length > 0 && (
              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-slate-800 mb-2">Custom Extractions</h4>
                <div className="space-y-4">
                  {Object.entries(result.extraction.custom_extractions).map(([cat, val]) => {
                    const parsed = val as {extracted_data: string, confidence?: string, reasoning?: string};
                    const extracted = parsed.extracted_data;
                    const parsedData = typeof extracted === 'string' ? parseExtractedData(extracted) : extracted;
                    return (
                      <div key={cat} className="text-sm p-2 bg-slate-50 rounded">
                        <div className="font-semibold text-slate-700 mb-1">{cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                        <div className="mb-1">
                          {typeof parsedData === 'object' ? (
                            <ul className="ml-4 list-disc">
                              {Object.entries(parsedData).map(([k, v]) => (
                                <li key={k}><span className="font-medium">{k}:</span> {String(v)}</li>
                              ))}
                            </ul>
                          ) : (
                            <span>{String(parsedData)}</span>
                          )}
                        </div>
                        <div className="text-xs text-slate-600 mb-1">Confidence: {parsed.confidence}</div>
                        {parsed.reasoning && <div className="text-xs text-slate-500">Reasoning: {parsed.reasoning}</div>}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {result.processing_time && (
              <div className="text-center text-sm text-slate-600">
                Processing time: {result.processing_time.toFixed(2)}s
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button 
                onClick={downloadResults}
                variant="outline"
                className="w-full"
              >
                <Download className="w-4 h-4 mr-2" />
                Download Results (JSON)
              </Button>
              
              {result && (
                <PDFDownloadLink
                  document={
                    <VisitSummaryPDF
                      extraction={{
                        ...result.extraction,
                        custom_extractions: result.extraction.custom_extractions ? 
                          Object.entries(result.extraction.custom_extractions).reduce((acc, [key, value]) => ({
                            ...acc,
                            [key]: value as { extracted_data: string; confidence: string; reasoning?: string }
                          }), {}) : undefined
                      }}
                      patientName={patientName}
                      clinicName={clinicName}
                      visitDate={new Date().toLocaleDateString()}
                    />
                  }
                  fileName={`${patientName.replace(/\s+/g, '_')}_visit_summary.pdf`}
                  className="w-full"
                >
                  {({ loading }) => (
                    <Button 
                      variant="outline"
                      className="w-full bg-blue-50 border-blue-200 hover:bg-blue-100 text-blue-700 font-medium"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Generating PDF...
                        </>
                      ) : (
                        <>
                          <FileDown className="w-4 h-4 mr-2" />
                          Download Visit Summary (PDF)
                        </>
                      )}
                    </Button>
                  )}
                </PDFDownloadLink>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 