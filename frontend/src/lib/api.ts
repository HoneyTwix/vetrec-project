import axios from 'axios';

// API Types
export interface TranscriptRequest {
  transcript_text: string;
  notes?: string;
  user_id?: string | number;
}

export interface CustomCategory {
  name: string;
  description: string;
  field_type: 'structured' | 'text';
  required_fields: string[];
  optional_fields?: string[];
}

export interface UserInfo {
  id?: string;
  email?: string;
  name?: string;
}

export interface ExtractRequest {
  transcript_text: string;
  notes?: string;
  user_id?: string | number;
  user_info?: UserInfo;
  custom_categories?: CustomCategory[];
  sop_ids?: number[];  // IDs of SOPs to include in context
}

// SOP Types
export interface SOP {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  content: string;
  category?: string;
  tags?: string[];
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface SOPCreate {
  title: string;
  description?: string;
  content: string;
  category?: string;
  tags?: string[];
  is_active?: boolean;
  priority?: number;
}

export interface SOPUpdate {
  title?: string;
  description?: string;
  content?: string;
  category?: string;
  tags?: string[];
  is_active?: boolean;
  priority?: number;
}

export interface FlaggedResponseRequest {
  transcript_id: number;
  extraction_data: Record<string, unknown>;
  review_notes?: string;
  reviewed_by?: string;
}

export interface FlaggedResponseResponse {
  message: string;
  extraction_id: number;
  confidence_level: string;
  flagged: boolean;
}

export interface FollowUpTask {
  description: string;
  priority: 'high' | 'medium' | 'low';
  due_date?: string;
}

export interface MedicationInstruction {
  medication_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  special_instructions?: string;
}

export interface ClientReminder {
  description: string;
  reminder_type: string;
  priority: 'high' | 'medium' | 'low';
}

export interface ClinicianTodo {
  description: string;
  task_type: string;
  priority: 'high' | 'medium' | 'low';
}

export interface ExtractionResult {
  follow_up_tasks: FollowUpTask[];
  medication_instructions: MedicationInstruction[];
  client_reminders: ClientReminder[];
  clinician_todos: ClinicianTodo[];
  custom_extractions?: Record<string, unknown>[];
}

export interface ExtractionResponse {
  transcript?: {
    id: number;
    user_id?: number;
    transcript_text: string;
    notes?: string;
    created_at: string;
  };
  extraction: ExtractionResult;
  processing_time?: number;
  flagged?: boolean;
  confidence_level?: string;
  review_required?: boolean;
  message?: string;
}

// API Functions
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function extractMedicalActions(request: TranscriptRequest): Promise<ExtractionResponse> {
  try {
    const response = await axios.post(`${API_BASE_URL}/extract`, request, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data as ExtractionResponse;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred during extraction');
  }
}

export async function extractWithCustomCategories(request: ExtractRequest): Promise<ExtractionResponse> {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/v1/extract`, request, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data as ExtractionResponse;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      console.error('🔍 Full error response:', error.response?.data);
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred during extraction');
  }
}

export async function saveFlaggedResponse(request: FlaggedResponseRequest): Promise<FlaggedResponseResponse> {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/v1/save-flagged-response`, request, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data as FlaggedResponseResponse;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred while saving flagged response');
  }
}

// SOP API Functions
export async function createSOP(userId: string, sopData: SOPCreate): Promise<SOP> {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/v1/sops`, sopData, {
      params: { user_id: userId },
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data as SOP;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred while creating SOP');
  }
}

export async function getUserSOPs(
  userId: string, 
  activeOnly = true,
  category?: string,
  search?: string
): Promise<SOP[]> {
  try {
    const params: Record<string, string | boolean> = { active_only: activeOnly };
    if (category) params.category = category;
    if (search) params.search = search;
    
    const response = await axios.get(`${API_BASE_URL}/api/v1/sops/${userId}`, {
      params,
    });
    return response.data as SOP[];
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred while fetching SOPs');
  }
}

export async function getSOP(userId: string, sopId: number): Promise<SOP> {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/sops/${userId}/${sopId}`);
    return response.data as SOP;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred while fetching SOP');
  }
}

export async function updateSOP(userId: string, sopId: number, sopData: SOPUpdate): Promise<SOP> {
  try {
    const response = await axios.put(`${API_BASE_URL}/api/v1/sops/${userId}/${sopId}`, sopData, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data as SOP;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred while updating SOP');
  }
}

export async function deleteSOP(userId: string, sopId: number): Promise<{ message: string }> {
  try {
    const response = await axios.delete(`${API_BASE_URL}/api/v1/sops/${userId}/${sopId}`);
    return response.data as { message: string };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred while deleting SOP');
  }
}

export async function uploadSOPFile(
  userId: string,
  file: File,
  title?: string,
  description?: string,
  category?: string,
  tags?: string,
  priority = 1
): Promise<{ message: string; sop: SOP }> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (description) formData.append('description', description);
    if (category) formData.append('category', category);
    if (tags) formData.append('tags', tags);
    formData.append('priority', priority.toString());
    
    const response = await axios.post(`${API_BASE_URL}/api/v1/sops/${userId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data as { message: string; sop: SOP };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred while uploading SOP file');
  }
}

export async function getSOPCategories(userId: string): Promise<{ categories: string[] }> {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/sops/${userId}/categories`);
    return response.data as { categories: string[] };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred while fetching SOP categories');
  }
}

export async function bulkUploadSOPs(
  userId: string,
  files: File[],
  descriptions: Record<string, string>,  // Required: Map of filename to custom description
  category?: string,
  tags?: string
): Promise<{ message: string; uploaded_sops: SOP[]; errors: string[] }> {
  try {
    const formData = new FormData();
    
    // Add files
    files.forEach(file => {
      formData.append('files', file);
    });
    
    // Add required descriptions
    formData.append('descriptions', JSON.stringify(descriptions));
    
    // Add optional parameters
    if (category) {
      formData.append('category', category);
    }
    if (tags) {
      formData.append('tags', tags);
    }
    
    const response = await axios.post(`${API_BASE_URL}/api/v1/sops/${userId}/bulk-upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data as { message: string; uploaded_sops: SOP[]; errors: string[] };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred during bulk upload');
  }
}

export interface PDFAnalysis {
  filename: string;
  file_size_mb: number;
  pages: number;
  is_encrypted: boolean;
  text_extractable: boolean;
  extraction_success: boolean;
  preview_text?: string;
  recommendations: string[];
}

export async function analyzePDFFile(
  userId: string,
  file: File
): Promise<PDFAnalysis> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_BASE_URL}/api/v1/sops/${userId}/analyze-pdf`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data as PDFAnalysis;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred during PDF analysis');
  }
}

export interface TranscriptPDFResponse {
  success: boolean;
  extracted_text?: string;
  error?: string;
  filename?: string;
  file_size?: number;
  message?: string;
}

export async function uploadTranscriptPDF(
  file: File
): Promise<TranscriptPDFResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_BASE_URL}/api/v1/transcript/upload-pdf`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data as TranscriptPDFResponse;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorData = error.response?.data as { detail?: string } | undefined;
      const errorMessage = errorData?.detail;
      throw new Error(errorMessage ?? error.message);
    }
    throw new Error('An error occurred during transcript PDF upload');
  }
} 