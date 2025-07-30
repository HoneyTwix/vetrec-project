'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  getUserExtractions, 
  updateExtraction, 
  deleteExtraction,
  type UserExtraction,
  type UpdateExtractionRequest
} from '@/lib/api';
import { 
  FileText, 
  Loader2, 
  Edit, 
  Trash2, 
  Save, 
  X, 
  Eye,
  AlertCircle,
  CheckCircle,
  Plus,
  ArrowLeft
} from 'lucide-react';

export default function ReviewExtractionsPage() {
  const { user, isLoaded } = useUser();
  const router = useRouter();
  const [extractions, setExtractions] = useState<UserExtraction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingExtraction, setEditingExtraction] = useState<UserExtraction | null>(null);
  const [showTranscript, setShowTranscript] = useState<number | null>(null);

  

  useEffect(() => {
    if (isLoaded && !user) {
      router.push('/sign-in');
      return;
    }

    const loadExtractions = async () => {
        if (!user?.id) return;
        
        setIsLoading(true);
        setError(null);
        
        try {
          const userExtractions = await getUserExtractions(user.id);
          setExtractions(userExtractions);
          
          // Debug: Log the most recent extraction to inspect confidence level data
          if (userExtractions && userExtractions.length > 0) {
            const mostRecent = userExtractions[0]; // Assuming data is sorted by most recent first
            if (mostRecent) {
              console.log('🔍 Most recent extraction data:', {
                id: mostRecent.id,
                confidence_level: mostRecent.confidence_level,
                confidence_level_type: typeof mostRecent.confidence_level,
                full_extraction: mostRecent
              });
            }
          }
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to load extractions');
        } finally {
          setIsLoading(false);
        }
      };
    
    if (user) {
      void loadExtractions();
    }
  }, [user, isLoaded, router,]);

  const handleEdit = (extraction: UserExtraction) => {
    setEditingExtraction(extraction);
  };

  const handleCancelEdit = () => {
    setEditingExtraction(null);
  };

  const handleSave = async () => {
    if (!user?.id || !editingExtraction) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const updateData: UpdateExtractionRequest = {
        follow_up_tasks: editingExtraction.follow_up_tasks,
        medication_instructions: editingExtraction.medication_instructions,
        client_reminders: editingExtraction.client_reminders,
        clinician_todos: editingExtraction.clinician_todos,
        custom_extractions: editingExtraction.custom_extractions
      };
      
      const updatedExtraction = await updateExtraction(user.id, editingExtraction.id, updateData);
      
      setExtractions(extractions.map(ext => 
        ext.id === updatedExtraction.id ? updatedExtraction : ext
      ));
      setEditingExtraction(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update extraction');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (extractionId: number) => {
    if (!user?.id) return;
    
    if (!confirm('Are you sure you want to delete this extraction? This action cannot be undone.')) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      await deleteExtraction(user.id, extractionId);
      setExtractions(extractions.filter(ext => ext.id !== extractionId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete extraction');
    } finally {
      setIsLoading(false);
    }
  };

  const updateFollowUpTask = (index: number, field: string, value: string) => {
    if (!editingExtraction) return;
    
    const updatedTasks = [...editingExtraction.follow_up_tasks];
    const currentTask = updatedTasks[index];
    
    if (!currentTask) return;
    
    if (field === 'description') {
      updatedTasks[index] = { 
        description: value,
        priority: currentTask.priority,
        due_date: currentTask.due_date,
        assigned_to: currentTask.assigned_to
      };
    } else if (field === 'priority') {
      updatedTasks[index] = { 
        description: currentTask.description,
        priority: value as 'high' | 'medium' | 'low',
        due_date: currentTask.due_date,
        assigned_to: currentTask.assigned_to
      };
    } else if (field === 'due_date') {
      updatedTasks[index] = { 
        description: currentTask.description,
        priority: currentTask.priority,
        due_date: value ?? undefined,
        assigned_to: currentTask.assigned_to
      };
    } else if (field === 'assigned_to') {
      updatedTasks[index] = { 
        description: currentTask.description,
        priority: currentTask.priority,
        due_date: currentTask.due_date,
        assigned_to: value ?? undefined
      };
    }
    
    setEditingExtraction({
      ...editingExtraction,
      follow_up_tasks: updatedTasks
    });
  };

  const updateMedication = (index: number, field: string, value: string) => {
    if (!editingExtraction) return;
    
    const updatedMedications = [...editingExtraction.medication_instructions];
    const currentMed = updatedMedications[index];
    
    if (!currentMed) return;
    
    if (field === 'medication_name') {
      updatedMedications[index] = { 
        medication_name: value,
        dosage: currentMed.dosage,
        frequency: currentMed.frequency,
        duration: currentMed.duration,
        special_instructions: currentMed.special_instructions
      };
    } else if (field === 'dosage') {
      updatedMedications[index] = { 
        medication_name: currentMed.medication_name,
        dosage: value,
        frequency: currentMed.frequency,
        duration: currentMed.duration,
        special_instructions: currentMed.special_instructions
      };
    } else if (field === 'frequency') {
      updatedMedications[index] = { 
        medication_name: currentMed.medication_name,
        dosage: currentMed.dosage,
        frequency: value,
        duration: currentMed.duration,
        special_instructions: currentMed.special_instructions
      };
    } else if (field === 'duration') {
      updatedMedications[index] = { 
        medication_name: currentMed.medication_name,
        dosage: currentMed.dosage,
        frequency: currentMed.frequency,
        duration: value ?? undefined,
        special_instructions: currentMed.special_instructions
      };
    } else if (field === 'special_instructions') {
      updatedMedications[index] = { 
        medication_name: currentMed.medication_name,
        dosage: currentMed.dosage,
        frequency: currentMed.frequency,
        duration: currentMed.duration,
        special_instructions: value ?? undefined
      };
    }
    
    setEditingExtraction({
      ...editingExtraction,
      medication_instructions: updatedMedications
    });
  };

  const updateClientReminder = (index: number, field: string, value: string) => {
    if (!editingExtraction) return;
    
    const updatedReminders = [...editingExtraction.client_reminders];
    const currentReminder = updatedReminders[index];
    
    if (!currentReminder) return;
    
    if (field === 'description') {
      updatedReminders[index] = { 
        description: value,
        reminder_type: currentReminder.reminder_type,
        priority: currentReminder.priority,
        due_date: currentReminder.due_date
      };
    } else if (field === 'reminder_type') {
      updatedReminders[index] = { 
        description: currentReminder.description,
        reminder_type: value,
        priority: currentReminder.priority,
        due_date: currentReminder.due_date
      };
    } else if (field === 'priority') {
      updatedReminders[index] = { 
        description: currentReminder.description,
        reminder_type: currentReminder.reminder_type,
        priority: value as 'high' | 'medium' | 'low',
        due_date: currentReminder.due_date
      };
          } else if (field === 'due_date') {
        updatedReminders[index] = { 
          description: currentReminder.description,
          reminder_type: currentReminder.reminder_type,
          priority: currentReminder.priority,
          due_date: value ?? undefined
        };
    }
    
    setEditingExtraction({
      ...editingExtraction,
      client_reminders: updatedReminders
    });
  };

  const updateClinicianTodo = (index: number, field: string, value: string) => {
    if (!editingExtraction) return;
    
    const updatedTodos = [...editingExtraction.clinician_todos];
    const currentTodo = updatedTodos[index];
    
    if (!currentTodo) return;
    
    if (field === 'description') {
      updatedTodos[index] = { 
        description: value,
        task_type: currentTodo.task_type,
        priority: currentTodo.priority,
        due_date: currentTodo.due_date
      };
    } else if (field === 'task_type') {
      updatedTodos[index] = { 
        description: currentTodo.description,
        task_type: value,
        priority: currentTodo.priority,
        due_date: currentTodo.due_date
      };
    } else if (field === 'priority') {
      updatedTodos[index] = { 
        description: currentTodo.description,
        task_type: currentTodo.task_type,
        priority: value as 'high' | 'medium' | 'low',
        due_date: currentTodo.due_date
      };
          } else if (field === 'due_date') {
        updatedTodos[index] = { 
          description: currentTodo.description,
          task_type: currentTodo.task_type,
          priority: currentTodo.priority,
          due_date: value ?? undefined
        };
    }
    
    setEditingExtraction({
      ...editingExtraction,
      clinician_todos: updatedTodos
    });
  };

  const addFollowUpTask = () => {
    if (!editingExtraction) return;
    
    setEditingExtraction({
      ...editingExtraction,
      follow_up_tasks: [
        ...editingExtraction.follow_up_tasks,
        { description: '', priority: 'medium' as const, due_date: '', assigned_to: '' }
      ]
    });
  };

  const addMedication = () => {
    if (!editingExtraction) return;
    
    setEditingExtraction({
      ...editingExtraction,
      medication_instructions: [
        ...editingExtraction.medication_instructions,
        { medication_name: '', dosage: '', frequency: '', duration: '', special_instructions: '' }
      ]
    });
  };

  const addClientReminder = () => {
    if (!editingExtraction) return;
    
    setEditingExtraction({
      ...editingExtraction,
      client_reminders: [
        ...editingExtraction.client_reminders,
        { description: '', reminder_type: '', priority: 'medium' as const, due_date: '' }
      ]
    });
  };

  const addClinicianTodo = () => {
    if (!editingExtraction) return;
    
    setEditingExtraction({
      ...editingExtraction,
      clinician_todos: [
        ...editingExtraction.clinician_todos,
        { description: '', task_type: '', priority: 'medium' as const, due_date: '' }
      ]
    });
  };

  const removeItem = (category: 'follow_up_tasks' | 'medication_instructions' | 'client_reminders' | 'clinician_todos', index: number) => {
    if (!editingExtraction) return;
    
    const updatedItems = [...editingExtraction[category]];
    updatedItems.splice(index, 1);
    
    setEditingExtraction({
      ...editingExtraction,
      [category]: updatedItems
    });
  };

  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-red-600 bg-red-100';
      case 'reviewed': return 'text-blue-600 bg-blue-100';
      default: return 'text-slate-600 bg-slate-100';
    }
  };

  const getConfidenceIcon = (level: string) => {
    switch (level) {
      case 'high': return <CheckCircle className="w-4 h-4" />;
      case 'medium': return <AlertCircle className="w-4 h-4" />;
      case 'low': return <AlertCircle className="w-4 h-4" />;
      case 'reviewed': return <CheckCircle className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect to sign-in
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            onClick={() => router.push('/')}
            variant="ghost"
            className="mb-4 flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Extraction
          </Button>
          
          <div className="flex items-center gap-4 mb-6">
            <div className="bg-blue-600 p-3 rounded-full">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-slate-900">Review Extractions</h1>
              <p className="text-slate-600">View, edit, and manage your saved medical extractions</p>
            </div>
          </div>
        </div>

        {/* Extractions List */}
        <div className="space-y-6">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-slate-600">Loading extractions...</p>
            </div>
          ) : extractions.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-slate-800 mb-2">No Extractions Found</h3>
                                 <p className="text-slate-600 mb-4">
                   You haven&apos;t saved any extractions yet. Create your first extraction to see it here.
                 </p>
                <Button onClick={() => router.push('/')}>
                  Create Extraction
                </Button>
              </CardContent>
            </Card>
          ) : (
            extractions.map((extraction) => (
              <Card key={extraction.id} className="border-slate-200">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 text-xs rounded-full flex items-center gap-1 ${getConfidenceColor(extraction.confidence_level)}`}>
                          {getConfidenceIcon(extraction.confidence_level)}
                          {extraction.confidence_level}
                        </span>
                      </div>
                      <span className="text-sm text-slate-500">
                        {new Date(extraction.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        onClick={() => setShowTranscript(showTranscript === extraction.id ? null : extraction.id)}
                        variant="ghost"
                        size="sm"
                        className="text-blue-600 hover:text-blue-700"
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        {showTranscript === extraction.id ? 'Hide' : 'View'} Transcript
                      </Button>
                      
                      {editingExtraction?.id !== extraction.id && (
                        <>
                          <Button
                            onClick={() => handleEdit(extraction)}
                            variant="ghost"
                            size="sm"
                            className="text-green-600 hover:text-green-700"
                          >
                            <Edit className="w-4 h-4 mr-1" />
                            Edit
                          </Button>
                          <Button
                            onClick={() => handleDelete(extraction.id)}
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4 mr-1" />
                            Delete
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Transcript Preview */}
                  {showTranscript === extraction.id && (
                    <div className="bg-slate-50 p-4 rounded-lg">
                      <h4 className="font-medium text-slate-800 mb-2">Original Transcript</h4>
                      <div className="text-sm text-slate-600 max-h-32 overflow-y-auto">
                        {extraction.transcript.transcript_text}
                      </div>
                    </div>
                  )}

                  {/* Extraction Results */}
                  {editingExtraction?.id === extraction.id ? (
                    // Edit Mode
                    <div className="space-y-6">
                      {/* Follow-up Tasks */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <Label className="text-base font-medium">Follow-up Tasks</Label>
                          <Button onClick={addFollowUpTask} variant="outline" size="sm">
                            <Plus className="w-4 h-4 mr-1" />
                            Add Task
                          </Button>
                        </div>
                        <div className="space-y-3">
                          {editingExtraction.follow_up_tasks.map((task, index) => (
                            <div key={index} className="p-3 border rounded-lg space-y-2">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                <Input
                                  placeholder="Task description"
                                  value={task.description}
                                  onChange={(e) => updateFollowUpTask(index, 'description', e.target.value)}
                                />
                                <select
                                  value={task.priority}
                                  onChange={(e) => updateFollowUpTask(index, 'priority', e.target.value)}
                                  className="px-3 py-2 border border-slate-300 rounded-md"
                                >
                                  <option value="low">Low Priority</option>
                                  <option value="medium">Medium Priority</option>
                                  <option value="high">High Priority</option>
                                </select>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                <Input
                                  placeholder="Due date"
                                  value={task.due_date ?? ''}
                                  onChange={(e) => updateFollowUpTask(index, 'due_date', e.target.value)}
                                />
                                <Input
                                  placeholder="Assigned to"
                                  value={task.assigned_to ?? ''}
                                  onChange={(e) => updateFollowUpTask(index, 'assigned_to', e.target.value)}
                                />
                              </div>
                              <Button
                                onClick={() => removeItem('follow_up_tasks', index)}
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                              >
                                <X className="w-4 h-4 mr-1" />
                                Remove
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Medication Instructions */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <Label className="text-base font-medium">Medication Instructions</Label>
                          <Button onClick={addMedication} variant="outline" size="sm">
                            <Plus className="w-4 h-4 mr-1" />
                            Add Medication
                          </Button>
                        </div>
                        <div className="space-y-3">
                          {editingExtraction.medication_instructions.map((med, index) => (
                            <div key={index} className="p-3 border rounded-lg space-y-2">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                <Input
                                  placeholder="Medication name"
                                  value={med.medication_name}
                                  onChange={(e) => updateMedication(index, 'medication_name', e.target.value)}
                                />
                                <Input
                                  placeholder="Dosage"
                                  value={med.dosage}
                                  onChange={(e) => updateMedication(index, 'dosage', e.target.value)}
                                />
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                <Input
                                  placeholder="Frequency"
                                  value={med.frequency}
                                  onChange={(e) => updateMedication(index, 'frequency', e.target.value)}
                                />
                                <Input
                                  placeholder="Duration"
                                  value={med.duration ?? ''}
                                  onChange={(e) => updateMedication(index, 'duration', e.target.value)}
                                />
                              </div>
                              <Textarea
                                placeholder="Special instructions"
                                value={med.special_instructions ?? ''}
                                onChange={(e) => updateMedication(index, 'special_instructions', e.target.value)}
                                className="min-h-[60px]"
                              />
                              <Button
                                onClick={() => removeItem('medication_instructions', index)}
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                              >
                                <X className="w-4 h-4 mr-1" />
                                Remove
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Client Reminders */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <Label className="text-base font-medium">Client Reminders</Label>
                          <Button onClick={addClientReminder} variant="outline" size="sm">
                            <Plus className="w-4 h-4 mr-1" />
                            Add Reminder
                          </Button>
                        </div>
                        <div className="space-y-3">
                          {editingExtraction.client_reminders.map((reminder, index) => (
                            <div key={index} className="p-3 border rounded-lg space-y-2">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                <Input
                                  placeholder="Reminder description"
                                  value={reminder.description}
                                  onChange={(e) => updateClientReminder(index, 'description', e.target.value)}
                                />
                                <Input
                                  placeholder="Reminder type"
                                  value={reminder.reminder_type}
                                  onChange={(e) => updateClientReminder(index, 'reminder_type', e.target.value)}
                                />
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                <select
                                  value={reminder.priority ?? 'medium'}
                                  onChange={(e) => updateClientReminder(index, 'priority', e.target.value)}
                                  className="px-3 py-2 border border-slate-300 rounded-md"
                                >
                                  <option value="low">Low Priority</option>
                                  <option value="medium">Medium Priority</option>
                                  <option value="high">High Priority</option>
                                </select>
                                <Input
                                  placeholder="Due date"
                                  value={reminder.due_date ?? ''}
                                  onChange={(e) => updateClientReminder(index, 'due_date', e.target.value)}
                                />
                              </div>
                              <Button
                                onClick={() => removeItem('client_reminders', index)}
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                              >
                                <X className="w-4 h-4 mr-1" />
                                Remove
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Clinician Todos */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <Label className="text-base font-medium">Clinician Tasks</Label>
                          <Button onClick={addClinicianTodo} variant="outline" size="sm">
                            <Plus className="w-4 h-4 mr-1" />
                            Add Task
                          </Button>
                        </div>
                        <div className="space-y-3">
                          {editingExtraction.clinician_todos.map((todo, index) => (
                            <div key={index} className="p-3 border rounded-lg space-y-2">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                <Input
                                  placeholder="Task description"
                                  value={todo.description}
                                  onChange={(e) => updateClinicianTodo(index, 'description', e.target.value)}
                                />
                                <Input
                                  placeholder="Task type"
                                  value={todo.task_type}
                                  onChange={(e) => updateClinicianTodo(index, 'task_type', e.target.value)}
                                />
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                <select
                                  value={todo.priority ?? 'medium'}
                                  onChange={(e) => updateClinicianTodo(index, 'priority', e.target.value)}
                                  className="px-3 py-2 border border-slate-300 rounded-md"
                                >
                                  <option value="low">Low Priority</option>
                                  <option value="medium">Medium Priority</option>
                                  <option value="high">High Priority</option>
                                </select>
                                <Input
                                  placeholder="Due date"
                                  value={todo.due_date ?? ''}
                                  onChange={(e) => updateClinicianTodo(index, 'due_date', e.target.value)}
                                />
                              </div>
                              <Button
                                onClick={() => removeItem('clinician_todos', index)}
                                variant="ghost"
                                size="sm"
                                className="text-red-600 hover:text-red-700"
                              >
                                <X className="w-4 h-4 mr-1" />
                                Remove
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-2 pt-4">
                        <Button onClick={handleSave} disabled={isLoading} className="flex-1">
                          {isLoading ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <Save className="w-4 h-4 mr-2" />
                              Save Changes
                            </>
                          )}
                        </Button>
                        <Button onClick={handleCancelEdit} variant="outline">
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    // View Mode
                    <div className="space-y-4">
                      {/* Follow-up Tasks */}
                      {extraction.follow_up_tasks.length > 0 && (
                        <div>
                          <Label className="text-base font-medium">Follow-up Tasks</Label>
                          <div className="space-y-2 mt-2">
                            {extraction.follow_up_tasks.map((task, index) => (
                              <div key={index} className="p-3 bg-slate-50 rounded-lg">
                                <div className="flex items-center justify-between">
                                  <span className="font-medium">{task.description}</span>
                                  <span className={`px-2 py-1 text-xs rounded ${task.priority === 'high' ? 'bg-red-100 text-red-800' : task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                                    {task.priority} priority
                                  </span>
                                </div>
                                {(task.due_date ?? task.assigned_to) && (
                                  <div className="text-sm text-slate-600 mt-1">
                                    {task.due_date && <span>Due: {task.due_date}</span>}
                                    {task.due_date && task.assigned_to && <span> • </span>}
                                    {task.assigned_to && <span>Assigned to: {task.assigned_to}</span>}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Medication Instructions */}
                      {extraction.medication_instructions.length > 0 && (
                        <div>
                          <Label className="text-base font-medium">Medication Instructions</Label>
                          <div className="space-y-2 mt-2">
                            {extraction.medication_instructions.map((med, index) => (
                              <div key={index} className="p-3 bg-slate-50 rounded-lg">
                                <div className="font-medium">{med.medication_name}</div>
                                <div className="text-sm text-slate-600">
                                  {med.dosage} • {med.frequency}
                                  {med.duration && ` • Duration: ${med.duration}`}
                                </div>
                                {med.special_instructions && (
                                  <div className="text-sm text-slate-600 mt-1">
                                    <span className="font-medium">Special instructions:</span> {med.special_instructions}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Client Reminders */}
                      {extraction.client_reminders.length > 0 && (
                        <div>
                          <Label className="text-base font-medium">Client Reminders</Label>
                          <div className="space-y-2 mt-2">
                            {extraction.client_reminders.map((reminder, index) => (
                              <div key={index} className="p-3 bg-slate-50 rounded-lg">
                                <div className="flex items-center justify-between">
                                  <span className="font-medium">{reminder.description}</span>
                                  <span className="text-sm text-slate-600">{reminder.reminder_type}</span>
                                </div>
                                {(reminder.priority ?? reminder.due_date) && (
                                  <div className="text-sm text-slate-600 mt-1">
                                    {reminder.priority && <span className={`px-2 py-1 text-xs rounded mr-2 ${reminder.priority === 'high' ? 'bg-red-100 text-red-800' : reminder.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                                      {reminder.priority} priority
                                    </span>}
                                    {reminder.due_date && <span>Due: {reminder.due_date}</span>}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Clinician Todos */}
                      {extraction.clinician_todos.length > 0 && (
                        <div>
                          <Label className="text-base font-medium">Clinician Tasks</Label>
                          <div className="space-y-2 mt-2">
                            {extraction.clinician_todos.map((todo, index) => (
                              <div key={index} className="p-3 bg-slate-50 rounded-lg">
                                <div className="flex items-center justify-between">
                                  <span className="font-medium">{todo.description}</span>
                                  <span className="text-sm text-slate-600">{todo.task_type}</span>
                                </div>
                                {(todo.priority ?? todo.due_date) && (
                                  <div className="text-sm text-slate-600 mt-1">
                                    {todo.priority && <span className={`px-2 py-1 text-xs rounded mr-2 ${todo.priority === 'high' ? 'bg-red-100 text-red-800' : todo.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                                      {todo.priority} priority
                                    </span>}
                                    {todo.due_date && <span>Due: {todo.due_date}</span>}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Custom Extractions */}
                      {extraction.custom_extractions && Object.keys(extraction.custom_extractions).length > 0 && (
                        <div>
                          <Label className="text-base font-medium">Custom Extractions</Label>
                          <div className="space-y-2 mt-2">
                            {Object.entries(extraction.custom_extractions).map(([category, data]) => (
                              <div key={category} className="p-3 bg-slate-50 rounded-lg">
                                <div className="font-medium text-blue-600">{category}</div>
                                <div className="text-sm text-slate-600 mt-1">{data.extracted_data}</div>
                                {data.reasoning && (
                                  <div className="text-xs text-slate-500 mt-1">
                                    <span className="font-medium">Reasoning:</span> {data.reasoning}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Error Display */}
        {error && (
          <Card className="border-red-200 bg-red-50 mt-6">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5" />
                <span className="font-medium">Error: {error}</span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
