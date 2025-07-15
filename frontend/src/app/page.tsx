'use client';

import { useUser } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Shield, 
  FileText, 
  ArrowRight,
  User,
  Lock
} from 'lucide-react';
import TranscriptExtractor from '@/components/TranscriptExtractor';

export default function HomePage() {
  const { isLoaded, isSignedIn } = useUser();
  const router = useRouter();

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

  if (isSignedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-12 text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="bg-blue-600 p-3 rounded-full mr-4">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-5xl font-bold text-slate-900">
                VetRec
              </h1>
            </div>
            <h2 className="text-3xl font-semibold text-slate-800 mb-4">
              Medical Action Extraction
            </h2>
            <p className="text-slate-600 max-w-3xl mx-auto text-lg leading-relaxed">
              Extract actionable items, medication instructions, and follow-up tasks from medical visit transcripts using advanced AI technology
            </p>
          </div>

          {/* Transcript Extractor */}
          <TranscriptExtractor />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-12 text-center">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-blue-600 p-3 rounded-full mr-4">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-5xl font-bold text-slate-900">
              VetRec
            </h1>
          </div>
          <h2 className="text-3xl font-semibold text-slate-800 mb-4">
            Medical Action Extraction
          </h2>
          <p className="text-slate-600 max-w-3xl mx-auto text-lg leading-relaxed">
            Extract actionable items, medication instructions, and follow-up tasks from medical visit transcripts using advanced AI technology
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            {/* Features */}
            <Card className="border-l-4 border-l-blue-500">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  Intelligent Extraction
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  Automatically identify and categorize medical actions, medications, follow-up tasks, and clinician responsibilities from visit transcripts.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-green-500">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="w-5 h-5 text-green-600" />
                  Secure & Private
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  Your medical data is protected with enterprise-grade security. All processing is done securely with full privacy compliance.
                </CardDescription>
              </CardContent>
            </Card>
          </div>

          {/* Authentication Section */}
          <Card className="max-w-md mx-auto">
            <CardHeader className="text-center">
              <div className="bg-blue-100 p-3 rounded-full w-fit mx-auto mb-4">
                <Lock className="w-6 h-6 text-blue-600" />
              </div>
              <CardTitle className="text-2xl">Sign In Required</CardTitle>
              <CardDescription className="text-base">
                Please sign in to access the medical action extraction tool
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button 
                onClick={() => router.push('/sign-in')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                size="lg"
              >
                <User className="w-5 h-5 mr-2" />
                Sign In to Continue
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
              
              <div className="text-center">
                <p className="text-sm text-slate-500">
                  Don&apos;t have an account?{' '}
                  <button 
                    onClick={() => router.push('/sign-in')}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Create one here
                  </button>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Additional Info */}
          <div className="mt-12 text-center">
            <h3 className="text-xl font-semibold text-slate-800 mb-4">
              What you can do with VetRec
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div className="text-center p-4">
                <div className="bg-blue-100 p-3 rounded-full w-fit mx-auto mb-3">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <h4 className="font-semibold text-slate-800 mb-2">Upload Transcripts</h4>
                <p className="text-slate-600 text-sm">
                  Upload PDF files or paste medical visit transcripts directly
                </p>
              </div>
              
              <div className="text-center p-4">
                <div className="bg-green-100 p-3 rounded-full w-fit mx-auto mb-3">
                  <User className="w-6 h-6 text-green-600" />
                </div>
                <h4 className="font-semibold text-slate-800 mb-2">AI Processing</h4>
                <p className="text-slate-600 text-sm">
                  Advanced AI extracts medications, tasks, and follow-ups
                </p>
              </div>
              
              <div className="text-center p-4">
                <div className="bg-purple-100 p-3 rounded-full w-fit mx-auto mb-3">
                  <ArrowRight className="w-6 h-6 text-purple-600" />
                </div>
                <h4 className="font-semibold text-slate-800 mb-2">Export Results</h4>
                <p className="text-slate-600 text-sm">
                  Download structured results in JSON format for integration
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
