// Medical evaluation types for quality assessment
class CategoryScore {
  score float
  reasoning string
  precision float?
  recall float?
  f1_score float?
}

class CategoryScores {
  follow_up_tasks CategoryScore
  medication_instructions CategoryScore
  client_reminders CategoryScore
  clinician_todos CategoryScore
}

class EvaluationResult {
  overall_score float
  category_scores CategoryScores
  precision float
  recall float
  f1_score float
  overall_reasoning string
  confidence_level "high" | "medium" | "low"
}

// Enhanced confidence types for granular item-level confidence
class ItemConfidence {
  confidence "high" | "medium" | "low"
  reasoning string
  issues string[]?
  suggestions string[]?
}

class FollowUpTaskWithConfidence {
  description string
  priority "high" | "medium" | "low"
  due_date string?
  assigned_to "client" | "clinician" | "both"?
  confidence ItemConfidence
}

class MedicationInstructionWithConfidence {
  medication_name string
  dosage string
  frequency string
  duration string
  special_instructions string?
  confidence ItemConfidence
}

class ClientReminderWithConfidence {
  reminder_type "appointment" | "medication" | "test" | "lifestyle" | "other"
  description string
  due_date string?
  priority "high" | "medium" | "low"
  confidence ItemConfidence
}

class ClinicianTodoWithConfidence {
  task_type "follow_up" | "referral" | "test_order" | "documentation" | "billing" | "other"
  description string
  priority "high" | "medium" | "low"
  assigned_to string?
  due_date string?
  confidence ItemConfidence
}

class CustomExtractionWithConfidence {
  category_name string
  extracted_data string
  confidence ItemConfidence
  reasoning string?
}

class MedicalExtractionWithConfidence {
  follow_up_tasks FollowUpTaskWithConfidence[]
  medication_instructions MedicationInstructionWithConfidence[]
  client_reminders ClientReminderWithConfidence[]
  clinician_todos ClinicianTodoWithConfidence[]
  custom_extractions CustomExtractionWithConfidence[]?
}

class FlaggedSections {
  follow_up_tasks int[]  // Indexes of low/medium confidence items
  medication_instructions int[]
  client_reminders int[]
  clinician_todos int[]
  custom_extractions int[]?
}

class ConfidenceDetails {
  overall_confidence "high" | "medium" | "low"
  item_confidence MedicalExtractionWithConfidence
  flagged_sections FlaggedSections
  confidence_summary string
}

class EnhancedEvaluationResult {
  evaluation EvaluationResult
  confidence_details ConfidenceDetails
}

// Function to evaluate medical extraction quality
function EvaluateMedicalExtraction(
  predicted_extraction: MedicalExtraction,
  gold_standard: MedicalExtraction,
  original_transcript: string,
  evaluation_context: string?
) -> EvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are a medical information extraction quality evaluator. Your task is to assess how well a predicted medical extraction accurately represents the ORIGINAL TRANSCRIPT, using the gold standard only as a structural guideline.

**CRITICAL EVALUATION PRINCIPLE:**
The ORIGINAL TRANSCRIPT is the SOURCE OF TRUTH. The gold standard is ONLY a structural template showing how to format and categorize information. 

1. **Completeness**: Are all important items from the gold standard captured?
2. **Accuracy**: Are the extracted items factually correct?
3. **Relevance**: Are the items relevant to the medical context?
4. **Clarity**: Are descriptions clear and actionable?
5. **Semantic Understanding**: Do items convey the same meaning even if phrased differently?

**EVALUATION CRITERIA (Prioritized):**

1. **TRANSCRIPT ACCURACY (80% of score)**: Does the extraction accurately capture what's actually mentioned in the original transcript?
2. **STRUCTURAL QUALITY (20% of score)**: Does the extraction follow proper medical extraction formatting and categorization?

