import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface TranscriptRequest {
  transcript_text: string;
  notes?: string;
  user_id?: number;
}

export interface FollowUpTask {
  description: string;
  priority: 'high' | 'medium' | 'low';
  due_date?: string;
  assigned_to?: 'client' | 'clinician' | 'both';
}

export interface MedicationInstruction {
  medication_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  special_instructions?: string;
}

export interface ClientReminder {
  reminder_type: 'appointment' | 'medication' | 'test' | 'lifestyle' | 'other';
  description: string;
  due_date?: string;
  priority: 'high' | 'medium' | 'low';
}

export interface ClinicianTodo {
  task_type: 'follow_up' | 'referral' | 'test_order' | 'documentation' | 'billing' | 'other';
  description: string;
  priority: 'high' | 'medium' | 'low';
  assigned_to?: string;
  due_date?: string;
}

export interface ExtractionResult {
  id: number;
  transcript_id: number;
  follow_up_tasks: FollowUpTask[];
  medication_instructions: MedicationInstruction[];
  client_reminders: ClientReminder[];
  clinician_todos: ClinicianTodo[];
  created_at: string;
}

export interface VisitTranscript {
  id: number;
  user_id?: number;
  transcript_text: string;
  notes?: string;
  created_at: string;
}

export interface ExtractionResponse {
  transcript: VisitTranscript;
  extraction: ExtractionResult;
}

export interface MemoryResponse {
  previous_visits: ExtractionResponse[];
}

// API Functions
export const extractMedicalActions = async (request: TranscriptRequest): Promise<ExtractionResponse> => {
  const response = await api.post<ExtractionResponse>('/extract', request);
  return response.data;
};

export const getUserMemory = async (userId: number, limit: number = 5): Promise<MemoryResponse> => {
  const response = await api.get<MemoryResponse>(`/memory/${userId}?limit=${limit}`);
  return response.data;
};

export const getExtractionResult = async (extractionId: number): Promise<ExtractionResult> => {
  const response = await api.get<ExtractionResult>(`/extraction/${extractionId}`);
  return response.data;
};

// Health check
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    return response.status === 200;
  } catch (error) {
    return false;
  }
};
