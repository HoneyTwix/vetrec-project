# Enhanced Confidence System Implementation

## Overview
This document describes the implementation of an enhanced confidence system that provides granular feedback on the confidence of extracted medical data. The system flags specific items or sections that require human review based on the LLM's assessment of extraction accuracy.

## Key Features
- **Granular Confidence Scoring**: Individual confidence levels for each extracted item
- **Flagged Sections**: Visual indicators for items requiring review
- **User Review Interface**: Ability to edit and clear flagged sections
- **No Auto-Save for High Confidence**: All extractions require user review regardless of confidence level

## Architecture Changes

### Enhanced Evaluation Functions
Both `EvaluateWithSingleStandard` and `EvaluateWithMultipleStandards` in `backend/baml_src/medical_evaluation.baml` have been modified to:

1. **Return Enhanced Results**: Changed return type from `SingleStandardResult`/`MultiStandardResult` to `EnhancedEvaluationResult`
2. **Include Granular Confidence**: Each item in the extraction receives its own confidence assessment
3. **Flagged Sections**: Identify specific items that need review
4. **Detailed Reasoning**: Provide reasoning, issues, and suggestions for each item

### New BAML Types
```baml
class ItemConfidence {
  confidence: "high" | "medium" | "low"
  reasoning: string
  issues?: string[]
  suggestions?: string[]
}

class MedicalExtractionWithConfidence {
  follow_up_tasks: FollowUpTaskWithConfidence[]
  medication_instructions: MedicationInstructionWithConfidence[]
  client_reminders: ClientReminderWithConfidence[]
  clinician_todos: ClinicianTodoWithConfidence[]
  custom_extractions: CustomExtractionWithConfidence[]
}

class FlaggedSections {
  follow_up_tasks: number[]
  medication_instructions: number[]
  client_reminders: number[]
  clinician_todos: number[]
  custom_extractions?: number[]
}

class ConfidenceDetails {
  overall_confidence: "high" | "medium" | "low"
  flagged_sections: FlaggedSections
  confidence_summary: string
  item_confidence?: {
    follow_up_tasks?: Array<{...with confidence}>
    medication_instructions?: Array<{...with confidence}>
    client_reminders?: Array<{...with confidence}>
    clinician_todos?: Array<{...with confidence}>
  }
}

class EnhancedEvaluationResult {
  evaluation: EvaluationResult
  confidence_details: ConfidenceDetails
}
```

## API Integration Updates

### Backend Changes (`backend/api/extract.py`)
1. **Modified Evaluation Logic**: Both single and multiple standard evaluation paths now use the enhanced functions
2. **Confidence Details Processing**: Convert BAML confidence details to dictionary format for API response
3. **No Auto-Save for High Confidence**: Modified `should_save` logic to always require user review
4. **Database Storage**: Store confidence details in the `confidence_details` JSON column

### Database Schema Updates
- **New Column**: Added `confidence_details JSON` to `extraction_results` table
- **Migration Script**: `backend/utils/migrate_database.py` handles the schema update

### Frontend Changes (`frontend/src/components/TranscriptExtractor.tsx`)
1. **Confidence Indicators**: Visual components showing confidence levels for each item
2. **Flagged Item Wrapper**: Red border and warning icon for items requiring review
3. **TypeScript Fixes**: Resolved type mismatches in map functions using React Fragments
4. **Enhanced UI**: Better visual hierarchy for confidence information

### TypeScript Interface Updates (`frontend/src/lib/api.ts`)
- **Confidence Types**: Added `ItemConfidence`, `FlaggedSections`, `ConfidenceDetails` interfaces
- **Response Updates**: Updated `ExtractionResponse` to include confidence details
- **Type Safety**: Proper typing for all confidence-related data structures

## User Experience Flow

1. **Extraction**: User submits transcript for extraction
2. **Evaluation**: System evaluates extraction against gold standards
3. **Confidence Assessment**: Each item receives individual confidence scoring
4. **Flagging**: Items with low/medium confidence are flagged for review
5. **Review Interface**: User sees flagged items with confidence indicators
6. **Manual Review**: User can edit, clear, or approve flagged sections
7. **Manual Save**: User must explicitly save the extraction (no auto-save)

## Testing

### Backend Testing
- **Test Script**: `backend/test_enhanced_confidence.py` tests the enhanced evaluation functions
- **Function**: Tests `EvaluateWithSingleStandard` with granular confidence assessment
- **Validation**: Verifies confidence details structure and flagged sections

### Frontend Testing
- **TypeScript Compilation**: All TypeScript errors resolved
- **Component Rendering**: Confidence indicators and flagged items display correctly
- **User Interaction**: Edit and review functionality works as expected

## Configuration

### Confidence Thresholds
The system uses a hybrid approach for confidence determination:
- **LLM Assessment**: Primary confidence evaluation from the LLM
- **Numeric Validation**: Override for edge cases based on similarity scores
- **Tiered Logic**: Multiple confidence tiers for different scenarios

### Evaluation Strategies
- **Single Standard**: Used when high similarity (≥0.8) to gold standard
- **Multiple Standards**: Used for lower similarity cases with weighted aggregation
- **No Evaluation**: Fallback when no similar transcripts found

## Future Enhancements

1. **Confidence Calibration**: Fine-tune confidence thresholds based on user feedback
2. **Batch Processing**: Handle multiple extractions with confidence assessment
3. **Confidence History**: Track confidence trends over time
4. **User Preferences**: Allow users to set confidence thresholds
5. **Advanced Flagging**: More sophisticated flagging rules and conditions

## Troubleshooting

### Common Issues
1. **TypeScript Errors**: Ensure all map functions return consistent types using React Fragments
2. **Confidence Details Missing**: Check that BAML functions return proper confidence structure
3. **Database Migration**: Run `python utils/migrate_database.py` to add confidence_details column
4. **Frontend Rendering**: Verify confidence_details structure matches TypeScript interfaces

### Debug Steps
1. Check backend logs for confidence evaluation results
2. Verify API response includes confidence_details
3. Inspect frontend console for TypeScript errors
4. Test with known high/low confidence cases 