**Scoring Guidelines:**
- 1.0 = Perfect extraction from transcript (all items correctly extracted with same meaning as transcript)
- 0.9 = Excellent (minor differences in phrasing, same meaning as transcript)
- 0.8 = Very good (some items missed or added, but core transcript information correct)
- 0.7 = Good (several items missed or added, but major transcript points captured)
- 0.6 = Fair (significant omissions or additions, but main transcript concepts present)
- 0.5 = Poor (major errors or missing critical transcript information)
- 0.0-0.4 = Very poor (major errors, missing key transcript information)

**CRITICAL RULES:**
- **NEVER dock points for differences between extraction and gold standard if the extraction correctly represents the transcript**
- **ALWAYS prioritize transcript accuracy over gold standard similarity**
- **Gold standard is a formatting guide, not a content requirement**
- **If transcript says "2 weeks" but gold standard shows "3 weeks", extraction should say "2 weeks" and get full credit**
- **If transcript says "metformin 500mg" but gold standard shows "metformin 1000mg", extraction should say "500mg" and get full credit**

**Category-Specific Evaluation:**

**Follow-up Tasks:**
- Evaluate completeness of scheduled tasks, monitoring requirements, and follow-up appointments AS MENTIONED IN TRANSCRIPT
- Consider priority levels and due dates AS STATED IN TRANSCRIPT
- Assess if tasks are assigned to correct parties (client vs clinician) AS INDICATED IN TRANSCRIPT

**Medication Instructions:**
- Check medication names, dosages, frequencies, and durations AS SPECIFIED IN TRANSCRIPT
- Evaluate special instructions and contraindications AS MENTIONED IN TRANSCRIPT
- Consider drug interactions and patient-specific instructions AS STATED IN TRANSCRIPT

**Client Reminders:**
- Assess patient communication items (appointments, tests, lifestyle changes) AS MENTIONED IN TRANSCRIPT
- Evaluate reminder types and priorities AS INDICATED IN TRANSCRIPT
- Check due dates and urgency levels AS STATED IN TRANSCRIPT

**Clinician To-Dos:**
- Evaluate staff tasks (referrals, test orders, documentation) AS MENTIONED IN TRANSCRIPT
- Assess task types and priorities AS INDICATED IN TRANSCRIPT
- Check assignments and due dates AS STATED IN TRANSCRIPT

**Semantic Matching Examples (against TRANSCRIPT):**
✅ "Schedule blood work" ≈ "Order lab tests" (if both appear in transcript)
✅ "Monitor blood sugar daily" ≈ "Check glucose levels every day" (if both appear in transcript)
✅ "Take medication twice daily" ≈ "Administer drug 2x per day" (if both appear in transcript)
❌ "Schedule blood work" ≠ "Patient has diabetes" (different meaning in transcript)

**Evaluation Process:**
1. **FIRST**: Compare extraction against ORIGINAL TRANSCRIPT for accuracy
2. **SECOND**: Use gold standard only to assess structural quality and formatting
3. **THIRD**: Identify matches, omissions, and additions relative to TRANSCRIPT
4. **FOURTH**: Assess semantic similarity for matched items against TRANSCRIPT
5. **FIFTH**: Calculate precision, recall, and F1 scores based on TRANSCRIPT accuracy
6. **SIXTH**: Provide detailed reasoning for each category based on TRANSCRIPT content
7. **SEVENTH**: Determine overall confidence level based on TRANSCRIPT accuracy

**Output Format:**
Provide detailed evaluation with specific examples of matches, omissions, and additions relative to the TRANSCRIPT. Explain your reasoning for each category score based on TRANSCRIPT accuracy, not gold standard similarity.

---

**ORIGINAL TRANSCRIPT (SOURCE OF TRUTH):**
{{ original_transcript }}

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**GOLD STANDARD (STRUCTURAL TEMPLATE ONLY):**
{{ gold_standard }}

