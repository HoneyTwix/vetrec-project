'use client';

import TranscriptExtractor from '@/components/TranscriptExtractor';

export default function ExtractPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            VetRec Medical Action Extraction
          </h1>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Extract actionable items, medication instructions, and follow-up tasks from medical visit transcripts using AI
          </p>
        </div>

        {/* Transcript Extractor */}
        <TranscriptExtractor />
      </div>
    </div>
  );
}
