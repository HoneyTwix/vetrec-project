'use client';

import { useState, useEffect, useCallback } from 'react';
import { useUser } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  createSOP, 
  getUserSOPs, 
  updateSOP, 
  deleteSOP, 
  getSOPCategories,
  bulkUploadSOPs,
  analyzePDFFile,
  type SOP, 
  type SOPCreate,
  type PDFAnalysis,
} from '@/lib/api';
import { 
  FileText, 
  Upload, 
  Plus, 
  Edit, 
  Trash2, 
  Search, 
  CheckCircle, 
  X,
  Settings,
  FolderOpen,
  FileUp
} from 'lucide-react';

interface SOPManagerProps {
  selectedSOPs: number[];
  onSOPSelectionChange: (sopIds: number[]) => void;
}

export default function SOPManager({ selectedSOPs, onSOPSelectionChange }: SOPManagerProps) {
  // Note: All buttons in this component have type="button" to prevent form submission
  // when this component is used inside a form (like in TranscriptExtractor)
  const { user } = useUser();
  const [sops, setSOPs] = useState<SOP[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [editingSOP, setEditingSOP] = useState<SOP | null>(null);
  const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
  const [pdfAnalysis, setPdfAnalysis] = useState<PDFAnalysis | null>(null);
  const [analyzingPdf, setAnalyzingPdf] = useState(false);

  // Form states
  const [sopForm, setSOPForm] = useState<SOPCreate>({
    title: '',
    description: '',
    content: '',
    category: '',
    tags: [],
    is_active: true,
    priority: 1
  });

  const [uploadForm, setUploadForm] = useState({
    title: '',
    description: '',
    category: '',
    tags: '',
    priority: 1
  });
  
  // Add state for custom descriptions for each file
  const [fileDescriptions, setFileDescriptions] = useState<Record<string, string>>({});

  const loadSOPs = useCallback(async () => {
    if (!user?.id) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const userSOPs = await getUserSOPs(user.id, true, selectedCategory || undefined, searchTerm || undefined);
      setSOPs(userSOPs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load SOPs');
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, selectedCategory, searchTerm]);

  const loadCategories = useCallback(async () => {
    if (!user?.id) return;
    
    try {
      console.log('Loading categories for user:', user.id);
      const response = await getSOPCategories(user.id);
      console.log('Categories response:', response);
      setCategories(response.categories);
    } catch (err) {
      console.error('Failed to load categories:', err);
      setError(err instanceof Error ? err.message : 'Failed to load categories');
    }
  }, [user?.id]);

  useEffect(() => {
    if (user?.id) {
      void loadSOPs();
      void loadCategories();
    }
  }, [loadSOPs, loadCategories, user?.id]);

  const handleCreateSOP = async () => {
    if (!user?.id) return;
    
    // Validate that description is provided
    if (!sopForm.description?.trim()) {
      setError('Description is required for SOP creation');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const newSOP = await createSOP(user.id, {
        title: sopForm.title,
        description: sopForm.description,
        content: sopForm.content,
        category: sopForm.category,
        tags: sopForm.tags,
        is_active: sopForm.is_active,
        priority: sopForm.priority
      });
      
      setSOPs([...sops, newSOP]);
      setShowCreateForm(false);
      setSOPForm({
        title: '',
        description: '',
        content: '',
        category: '',
        tags: [],
        is_active: true,
        priority: 1
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create SOP');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateSOP = async () => {
    if (!user?.id || !editingSOP) return;
    
    // Validate that description is provided
    if (!sopForm.description?.trim()) {
      setError('Description is required for SOP updates');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const updatedSOP = await updateSOP(user.id, editingSOP.id, {
        title: sopForm.title,
        description: sopForm.description,
        content: sopForm.content,
        category: sopForm.category,
        tags: sopForm.tags,
        is_active: sopForm.is_active,
        priority: sopForm.priority
      });
      
      setSOPs(sops.map(sop => sop.id === updatedSOP.id ? updatedSOP : sop));
      setEditingSOP(null);
      setSOPForm({
        title: '',
        description: '',
        content: '',
        category: '',
        tags: [],
        is_active: true,
        priority: 1
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update SOP');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSOP = async (sopId: number) => {
    if (!user?.id) return;
    
    if (!confirm('Are you sure you want to delete this SOP?')) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      await deleteSOP(user.id, sopId);
      setSOPs(sops.filter(sop => sop.id !== sopId));
      // Remove from selected SOPs if it was selected
      onSOPSelectionChange(selectedSOPs.filter(id => id !== sopId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete SOP');
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to check if all files have descriptions
  const allFilesHaveDescriptions = () => {
    return uploadingFiles.every(file => {
      const description = fileDescriptions[file.name];
      return Boolean(description?.trim());
    });
  };

  const handleFileUpload = async () => {
    if (!user?.id || uploadingFiles.length === 0) return;
    
    // Validate that all files have descriptions
    if (!allFilesHaveDescriptions()) {
      setError('All files must have descriptions before uploading');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // All descriptions are mandatory, so send all of them
      const descriptionsToSend: Record<string, string> = {};
      uploadingFiles.forEach(file => {
        const description = fileDescriptions[file.name];
        if (description?.trim()) {
          descriptionsToSend[file.name] = description.trim();
        }
      });
      
      const result = await bulkUploadSOPs(
        user.id,
        uploadingFiles,
        descriptionsToSend,
        uploadForm.category || undefined,
        uploadForm.tags || undefined
      );
      
      setSOPs([...sops, ...result.uploaded_sops]);
      setShowUploadForm(false);
      setUploadingFiles([]);
      setFileDescriptions({}); // Clear descriptions
      setUploadForm({
        title: '',
        description: '',
        category: '',
        tags: '',
        priority: 1
      });
      
      if (result.errors.length > 0) {
        setError(`Upload completed with errors: ${result.errors.join(', ')}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload files');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSOPSelection = (sopId: number, checked: boolean) => {
    if (checked) {
      onSOPSelectionChange([...selectedSOPs, sopId]);
    } else {
      onSOPSelectionChange(selectedSOPs.filter(id => id !== sopId));
    }
  };

  const startEditing = (sop: SOP) => {
    setEditingSOP(sop);
    setSOPForm({
      title: sop.title,
      description: sop.description ?? '',
      content: sop.content,
      category: sop.category ?? '',
      tags: sop.tags ?? [],
      is_active: sop.is_active,
      priority: sop.priority
    });
  };

  const cancelEditing = () => {
    setEditingSOP(null);
    setSOPForm({
      title: '',
      description: '',
      content: '',
      category: '',
      tags: [],
      is_active: true,
      priority: 1
    });
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    setUploadingFiles(files);
    setPdfAnalysis(null); // Clear previous analysis
    
    // Initialize descriptions for new files
    const newDescriptions: Record<string, string> = {};
    files.forEach(file => {
      if (!fileDescriptions[file.name]) {
        newDescriptions[file.name] = '';
      }
    });
    setFileDescriptions(prev => ({ ...prev, ...newDescriptions }));
  };

  const handleAnalyzePDF = async (file: File) => {
    if (!user?.id) return;
    
    setAnalyzingPdf(true);
    setError(null);
    
    try {
      const analysis = await analyzePDFFile(user.id, file);
      setPdfAnalysis(analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze PDF');
    } finally {
      setAnalyzingPdf(false);
    }
  };

  const filteredSOPs = sops.filter(sop => {
    const matchesSearch = !searchTerm || 
      sop.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (sop.description?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false) ||
      sop.content.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = !selectedCategory || sop.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            Standard Operating Procedures (SOPs)
          </CardTitle>
          <CardDescription>
            Upload and manage clinic policies and procedures to improve extraction accuracy
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search and Filter */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Label htmlFor="search">Search SOPs</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <Input
                  id="search"
                  placeholder="Search by title, description, or content..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="w-full md:w-48">
              <Label htmlFor="category">Category</Label>
              <select
                id="category"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Categories</option>
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              onClick={() => setShowCreateForm(true)}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create SOP
            </Button>
            <Button
              type="button"
              onClick={() => setShowUploadForm(true)}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Upload Files
            </Button>
            <Button
              type="button"
              onClick={loadSOPs}
              variant="outline"
              className="flex items-center gap-2"
            >
              <FolderOpen className="w-4 h-4" />
              Refresh
            </Button>
          </div>

          {/* SOP List */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Available SOPs</Label>
            {isLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-slate-600">Loading SOPs...</p>
              </div>
            ) : filteredSOPs.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <FileText className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p>No SOPs found. Create or upload your first SOP to get started.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredSOPs.map(sop => (
                  <Card key={sop.id} className="border-slate-200">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <input
                              type="checkbox"
                              checked={selectedSOPs.includes(sop.id)}
                              onChange={(e) => handleSOPSelection(sop.id, e.target.checked)}
                              className="rounded border-slate-300"
                            />
                            <h4 className="font-semibold text-slate-800">{sop.title}</h4>
                            {sop.category && (
                              <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                                {sop.category}
                              </span>
                            )}
                            {!sop.is_active && (
                              <span className="px-2 py-1 text-xs bg-slate-100 text-slate-600 rounded">
                                Inactive
                              </span>
                            )}
                          </div>
                          {sop.description && (
                            <p className="text-sm text-slate-600 mb-2">{sop.description}</p>
                          )}
                          {sop.tags && sop.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-2">
                              {sop.tags.map((tag, index) => (
                                <span
                                  key={index}
                                  className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                          <p className="text-xs text-slate-500">
                            Priority: {sop.priority} | Created: {new Date(sop.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            type="button"
                            onClick={() => startEditing(sop)}
                            variant="ghost"
                            size="sm"
                            className="text-blue-600 hover:text-blue-700"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            type="button"
                            onClick={() => handleDeleteSOP(sop.id)}
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Selected SOPs Summary */}
          {selectedSOPs.length > 0 && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-800 mb-2">
                Selected SOPs ({selectedSOPs.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {selectedSOPs.map(sopId => {
                  const sop = sops.find(s => s.id === sopId);
                  return sop ? (
                    <span
                      key={sopId}
                      className="px-2 py-1 text-sm bg-blue-100 text-blue-800 rounded flex items-center gap-1"
                    >
                      {sop.title}
                      <button
                        onClick={() => handleSOPSelection(sopId, false)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ) : null;
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit SOP Form */}
      {(showCreateForm || editingSOP) && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              {editingSOP ? 'Edit SOP' : 'Create New SOP'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="sop-title">Title *</Label>
                <Input
                  id="sop-title"
                  value={sopForm.title}
                  onChange={(e) => setSOPForm({...sopForm, title: e.target.value})}
                  placeholder="e.g., Medication Prescription Protocol"
                />
              </div>
              <div>
                <Label htmlFor="sop-category">Category</Label>
                <Input
                  id="sop-category"
                  value={sopForm.category}
                  onChange={(e) => setSOPForm({...sopForm, category: e.target.value})}
                  placeholder="e.g., medication, referral, documentation"
                  className="w-full"
                />
                {categories.length > 0 && (
                  <div className="mt-1">
                    <Label className="text-xs text-slate-600">Existing categories:</Label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {categories.map(category => (
                        <button
                          key={category}
                          type="button"
                          onClick={() => setSOPForm({...sopForm, category})}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                        >
                          {category}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="sop-description">Description *</Label>
              <Textarea
                id="sop-description"
                value={sopForm.description}
                onChange={(e) => setSOPForm({...sopForm, description: e.target.value})}
                placeholder="Brief description of this SOP..."
                className="min-h-[80px]"
                required
              />
            </div>

            <div>
              <Label htmlFor="sop-content">Content *</Label>
              <Textarea
                id="sop-content"
                value={sopForm.content}
                onChange={(e) => setSOPForm({...sopForm, content: e.target.value})}
                placeholder="Enter the full SOP content, procedures, and guidelines..."
                className="min-h-[200px]"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="sop-priority">Priority</Label>
                <select
                  id="sop-priority"
                  value={sopForm.priority}
                  onChange={(e) => setSOPForm({...sopForm, priority: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md"
                >
                  <option value={1}>Low</option>
                  <option value={2}>Medium</option>
                  <option value={3}>High</option>
                </select>
              </div>
              <div>
                <Label htmlFor="sop-tags">Tags (comma-separated)</Label>
                <Input
                  id="sop-tags"
                  value={sopForm.tags?.join(', ') ?? ''}
                  onChange={(e) => setSOPForm({...sopForm, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)})}
                  placeholder="medication, prescription, protocol"
                />
              </div>
              <div className="flex items-center">
                <input
                  id="sop-active"
                  type="checkbox"
                  checked={sopForm.is_active}
                  onChange={(e) => setSOPForm({...sopForm, is_active: e.target.checked})}
                  className="rounded border-slate-300 mr-2"
                />
                <Label htmlFor="sop-active">Active</Label>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                onClick={editingSOP ? handleUpdateSOP : handleCreateSOP}
                disabled={isLoading || !sopForm.title || !sopForm.content || !sopForm.description?.trim()}
                className="flex-1"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    {editingSOP ? 'Updating...' : 'Creating...'}
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    {editingSOP ? 'Update SOP' : 'Create SOP'}
                  </>
                )}
              </Button>
              <Button
                type="button"
                onClick={editingSOP ? cancelEditing : () => setShowCreateForm(false)}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* File Upload Form */}
      {showUploadForm && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileUp className="w-5 h-5" />
              Upload SOP Files
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="file-upload">Select Files</Label>
              <Input
                id="file-upload"
                type="file"
                multiple
                accept=".txt,.md,.json,.pdf"
                onChange={handleFileSelect}
                className="cursor-pointer"
              />
              <p className="text-sm text-slate-600 mt-1">
                Supported formats: TXT, MD, JSON, PDF. PDF files will be automatically converted to text for processing.
              </p>
            </div>

            {uploadingFiles.length > 0 && (
              <div>
                <Label>Selected Files ({uploadingFiles.length})</Label>
                <div className="space-y-3 mt-2">
                  {uploadingFiles.map((file, index) => (
                    <div key={index} className="p-3 bg-white rounded border">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{file.name}</span>
                          {file.name.toLowerCase().endsWith('.pdf') && (
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => handleAnalyzePDF(file)}
                              disabled={analyzingPdf}
                              className="text-blue-600 hover:text-blue-700"
                            >
                              {analyzingPdf ? (
                                <>
                                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 mr-1"></div>
                                  Analyzing...
                                </>
                              ) : (
                                'Analyze PDF'
                              )}
                            </Button>
                          )}
                        </div>
                        <span className="text-xs text-slate-500">
                          {(file.size / 1024).toFixed(1)} KB
                        </span>
                      </div>
                      
                      {/* Description input for this file */}
                      <div>
                        <Label htmlFor={`description-${index}`} className="text-xs text-slate-600">
                          Description *
                        </Label>
                        <Textarea
                          id={`description-${index}`}
                          value={fileDescriptions[file.name] ?? ''}
                          onChange={(e) => setFileDescriptions(prev => ({
                            ...prev,
                            [file.name]: e.target.value
                          }))}
                          placeholder={`Enter description for ${file.name}...`}
                          className="mt-1 text-sm min-h-[60px]"
                          required
                        />
                        <p className="text-xs text-slate-500 mt-1">
                          Description is required for all uploaded files
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* PDF Analysis Results */}
            {pdfAnalysis && (
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-800 mb-3">PDF Analysis Results</h4>
                <div className="space-y-2 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="font-medium">File:</span> {pdfAnalysis.filename}
                    </div>
                    <div>
                      <span className="font-medium">Size:</span> {pdfAnalysis.file_size_mb} MB
                    </div>
                    <div>
                      <span className="font-medium">Pages:</span> {pdfAnalysis.pages}
                    </div>
                    <div>
                      <span className="font-medium">Encrypted:</span> {pdfAnalysis.is_encrypted ? 'Yes' : 'No'}
                    </div>
                    <div>
                      <span className="font-medium">Text Extractable:</span> {pdfAnalysis.text_extractable ? 'Yes' : 'No'}
                    </div>
                    <div>
                      <span className="font-medium">Extraction Success:</span> {pdfAnalysis.extraction_success ? 'Yes' : 'No'}
                    </div>
                  </div>
                  
                  {pdfAnalysis.preview_text && (
                    <div>
                      <span className="font-medium">Preview:</span>
                      <div className="mt-1 p-2 bg-white rounded text-xs max-h-20 overflow-y-auto">
                        {pdfAnalysis.preview_text}
                      </div>
                    </div>
                  )}
                  
                  {pdfAnalysis.recommendations.length > 0 && (
                    <div>
                      <span className="font-medium">Recommendations:</span>
                      <ul className="mt-1 list-disc list-inside text-xs">
                        {pdfAnalysis.recommendations.map((rec, index) => (
                          <li key={index} className="text-blue-700">{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="upload-category">Category (applied to all files)</Label>
                <Input
                  id="upload-category"
                  value={uploadForm.category}
                  onChange={(e) => setUploadForm({...uploadForm, category: e.target.value})}
                  placeholder="e.g., medication, referral, documentation"
                  className="w-full"
                />
                {categories.length > 0 && (
                  <div className="mt-1">
                    <Label className="text-xs text-slate-600">Existing categories:</Label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {categories.map(category => (
                        <button
                          key={category}
                          type="button"
                          onClick={() => setUploadForm({...uploadForm, category})}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                        >
                          {category}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div>
                <Label htmlFor="upload-tags">Tags (comma-separated, applied to all files)</Label>
                <Input
                  id="upload-tags"
                  value={uploadForm.tags}
                  onChange={(e) => setUploadForm({...uploadForm, tags: e.target.value})}
                  placeholder="protocol, guideline, policy"
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                onClick={handleFileUpload}
                disabled={isLoading || uploadingFiles.length === 0 || !allFilesHaveDescriptions()}
                className="flex-1"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Files
                  </>
                )}
              </Button>
              <Button
                type="button"
                onClick={() => {
                  setShowUploadForm(false);
                  setUploadingFiles([]);
                  setFileDescriptions({}); // Clear descriptions
                  setUploadForm({
                    title: '',
                    description: '',
                    category: '',
                    tags: '',
                    priority: 1
                  });
                }}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-700">
              <X className="w-5 h-5" />
              <span className="font-medium">Error: {error}</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 