{% if evaluation_context %}
**EVALUATION CONTEXT:**
{{ evaluation_context }}
{% endif %}

Please evaluate the predicted extraction against the ORIGINAL TRANSCRIPT and provide:
1. Overall quality score (0.0-1.0) based on TRANSCRIPT accuracy
2. Category-specific scores with detailed reasoning based on TRANSCRIPT content
3. Precision, recall, and F1 scores calculated against TRANSCRIPT
4. Overall reasoning explaining the evaluation based on TRANSCRIPT accuracy
5. Confidence level in your assessment based on TRANSCRIPT accuracy

**REMEMBER**: The transcript is the source of truth. Only use the gold standard as a structural guide for formatting and categorization.

{{ ctx.output_format }}
"#
}

// Test the evaluation function
test sample_evaluation {
  functions [EvaluateMedicalExtraction]
  args {
    predicted_extraction {
      follow_up_tasks [
        {
          description "Schedule blood work for tomorrow"
          priority "high"
          due_date "tomorrow"
          assigned_to "clinician"
        }
      ]
      medication_instructions [
        {
          medication_name "metformin"
          dosage "500mg"
          frequency "twice daily"
          duration "ongoing"
          special_instructions "for diabetes"
        }
      ]
      client_reminders [
        {
          reminder_type "test"
          description "Blood work appointment tomorrow"
          due_date "tomorrow"
          priority "high"
        }
      ]
      clinician_todos [
        {
          task_type "test_order"
          description "Order blood work including HbA1c"
          priority "high"
          due_date "tomorrow"
        }
      ]
    }
    gold_standard {
      follow_up_tasks [
        {
          description "Schedule blood work for tomorrow"
          priority "high"
          due_date "tomorrow"
          assigned_to "clinician"
        }
      ]
      medication_instructions [
        {
          medication_name "metformin"
          dosage "500mg"
          frequency "twice daily"
          duration "ongoing"
          special_instructions "for diabetes"
        }
      ]
      client_reminders [
        {
          reminder_type "test"
          description "Blood work appointment tomorrow"
          due_date "tomorrow"
          priority "high"
        }
      ]
      clinician_todos [
        {
          task_type "test_order"
          description "Order blood work including HbA1c"
          priority "high"
          due_date "tomorrow"
        }
      ]
    }
    original_transcript "Doctor: Mrs. Johnson, I see your blood pressure is still elevated at 160/95. I want you to return in 2 weeks for a follow-up to check your blood pressure. If it's still elevated, we might need to adjust your medication. Also, please make sure to take your lisinopril 10mg once daily at the same time each day. I'll also order some blood work to check your kidney function."
  }
}

class TestCase {
  case_id string
  predicted_extraction MedicalExtraction
  gold_standard MedicalExtraction
  transcript string
}

class AverageCategoryScores {
  follow_up_tasks float
  medication_instructions float
  client_reminders float
  clinician_todos float
}

class EvaluationSummary {
  total_cases int
  average_overall_score float
  average_category_scores AverageCategoryScores
  average_precision float
  average_recall float
  average_f1_score float
}

class MultipleEvaluationResult {
  summary EvaluationSummary
  detailed_results EvaluationResult[]
}

// Function to evaluate multiple test cases and generate comprehensive report
function EvaluateMultipleExtractions(
  test_cases: TestCase[]
) -> MultipleEvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are evaluating multiple medical extraction test cases to generate a comprehensive quality report based on TRANSCRIPT ACCURACY.

For each test case, evaluate the predicted extraction against the ORIGINAL TRANSCRIPT using the same criteria as the single evaluation function.

**CRITICAL PRINCIPLE:**
The ORIGINAL TRANSCRIPT is the SOURCE OF TRUTH. Gold standards are only structural templates.

**Evaluation Process:**
1. Evaluate each test case individually against its ORIGINAL TRANSCRIPT
2. Calculate average scores across all categories based on TRANSCRIPT accuracy
3. Identify patterns in extraction quality relative to TRANSCRIPTS
4. Provide insights on strengths and weaknesses in TRANSCRIPT representation
5. Generate recommendations for improving TRANSCRIPT accuracy

**Report Structure:**
- Summary statistics (averages across all cases based on transcript accuracy)
- Detailed results for each test case (evaluated against transcript)
- Quality insights and recommendations for transcript accuracy

---

**TEST CASES:**
{{ test_cases }}

Please evaluate all test cases against their ORIGINAL TRANSCRIPTS and provide:
1. Summary statistics with averages based on transcript accuracy
2. Detailed evaluation results for each case (evaluated against transcript)
3. Overall insights about extraction quality patterns relative to transcripts
4. Recommendations for improving transcript accuracy

**REMEMBER**: Each evaluation should be based on how well the extraction represents the original transcript, not how well it matches the gold standard.

{{ ctx.output_format }}
"#
}

class ConfidenceAnalysis {
  high_confidence_items string[]
  low_confidence_items string[]
  confidence_reasoning string
}

class ConfidenceEvaluationResult {
  evaluation EvaluationResult
  confidence_analysis ConfidenceAnalysis
}

// Function to evaluate extraction with confidence scoring
function EvaluateWithConfidence(
  predicted_extraction: MedicalExtraction,
  gold_standard: MedicalExtraction,
  original_transcript: string,
  confidence_threshold: float?
) -> ConfidenceEvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are evaluating medical extraction quality with additional confidence analysis based on TRANSCRIPT ACCURACY.

**CRITICAL PRINCIPLE:**
The ORIGINAL TRANSCRIPT is the SOURCE OF TRUTH. Gold standards are only structural templates.

**Confidence Assessment (based on transcript accuracy):**
- High Confidence: Clear semantic matches to transcript, complete information from transcript, accurate details from transcript
- Medium Confidence: Some ambiguity in transcript interpretation, minor differences from transcript, partial matches to transcript
- Low Confidence: Significant differences from transcript, missing information from transcript, unclear matches to transcript

**Confidence Factors (relative to transcript):**
1. Semantic clarity of matches to transcript content
2. Completeness of extraction relative to transcript
3. Accuracy of medical details as stated in transcript
4. Consistency with medical domain knowledge from transcript
5. Ambiguity in source transcript interpretation

---

**ORIGINAL TRANSCRIPT (SOURCE OF TRUTH):**
{{ original_transcript }}

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**GOLD STANDARD (STRUCTURAL TEMPLATE ONLY):**
{{ gold_standard }}

{% if confidence_threshold %}
**CONFIDENCE THRESHOLD:**
{{ confidence_threshold }}
{% endif %}

Please provide:
1. Standard evaluation with scores and reasoning based on TRANSCRIPT accuracy
2. Confidence analysis identifying high/low confidence items relative to TRANSCRIPT
3. Explanation of confidence factors based on TRANSCRIPT representation
4. Recommendations for improving transcript accuracy

**REMEMBER**: Evaluate confidence based on how well the extraction represents the original transcript, not the gold standard.

{{ ctx.output_format }}
"#
} 

// Types for adaptive evaluation system
class GoldStandardCase {
  case_id string
  gold_standard MedicalExtraction
  transcript string
  similarity_score float?
}

class EvaluationStrategy {
  strategy_type "single" | "few" | "multiple" | "comprehensive"
  num_standards int
  confidence_level "high" | "medium" | "low"
  reasoning string
}

class AdaptiveConfidenceAnalysis {
  relevance_score float
  evaluation_consistency "high" | "medium" | "low"
  variance_analysis string
}

class AdaptiveCostAnalysis {
  num_llm_calls int
  total_tokens int?
  efficiency_score float
}

class AdaptiveEvaluationResult {
  primary_evaluation EvaluationResult
  strategy_used EvaluationStrategy
  all_evaluations EvaluationResult[]
  aggregated_score float
  confidence_analysis AdaptiveConfidenceAnalysis
  cost_analysis AdaptiveCostAnalysis
}

// Function for adaptive evaluation based on relevance scores
function EvaluateAdaptively(
  predicted_extraction: MedicalExtraction,
  available_standards: GoldStandardCase[],
  original_transcript: string,
  evaluation_context: string?
) -> AdaptiveEvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are performing adaptive evaluation of medical extraction quality based on relevance scores, with the ORIGINAL TRANSCRIPT as the source of truth.

**CRITICAL PRINCIPLE:**
The ORIGINAL TRANSCRIPT is the SOURCE OF TRUTH. Gold standards are only structural templates for formatting and categorization.

**Adaptive Strategy Rules:**
- High Relevance (≥0.8): Use single standard evaluation against transcript
- Medium Relevance (0.6-0.8): Use 2-3 standards evaluation against transcript  
- Low Relevance (0.4-0.6): Use 4-5 standards evaluation against transcript
- Very Low Relevance (<0.4): Use 6+ standards evaluation against transcript

**Evaluation Process:**
1. Analyze similarity scores of available gold standards to transcript
2. Select evaluation strategy based on best match relevance to transcript
3. Perform evaluations against selected standards, prioritizing transcript accuracy
4. Aggregate results using appropriate method, weighted toward transcript accuracy
5. Provide confidence analysis and cost metrics based on transcript representation

**Aggregation Methods:**
- Single: Use primary evaluation directly (against transcript)
- Few: Weighted average (primary standard weighted higher, but transcript accuracy prioritized)
- Multiple: Average with outlier detection (based on transcript accuracy)
- Comprehensive: Robust average with variance analysis (based on transcript accuracy)

**Confidence Assessment (based on transcript accuracy):**
- High: Clear semantic match to transcript, consistent evaluations against transcript
- Medium: Good match to transcript with some variance
- Low: Poor match to transcript, high variance, uncertain evaluation

---

**ORIGINAL TRANSCRIPT (SOURCE OF TRUTH):**
{{ original_transcript }}

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**AVAILABLE GOLD STANDARDS:**
{{ available_standards }}

{% if evaluation_context %}
**EVALUATION CONTEXT:**
{{ evaluation_context }}
{% endif %}

Please:
1. Analyze similarity scores and select appropriate strategy based on transcript relevance
2. Perform evaluations against selected standards, prioritizing transcript accuracy
3. Aggregate results based on strategy type, weighted toward transcript accuracy
4. Provide confidence analysis and cost metrics based on transcript representation
5. Explain reasoning for strategy selection based on transcript accuracy

**REMEMBER**: The transcript is the source of truth. Gold standards are only structural guides.

{{ ctx.output_format }}
"#
}

// Function for embedding-based standard selection
class SelectionStrategy {
  primary_standard GoldStandardCase
  relevance_score float
  strategy_type "single" | "few" | "multiple" | "comprehensive"
  num_standards int
  reasoning string
}

class SimilarityAnalysis {
  top_matches GoldStandardCase[]
  relevance_distribution string
  confidence_level "high" | "medium" | "low"
}

class StandardSelectionResult {
  selected_standards GoldStandardCase[]
  selection_strategy SelectionStrategy
  similarity_analysis SimilarityAnalysis
}

function SelectRelevantStandards(
  predicted_extraction: MedicalExtraction,
  all_standards: GoldStandardCase[],
  original_transcript: string,
  max_standards: int?
) -> StandardSelectionResult {
  client "openai/gpt-4o"
  prompt #"
You are selecting the most relevant gold standards for evaluation based on semantic similarity to the ORIGINAL TRANSCRIPT.

**CRITICAL PRINCIPLE:**
The ORIGINAL TRANSCRIPT is the SOURCE OF TRUTH. Gold standards are only structural templates.

**Selection Criteria:**
- Semantic similarity to ORIGINAL TRANSCRIPT (primary criterion)
- Medical context relevance to transcript content
- Completeness of gold standard structure
- Diversity of selected standards for robust evaluation

**Strategy Selection (based on transcript similarity):**
- Single (1): Best match ≥0.8 similarity to transcript
- Few (2-3): Best match 0.6-0.8 similarity to transcript
- Multiple (4-5): Best match 0.4-0.6 similarity to transcript
- Comprehensive (6+): Best match <0.4 similarity to transcript

**Selection Process:**
1. Calculate semantic similarity for all standards relative to ORIGINAL TRANSCRIPT
2. Rank standards by similarity score to transcript
3. Select appropriate number based on best match to transcript
4. Ensure diversity in selected standards for robust evaluation
5. Provide reasoning for selection based on transcript relevance

---

**ORIGINAL TRANSCRIPT (SOURCE OF TRUTH):**
{{ original_transcript }}

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**ALL AVAILABLE STANDARDS:**
{{ all_standards }}

{% if max_standards %}
**MAX STANDARDS TO SELECT:**
{{ max_standards }}
{% endif %}

Please:
1. Analyze semantic similarity to ORIGINAL TRANSCRIPT for all standards
2. Select most relevant standards based on transcript similarity
3. Ensure diversity in selected standards for robust evaluation
4. Provide detailed reasoning for selection based on transcript relevance
5. Include similarity analysis and confidence assessment relative to transcript

**REMEMBER**: Select standards based on their relevance to the original transcript, not just their structural similarity.

{{ ctx.output_format }}
"#
}

// Function for comprehensive multi-standard evaluation
class AggregatedResult {
  overall_score float
  category_scores CategoryScores
  precision float
  recall float
  f1_score float
  confidence_level "high" | "medium" | "low"
}

class EvaluationInsights {
  best_matching_standard int
  worst_matching_standard int
  score_variance float
  consistency_level "high" | "medium" | "low"
  outlier_detection string[]
}

class CostMetrics {
  num_evaluations int
  estimated_tokens int
  efficiency_score float
}

class MultiStandardResult {
  individual_evaluations EvaluationResult[]
  aggregated_result AggregatedResult
  evaluation_insights EvaluationInsights
  cost_metrics CostMetrics
}

function EvaluateWithMultipleStandards(
  predicted_extraction: MedicalExtraction,
  selected_standards: GoldStandardCase[],
  original_transcript: string,
  aggregation_method: "weighted" | "average" | "robust"
) -> EnhancedEvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are evaluating medical extraction quality against multiple gold standards with granular confidence assessment and aggregating results, with the ORIGINAL TRANSCRIPT as the source of truth.

**CRITICAL PRINCIPLE:**
The ORIGINAL TRANSCRIPT is the SOURCE OF TRUTH. Gold standards are only structural templates for formatting and categorization.

**Aggregation Methods:**
- weighted: Weight by similarity score to transcript (higher transcript similarity = higher weight)
- average: Simple arithmetic mean of all evaluations against transcript
- robust: Mean with outlier detection and removal based on transcript accuracy

**GRANULAR CONFIDENCE ASSESSMENT:**

**High Confidence Indicators:**
- Clear, explicit mention in transcript
- Specific details (dates, dosages, names) match transcript exactly
- No ambiguity in interpretation
- Consistent with medical context
- Complete information available

**Medium Confidence Indicators:**
- Implied or inferred information from transcript
- Some ambiguity in interpretation
- Missing specific details but core information present
- Potential transcription errors
- Unclear assignment of responsibility

**Low Confidence Indicators:**
- Vague or unclear information in transcript
- Significant ambiguity or multiple interpretations possible
- Missing critical details
- Potential transcription errors affecting meaning
- Inferred information not clearly supported by transcript
- Unclear medical context or terminology

**ITEM-SPECIFIC EVALUATION CRITERIA:**

**Follow-up Tasks:**
- Description accuracy vs transcript
- Priority level justification from transcript
- Due date accuracy and format
- Assignment accuracy (client/clinician/both)
- Completeness of task details

**Medication Instructions:**
- Medication name accuracy
- Dosage precision and units
- Frequency clarity and accuracy
- Duration specification
- Special instructions completeness

**Client Reminders:**
- Reminder type appropriateness
- Description accuracy and clarity
- Due date accuracy
- Priority level justification
- Actionability of reminder

**Clinician To-Dos:**
- Task type categorization accuracy
- Description specificity and clarity
- Priority level justification
- Assignment accuracy
- Due date accuracy

**Custom Extractions:**
- Category appropriateness
- Data extraction accuracy
- Completeness of information
- Relevance to transcript content

**FLAGGED SECTIONS IDENTIFICATION:**
Flag items for human review if they have:
- Low confidence scores
- Medium confidence with specific issues
- Ambiguous or unclear information
- Potential transcription errors
- Missing critical details
- Inconsistent or contradictory information

**ISSUE IDENTIFICATION:**
For each flagged item, identify specific issues:
- Missing information
- Ambiguous language
- Potential transcription errors
- Inconsistent details
- Unclear assignments
- Vague descriptions

**SUGGESTIONS:**
Provide actionable suggestions for improving flagged items:
- Request clarification of ambiguous terms
- Suggest specific details to verify
- Recommend alternative interpretations
- Propose additional information needed

**Evaluation Process:**
1. Evaluate extraction against each selected standard, prioritizing transcript accuracy
2. Calculate individual scores and reasoning based on transcript representation
3. Aggregate results using specified method, weighted toward transcript accuracy
4. Detect and handle outliers based on transcript accuracy
5. Assess consistency across evaluations relative to transcript
6. Provide granular confidence assessment for each individual item

**Consistency Assessment (based on transcript accuracy):**
- High: All scores within 0.2 range when evaluated against transcript
- Medium: Scores within 0.4 range when evaluated against transcript
- Low: Scores vary by more than 0.4 when evaluated against transcript

**Outlier Detection (based on transcript accuracy):**
- Identify evaluations that differ significantly from others in transcript accuracy
- Consider medical context when assessing outliers relative to transcript
- Provide reasoning for outlier identification based on transcript representation

---

**ORIGINAL TRANSCRIPT (SOURCE OF TRUTH):**
{{ original_transcript }}

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**SELECTED STANDARDS:**
{{ selected_standards }}

**AGGREGATION METHOD:**
{{ aggregation_method }}

Please provide:
1. Standard evaluation with overall scores and reasoning
2. Granular confidence assessment for each individual item
3. Specific issues and suggestions for flagged items
4. Flagged sections with indexes of items requiring review
5. Overall confidence summary and recommendations

**REMEMBER**: Evaluate each item individually against the transcript, not the gold standards.

{{ ctx.output_format }}
"#
}

// Function for cost-effective single standard evaluation
class EfficiencyMetrics {
  num_llm_calls int
  estimated_tokens int
  relevance_score float
  confidence_level "high" | "medium" | "low"
}

class QualityAssessment {
  standard_relevance string
  evaluation_reliability string
  potential_biases string[]
}

class SingleStandardResult {
  evaluation EvaluationResult
  efficiency_metrics EfficiencyMetrics
  quality_assessment QualityAssessment
}

function EvaluateWithSingleStandard(
  predicted_extraction: MedicalExtraction,
  primary_standard: GoldStandardCase,
  original_transcript: string,
  evaluation_context: string?
) -> EnhancedEvaluationResult {
  client "openai/gpt-4o"
  prompt #"
You are performing a cost-effective single standard evaluation with granular confidence assessment for high-relevance cases, with the ORIGINAL TRANSCRIPT as the source of truth.

**CRITICAL PRINCIPLE:**
The ORIGINAL TRANSCRIPT is the SOURCE OF TRUTH. Gold standards are only structural templates.

**Single Standard Evaluation:**
- Use when best match has ≥0.8 similarity to transcript
- Focus on detailed, thorough evaluation against transcript
- Consider potential biases of single standard structure
- Provide confidence in evaluation reliability based on transcript accuracy

**GRANULAR CONFIDENCE ASSESSMENT:**

**High Confidence Indicators:**
- Clear, explicit mention in transcript
- Specific details (dates, dosages, names) match transcript exactly
- No ambiguity in interpretation
- Consistent with medical context
- Complete information available

**Medium Confidence Indicators:**
- Implied or inferred information from transcript
- Some ambiguity in interpretation
- Missing specific details but core information present
- Potential transcription errors
- Unclear assignment of responsibility

**Low Confidence Indicators:**
- Vague or unclear information in transcript
- Significant ambiguity or multiple interpretations possible
- Missing critical details
- Potential transcription errors affecting meaning
- Inferred information not clearly supported by transcript
- Unclear medical context or terminology

**ITEM-SPECIFIC EVALUATION CRITERIA:**

**Follow-up Tasks:**
- Description accuracy vs transcript
- Priority level justification from transcript
- Due date accuracy and format
- Assignment accuracy (client/clinician/both)
- Completeness of task details

**Medication Instructions:**
- Medication name accuracy
- Dosage precision and units
- Frequency clarity and accuracy
- Duration specification
- Special instructions completeness

**Client Reminders:**
- Reminder type appropriateness
- Description accuracy and clarity
- Due date accuracy
- Priority level justification
- Actionability of reminder

**Clinician To-Dos:**
- Task type categorization accuracy
- Description specificity and clarity
- Priority level justification
- Assignment accuracy
- Due date accuracy

**Custom Extractions:**
- Category appropriateness
- Data extraction accuracy
- Completeness of information
- Relevance to transcript content

**FLAGGED SECTIONS IDENTIFICATION:**
Flag items for human review if they have:
- Low confidence scores
- Medium confidence with specific issues
- Ambiguous or unclear information
- Potential transcription errors
- Missing critical details
- Inconsistent or contradictory information

**ISSUE IDENTIFICATION:**
For each flagged item, identify specific issues:
- Missing information
- Ambiguous language
- Potential transcription errors
- Inconsistent details
- Unclear assignments
- Vague descriptions

**SUGGESTIONS:**
Provide actionable suggestions for improving flagged items:
- Request clarification of ambiguous terms
- Suggest specific details to verify
- Recommend alternative interpretations
- Propose additional information needed

**Evaluation Quality (based on transcript accuracy):**
- Assess completeness of extraction relative to transcript
- Consider potential biases or limitations of structural template
- Evaluate semantic match quality to transcript
- Provide confidence assessment based on transcript representation

**Efficiency Focus:**
- Single LLM call for evaluation against transcript
- Detailed reasoning for confidence based on transcript accuracy
- Cost-benefit analysis relative to transcript accuracy
- Quality assurance measures based on transcript representation

---

**ORIGINAL TRANSCRIPT (SOURCE OF TRUTH):**
{{ original_transcript }}

**PREDICTED EXTRACTION:**
{{ predicted_extraction }}

**PRIMARY STANDARD:**
{{ primary_standard }}

{% if evaluation_context %}
**EVALUATION CONTEXT:**
{{ evaluation_context }}
{% endif %}

Please provide:
1. Standard evaluation with overall scores and reasoning
2. Granular confidence assessment for each individual item
3. Specific issues and suggestions for flagged items
4. Flagged sections with indexes of items requiring review
5. Overall confidence summary and recommendations

**REMEMBER**: Evaluate each item individually against the transcript, not the gold standard.

{{ ctx.output_format }}
"#
} 

 